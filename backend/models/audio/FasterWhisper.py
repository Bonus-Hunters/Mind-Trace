from faster_whisper import WhisperModel
from typing import Optional, List, Dict, Any
import os


class FasterWhisperTranscriber:
    """
    A wrapper class for faster-whisper transcription.

    Attributes:
        model_size: Size of the Whisper model (tiny, base, small, medium, large-v2, large-v3)
        device: Device to run inference on (cuda, cpu, auto)
        compute_type: Computation type (float16, int8, int8_float16, float32)
    """

    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

    def __init__(
        self,
        model_size: str = "large-v2",
        device: str = "auto",
        compute_type: str = "float16",
    ):
        """
        Initialize the FasterWhisper transcriber.

        Args:
            model_size: Size of the model to use
            device: Device for inference ('cuda', 'cpu', or 'auto')
            compute_type: Precision type for computation
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None

    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        if self.model is None:
            self.model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5,
        word_timestamps: bool = True,
        vad_filter: bool = True,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'ar'). None for auto-detection
            task: 'transcribe' or 'translate'
            beam_size: Beam size for decoding
            word_timestamps: Whether to include word-level timestamps
            vad_filter: Whether to use VAD to filter out silence

        Returns:
            Dictionary containing transcription results with:
                - text: Full transcription text
                - segments: List of segment dictionaries
                - language: Detected language
                - language_probability: Confidence in language detection
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model if not already loaded
        self.load_model()

        # Perform transcription
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=beam_size,
            word_timestamps=word_timestamps,
            vad_filter=vad_filter,
        )

        # Process segments
        segment_list = []
        full_text_parts = []

        for segment in segments:
            segment_dict = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }

            if word_timestamps and hasattr(segment, "words") and segment.words:
                segment_dict["words"] = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability,
                    }
                    for word in segment.words
                ]

            segment_list.append(segment_dict)
            full_text_parts.append(segment.text.strip())

        return {
            "text": " ".join(full_text_parts),
            "segments": segment_list,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
        }

    def get_formatted_transcript(
        self, result: Dict[str, Any], include_timestamps: bool = True
    ) -> str:
        """
        Format the transcription result as a readable string.

        Args:
            result: Transcription result dictionary
            include_timestamps: Whether to include timestamps in output

        Returns:
            Formatted transcript string
        """
        if not include_timestamps:
            return result["text"]

        lines = []
        for segment in result["segments"]:
            start_time = self._format_timestamp(segment["start"])
            end_time = self._format_timestamp(segment["end"])
            lines.append(f"[{start_time} --> {end_time}] {segment['text']}")

        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to HH:MM:SS.mmm format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
