"""
Meeting Pipeline - Full Speech-to-Dialogue Transcription
Combines VAD, Speaker Diarization, and Whisper Transcription
to produce speaker-labeled dialogue from meeting audio.
"""

import os
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

from models.audio.SileroVad import SileroVAD
from models.audio.SpeakerDiarization import SpeakerDiarizer
from models.audio.FasterWhisper import FasterWhisperTranscriber
from models.audio.TextSummarizer import TextSummarizer


class MeetingPipeline:
    """
    Full meeting transcription pipeline with speaker diarization.

    Combines:
    1. Voice Activity Detection (Silero VAD)
    2. Speaker Diarization (pyannote-audio)
    3. Speech Transcription (Whisper)

    To produce a speaker-labeled dialogue output.
    """

    def __init__(
        self,
        whisper_model_size: str = "large-v2",
        device: str = "cpu",
        compute_type: str = "int8",
        hf_token: Optional[str] = None,
        use_vad: bool = True,
        enable_summarization: bool = False,
        summarization_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the meeting pipeline.

        Args:
            whisper_model_size: Whisper model size
            device: Device for inference ('cuda', 'cpu', 'auto')
            compute_type: Whisper compute type
            hf_token: HuggingFace token for pyannote (defaults to HF_TOKEN env var)
            use_vad: Whether to use VAD filtering
            enable_summarization: Whether to enable text summarization and chunking
            summarization_config: Configuration dict for TextSummarizer (optional)
        """
        self.whisper_model_size = whisper_model_size
        self.device = device
        self.compute_type = compute_type
        self.hf_token = hf_token
        self.use_vad = use_vad
        self.enable_summarization = enable_summarization
        self.summarization_config = summarization_config or {}

        # Initialize components (lazy loading)
        self.vad: Optional[SileroVAD] = None
        self.diarizer: Optional[SpeakerDiarizer] = None
        self.transcriber: Optional[FasterWhisperTranscriber] = None
        self.summarizer: Optional[TextSummarizer] = None

        self._models_loaded = False

    def load_models(self) -> None:
        """Load all models into memory."""
        if self._models_loaded:
            return

        # Initialize VAD
        if self.use_vad:
            self.vad = SileroVAD()
            self.vad.load_model()

        # Initialize diarizer
        self.diarizer = SpeakerDiarizer(device=self.device, hf_token=self.hf_token)
        self.diarizer.load_model()

        # Initialize transcriber
        self.transcriber = FasterWhisperTranscriber(
            model_size=self.whisper_model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        self.transcriber.load_model()

        # Initialize summarizer if enabled
        if self.enable_summarization:
            self.summarizer = TextSummarizer(
                device=self.device, **self.summarization_config
            )
            self.summarizer.load_models()

        self._models_loaded = True

    def process(
        self,
        audio_path: str,
        language: Optional[str] = None,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process a meeting audio file to produce speaker-labeled dialogue.

        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'ar'). None for auto-detection
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum expected speakers
            max_speakers: Maximum expected speakers

        Returns:
            Dictionary with:
                - dialogue: List of speaker turns with text and timestamps
                - speakers: List of speaker labels
                - num_speakers: Number of detected speakers
                - duration: Total audio duration
                - language: Detected language
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load models
        self.load_models()

        # Step 1: Speaker Diarization - identify who spoke when
        diarization_result = self.diarizer.diarize(
            audio_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )

        speaker_segments = diarization_result["segments"]

        # Step 2: Transcribe the full audio
        transcription_result = self.transcriber.transcribe(
            audio_path, language=language, word_timestamps=True, vad_filter=self.use_vad
        )

        # Step 3: Align transcription with speaker segments
        dialogue = self._align_transcription_with_speakers(
            transcription_result["segments"], speaker_segments
        )

        # Step 4: Merge consecutive segments from same speaker
        merged_dialogue = self._merge_consecutive_speaker_segments(dialogue)

        # Build result
        result = {
            "dialogue": merged_dialogue,
            "speakers": diarization_result["speakers"],
            "num_speakers": diarization_result["num_speakers"],
            "duration": transcription_result["duration"],
            "language": transcription_result["language"],
            "language_probability": transcription_result["language_probability"],
        }

        # Step 5: Generate summaries and embeddings if enabled
        if self.enable_summarization and self.summarizer:
            meeting_json = {"dialogue": merged_dialogue}
            chunks = self.summarizer.chunk_meeting_dialogue(meeting_json)
            result["chunks"] = chunks

        return result

    def _align_transcription_with_speakers(
        self, transcription_segments: List[Dict], speaker_segments: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Align transcription segments with speaker diarization.

        Uses word-level timestamps to assign each word to a speaker,
        then groups words into speaker turns.
        """
        dialogue = []

        for trans_seg in transcription_segments:
            # Get words with timestamps
            if "words" in trans_seg and trans_seg["words"]:
                words = trans_seg["words"]
            else:
                # Fall back to segment-level assignment
                speaker = self._find_speaker_for_time(
                    (trans_seg["start"] + trans_seg["end"]) / 2, speaker_segments
                )
                dialogue.append(
                    {
                        "speaker": speaker,
                        "text": trans_seg["text"],
                        "start": trans_seg["start"],
                        "end": trans_seg["end"],
                    }
                )
                continue

            # Group consecutive words by speaker
            current_speaker = None
            current_words = []
            current_start = None

            for word in words:
                word_mid = (word["start"] + word["end"]) / 2
                speaker = self._find_speaker_for_time(word_mid, speaker_segments)

                if speaker != current_speaker:
                    # Save previous group
                    if current_words and current_speaker:
                        dialogue.append(
                            {
                                "speaker": current_speaker,
                                "text": "".join(
                                    w["word"] for w in current_words
                                ).strip(),
                                "start": current_start,
                                "end": current_words[-1]["end"],
                            }
                        )

                    # Start new group
                    current_speaker = speaker
                    current_words = [word]
                    current_start = word["start"]
                else:
                    current_words.append(word)

            # Save last group
            if current_words and current_speaker:
                dialogue.append(
                    {
                        "speaker": current_speaker,
                        "text": "".join(w["word"] for w in current_words).strip(),
                        "start": current_start,
                        "end": current_words[-1]["end"],
                    }
                )

        return dialogue

    def _find_speaker_for_time(self, time: float, speaker_segments: List[Dict]) -> str:
        """Find which speaker was talking at a specific time."""
        for seg in speaker_segments:
            if seg["start"] <= time <= seg["end"]:
                return seg["speaker"]

        # If no exact match, find closest segment
        min_dist = float("inf")
        closest_speaker = "Unknown"

        for seg in speaker_segments:
            seg_mid = (seg["start"] + seg["end"]) / 2
            dist = abs(time - seg_mid)
            if dist < min_dist:
                min_dist = dist
                closest_speaker = seg["speaker"]

        return closest_speaker

    def _merge_consecutive_speaker_segments(
        self, dialogue: List[Dict[str, Any]], max_gap: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Merge consecutive dialogue entries from the same speaker.

        Args:
            dialogue: List of dialogue entries
            max_gap: Maximum gap in seconds to merge

        Returns:
            Merged dialogue list
        """
        if not dialogue:
            return []

        merged = [dialogue[0].copy()]

        for entry in dialogue[1:]:
            last = merged[-1]

            # Merge if same speaker and gap is small
            if (
                entry["speaker"] == last["speaker"]
                and entry["start"] - last["end"] <= max_gap
            ):
                last["text"] = f"{last['text']} {entry['text']}"
                last["end"] = entry["end"]
            else:
                merged.append(entry.copy())

        return merged

    def get_dialogue_text(
        self, result: Dict[str, Any], include_timestamps: bool = False
    ) -> str:
        """
        Format dialogue result as readable text.

        Args:
            result: Pipeline result dictionary
            include_timestamps: Whether to include timestamps

        Returns:
            Formatted dialogue string
        """
        lines = []
        for entry in result["dialogue"]:
            if include_timestamps:
                start = self._format_time(entry["start"])
                end = self._format_time(entry["end"])
                lines.append(f"[{start} → {end}] {entry['speaker']}: {entry['text']}")
            else:
                lines.append(f"{entry['speaker']}: {entry['text']}")

        return "\n".join(lines)

    def get_dialogue_json(self, result: Dict[str, Any]) -> str:
        """
        Format dialogue result as JSON.

        Args:
            result: Pipeline result dictionary

        Returns:
            JSON string of the dialogue
        """
        # Create simplified output format
        output = {entry["speaker"]: entry["text"] for entry in result["dialogue"]}

        # For actual dialogue list (with duplicates)
        output_full = {
            "speakers": result["speakers"],
            "num_speakers": result["num_speakers"],
            "duration": result["duration"],
            "language": result["language"],
            "dialogue": result["dialogue"],
        }

        return json.dumps(output_full, indent=2, ensure_ascii=False)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def unload_models(self) -> None:
        """Unload all models from memory."""
        if self.vad:
            self.vad.unload_model()
            self.vad = None

        if self.diarizer:
            self.diarizer.unload_model()
            self.diarizer = None

        if self.transcriber:
            self.transcriber.unload_model()
            self.transcriber = None

        if self.summarizer:
            self.summarizer.unload_models()
            self.summarizer = None

        self._models_loaded = False


# Convenience function for quick usage
def transcribe_meeting(
    audio_path: str,
    language: Optional[str] = None,
    num_speakers: Optional[int] = None,
    whisper_model: str = "large-v2",
    device: str = "auto",
    hf_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to transcribe a meeting with speaker diarization.

    Args:
        audio_path: Path to meeting audio file
        language: Language code (None for auto-detect)
        num_speakers: Number of speakers (None for auto-detect)
        whisper_model: Whisper model size
        device: Computation device
        hf_token: HuggingFace token for pyannote (defaults to HF_TOKEN env var)

    Returns:
        Dialogue result dictionary
    """
    pipeline = MeetingPipeline(
        whisper_model_size=whisper_model, device=device, hf_token=hf_token
    )

    try:
        return pipeline.process(
            audio_path, language=language, num_speakers=num_speakers
        )
    finally:
        pipeline.unload_models()
