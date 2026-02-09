"""
Speaker Diarization Model using pyannote-audio
Identifies different speakers in an audio file and returns speaker segments.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
import torch
import importlib
import torchaudio
import wave
import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SpeakerDiarizer:
    """
    Speaker diarization using pyannote-audio pipeline.
    
    Identifies who spoke when in an audio file, returning segments
    with speaker labels and timestamps.
    
    Attributes:
        device: Device to run inference on (cuda, cpu)
        hf_token: HuggingFace token for model access
    """
    
    def __init__(
        self,
        device: str = "auto",
        hf_token: Optional[str] = None,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ):
        """
        Initialize the speaker diarizer.
        
        Args:
            device: Device for inference ('cuda', 'cpu', or 'auto')
            hf_token: HuggingFace token (defaults to HF_TOKEN env var)
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
        """
        self.device = self._resolve_device(device)
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.num_speakers = num_speakers
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        self.pipeline = None
        
    def _resolve_device(self, device: str) -> str:
        """Resolve 'auto' device to actual device."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def load_model(self) -> None:
        """Load the pyannote speaker diarization pipeline."""
        if self.pipeline is None:
            import functools
            
            if not self.hf_token:
                raise ValueError(
                    "HuggingFace token is required for pyannote models. "
                    "Set the HF_TOKEN environment variable or pass hf_token parameter. "
                    "Get your token at: https://huggingface.co/settings/tokens"
                )
            
            # Register TorchVersion as a safe global (PyTorch 2.6)
            try:
                import torch
                torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
            except Exception:
                pass
            
            # Patch torch.load to force weights_only=False regardless of arguments
            original_load = torch.load
            
            @functools.wraps(original_load)
            def patched_load(*args, **kwargs):
                # Force weights_only to False
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            
            torch.load = patched_load
            
            # Also patch lightning's cloud_io if available
            try:
                from lightning.fabric.utilities import cloud_io
                cloud_io.torch.load = patched_load
            except Exception:
                pass
            
            # Ensure AudioDecoder exists (fallback when torchcodec is unavailable)
            io_mod = importlib.import_module("pyannote.audio.core.io")
            if not hasattr(io_mod, "AudioDecoder"):
                class _FallbackAudioDecoder:
                    """Fallback AudioDecoder using soundfile (supports multiple formats).

                    Provides a `metadata` attribute with `duration_seconds_from_header` and a `get_all_samples` method.
                    """
                    def __init__(self, audio_path):
                        import soundfile as sf
                        import types
                        self.audio_path = audio_path
                        # soundfile.info is lightweight and supports many formats
                        try:
                            info = sf.info(audio_path)
                            self.sample_rate = info.samplerate
                            self.waveform = None
                            self.metadata = types.SimpleNamespace(
                                duration_seconds_from_header=info.duration,
                                sample_rate=info.samplerate,
                                num_channels=info.channels
                            )
                        except Exception as e:
                            raise RuntimeError(f"Failed to load audio file {audio_path} with soundfile: {e}")

                    def get_all_samples(self):
                        """Return an object mimicking AudioSamples with `data` attribute containing the waveform tensor."""
                        import soundfile as sf
                        import torch
                        import types
                        
                        # Read audio using soundfile (returns (frames, channels))
                        # always_2d=True ensures consistency
                        audio_np, sample_rate = sf.read(self.audio_path, dtype='float32', always_2d=True)
                        
                        # Transpose to (channels, frames) as expected by pyannote/torch
                        # audio_np is (time, channels), we want (channels, time)
                        audio_np = audio_np.T
                        
                        waveform = torch.from_numpy(audio_np)
                        return types.SimpleNamespace(data=waveform, sample_rate=sample_rate)

                    def get_samples_played_in_range(self, start, end):
                        """
                        Read specific range of audio samples.
                        start: start time in seconds
                        end: end time in seconds
                        """
                        import soundfile as sf
                        import torch
                        import types
                        import math

                        # Calculate start and end frames
                        start_frame = math.floor(start * self.sample_rate)
                        end_frame = math.ceil(end * self.sample_rate)
                        duration_frames = end_frame - start_frame
                        
                        if duration_frames <= 0:
                             # Return empty tensor if invalid range
                             return types.SimpleNamespace(data=torch.empty(self.metadata.num_channels, 0), sample_rate=self.sample_rate)

                        # Read partial audio using soundfile
                        # seek to start frame
                        with sf.SoundFile(self.audio_path) as f:
                            f.seek(start_frame)
                            audio_np = f.read(frames=duration_frames, dtype='float32', always_2d=True)
                        
                        # Transpose to (channels, frames)
                        audio_np = audio_np.T
                        
                        waveform = torch.from_numpy(audio_np)
                        return types.SimpleNamespace(data=waveform, sample_rate=self.sample_rate)
                io_mod.AudioDecoder = _FallbackAudioDecoder
            
            try:
                from pyannote.audio import Pipeline
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=self.hf_token
                )
                self.pipeline.to(torch.device(self.device))
            finally:
                # Restore original torch.load
                torch.load = original_load
                try:
                    from lightning.fabric.utilities import cloud_io
                    cloud_io.torch.load = original_load
                except Exception:
                    pass
                try:
                    from lightning.fabric.utilities import cloud_io
                    cloud_io.torch.load = original_load
                except Exception:
                    pass
    
    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform speaker diarization on an audio file.
        
        Args:
            audio_path: Path to the audio file
            num_speakers: Override exact number of speakers
            min_speakers: Override minimum number of speakers
            max_speakers: Override maximum number of speakers
            
        Returns:
            Dictionary containing:
                - segments: List of dicts with speaker, start, end
                - speakers: List of unique speaker labels
                - num_speakers: Number of detected speakers
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load model if not already loaded
        self.load_model()
        
        # Build diarization parameters
        params = {}
        
        n_speakers = num_speakers or self.num_speakers
        min_spk = min_speakers or self.min_speakers
        max_spk = max_speakers or self.max_speakers
        
        if n_speakers is not None:
            params["num_speakers"] = n_speakers
        if min_spk is not None:
            params["min_speakers"] = min_spk
        if max_spk is not None:
            params["max_speakers"] = max_spk
        
        # Run diarization
        diarization = self.pipeline(audio_path, **params)
        
        # Handle DiarizeOutput object (pyannote 3.1+)
        if hasattr(diarization, "speaker_diarization"):
            diarization = diarization.speaker_diarization
        elif hasattr(diarization, "annotation"): # Possible other variation
            diarization = diarization.annotation
        
        # Process results into segments
        segments = []
        speakers_set = set()
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end
            })
            speakers_set.add(speaker)
        
        # Sort segments by start time
        segments.sort(key=lambda x: x["start"])
        
        # Create speaker mapping for cleaner labels
        speakers_list = sorted(speakers_set)
        speaker_map = {
            spk: f"Speaker {i+1}" 
            for i, spk in enumerate(speakers_list)
        }
        
        # Apply clean labels
        for segment in segments:
            segment["speaker_id"] = segment["speaker"]
            segment["speaker"] = speaker_map[segment["speaker"]]
        
        return {
            "segments": segments,
            "speakers": list(speaker_map.values()),
            "num_speakers": len(speakers_list),
            "speaker_map": speaker_map
        }
    
    def get_speaker_segments(
        self,
        audio_path: str,
        **kwargs
    ) -> List[Tuple[float, float, str]]:
        """
        Get speaker segments as simple tuples.
        
        Args:
            audio_path: Path to the audio file
            **kwargs: Additional arguments for diarize()
            
        Returns:
            List of (start_time, end_time, speaker_label) tuples
        """
        result = self.diarize(audio_path, **kwargs)
        return [
            (seg["start"], seg["end"], seg["speaker"])
            for seg in result["segments"]
        ]
    
    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda":
                torch.cuda.empty_cache()
