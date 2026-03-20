"""
Silero VAD (Voice Activity Detection) Model Wrapper
Detects speech segments in audio using Silero VAD.
"""

import torch
import torchaudio
from typing import List, Tuple, Optional, Dict, Any
import numpy as np


class SileroVAD:
    """
    Voice Activity Detection using Silero VAD model.
    
    Detects speech segments in audio files, filtering out
    silence and background noise.
    
    Attributes:
        threshold: Speech detection threshold (0-1)
        min_speech_duration_ms: Minimum speech segment duration
        min_silence_duration_ms: Minimum silence gap to split segments
        sampling_rate: Expected audio sampling rate
    """
    
    SAMPLING_RATE = 16000  # Silero VAD expects 16kHz audio
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
        speech_pad_ms: int = 30
    ):
        """
        Initialize the Silero VAD detector.
        
        Args:
            threshold: Speech probability threshold (0-1)
            min_speech_duration_ms: Minimum speech segment length in ms
            min_silence_duration_ms: Minimum silence to split segments in ms
            speech_pad_ms: Padding to add around speech segments in ms
        """
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms
        self.model = None
        self.utils = None
        
    def load_model(self) -> None:
        """Load the Silero VAD model from torch hub."""
        if self.model is None:
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                trust_repo=True
            )
    
    def _load_audio(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """
        Load and preprocess audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (audio_tensor, sample_rate)
        """
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample to 16kHz if needed
        if sample_rate != self.SAMPLING_RATE:
            resampler = torchaudio.transforms.Resample(
                orig_freq=sample_rate,
                new_freq=self.SAMPLING_RATE
            )
            waveform = resampler(waveform)
        
        return waveform.squeeze(), self.SAMPLING_RATE
    
    def detect_speech(
        self,
        audio_path: str,
        return_seconds: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Detect speech segments in an audio file.
        
        Args:
            audio_path: Path to the audio file
            return_seconds: If True, return times in seconds; else samples
            
        Returns:
            List of dicts with 'start' and 'end' times for speech segments
        """
        # Load model if needed
        self.load_model()
        
        # Load audio
        wav, sr = self._load_audio(audio_path)
        
        # Get speech timestamps using Silero's utility function
        get_speech_timestamps = self.utils[0]
        
        speech_timestamps = get_speech_timestamps(
            wav,
            self.model,
            threshold=self.threshold,
            min_speech_duration_ms=self.min_speech_duration_ms,
            min_silence_duration_ms=self.min_silence_duration_ms,
            speech_pad_ms=self.speech_pad_ms,
            sampling_rate=sr,
            return_seconds=return_seconds
        )
        
        return speech_timestamps
    
    def get_speech_segments(
        self,
        audio_path: str
    ) -> List[Tuple[float, float]]:
        """
        Get speech segments as simple tuples.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        segments = self.detect_speech(audio_path, return_seconds=True)
        return [(seg['start'], seg['end']) for seg in segments]
    
    def filter_audio(
        self,
        audio_path: str,
        output_path: str
    ) -> str:
        """
        Filter audio to keep only speech segments.
        
        Args:
            audio_path: Input audio file path
            output_path: Output audio file path
            
        Returns:
            Path to the filtered audio file
        """
        # Load model if needed
        self.load_model()
        
        # Load audio
        wav, sr = self._load_audio(audio_path)
        
        # Get speech segments in samples
        segments = self.detect_speech(audio_path, return_seconds=False)
        
        if not segments:
            # No speech detected, save empty audio
            torchaudio.save(output_path, torch.zeros(1, 1), self.SAMPLING_RATE)
            return output_path
        
        # Concatenate speech segments
        speech_parts = []
        for seg in segments:
            start_sample = seg['start']
            end_sample = seg['end']
            speech_parts.append(wav[start_sample:end_sample])
        
        # Combine all speech
        filtered_audio = torch.cat(speech_parts)
        
        # Save filtered audio
        torchaudio.save(
            output_path,
            filtered_audio.unsqueeze(0),
            self.SAMPLING_RATE
        )
        
        return output_path
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get the total duration of an audio file in seconds.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        wav, sr = self._load_audio(audio_path)
        return len(wav) / sr
    
    def get_speech_ratio(self, audio_path: str) -> float:
        """
        Get the ratio of speech to total audio duration.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Speech ratio (0-1)
        """
        total_duration = self.get_audio_duration(audio_path)
        segments = self.get_speech_segments(audio_path)
        
        speech_duration = sum(end - start for start, end in segments)
        
        return speech_duration / total_duration if total_duration > 0 else 0
    
    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self.utils = None
