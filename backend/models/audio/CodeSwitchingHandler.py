"""
Code-Switching Handler for Arabic-English Meeting Transcription

Handles audio where speakers switch between Arabic and English.

Pipeline:
  1. Fine-tuned Whisper ASR  → mixed Arabic/English transcript
  2. PEFT/LoRA Llama 3 model → fully English translation

Both models are loaded via HuggingFace transformers + peft.
No Ollama and no torchcodec/FFmpeg required.

Output format matches FasterWhisperTranscriber.transcribe() so it
plugs in transparently inside MeetingPipeline.
"""

# https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct make sure you have access to this model
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftConfig, PeftModel


DEFAULT_WHISPER_MODEL = "ahmedheakl/arazn-whisper-small-v2"
DEFAULT_TRANSLATION_MODEL = "ahmedheakl/arazn-llama3-english"
TARGET_SAMPLE_RATE = 16_000
CHUNK_SECONDS = 30

# Official prompt template from the model card
_LLAMA_PROMPT = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
    "Translate the following code-switched Arabic-English-mixed text to English only."
    "<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
    "{source}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
)


class CodeSwitchingHandler:
    """
    Transcribes Arabic/English code-switching audio and translates to English.

    Step 1 — ASR: fine-tuned Whisper (ahmedheakl/arazn-whisper-small-v2)
        Loaded directly via AutoProcessor + AutoModelForSpeechSeq2Seq.
        Audio is read with soundfile — no FFmpeg/torchcodec needed.

    Step 2 — Translation: PEFT/LoRA Llama 3 (ahmedheakl/arazn-llama3-english)
        Loaded via PeftConfig + PeftModel on top of the base Llama 3 model,
        exactly as shown in the official model card.

    Attributes:
        whisper_model_id: HuggingFace ID for the fine-tuned Whisper ASR model.
        translation_model_id: HuggingFace PEFT adapter ID for translation.
        device: Inference device ('cuda', 'cpu', or 'auto').
        max_new_tokens: Max tokens the translation LLM may generate.
    """

    def __init__(
        self,
        whisper_model_id: str = DEFAULT_WHISPER_MODEL,
        translation_model_id: str = DEFAULT_TRANSLATION_MODEL,
        device: str = "auto",
        max_new_tokens: int = 100,
    ) -> None:
        self.whisper_model_id = whisper_model_id
        self.translation_model_id = translation_model_id
        self.max_new_tokens = max_new_tokens

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # ASR artefacts
        self._asr_processor: Optional[AutoProcessor] = None
        self._asr_model: Optional[AutoModelForSpeechSeq2Seq] = None

        # Translation artefacts
        self._tokenizer: Optional[AutoTokenizer] = None
        self._translation_model: Optional[PeftModel] = None

        self._model_loaded = False

    # ------------------------------------------------------------------
    # Public API (mirrors FasterWhisperTranscriber)
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Load Whisper ASR model and PEFT translation model into memory."""
        if self._model_loaded:
            return

        # --- ASR model (fine-tuned Whisper) --------------------------------
        self._asr_processor = AutoProcessor.from_pretrained(self.whisper_model_id)
        self._asr_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.whisper_model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        self._asr_model.to(self.device)
        self._asr_model.eval()

        # --- Translation model (PEFT/LoRA Llama 3) -------------------------
        peft_config = PeftConfig.from_pretrained(self.translation_model_id)
        base_model_name = peft_config.base_model_name_or_path

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
        self._translation_model = PeftModel.from_pretrained(
            base_model,
            self.translation_model_id,
            device_map="auto",
        )
        self._translation_model.eval()

        self._tokenizer = AutoTokenizer.from_pretrained(self.translation_model_id)

        self._model_loaded = True

    def transcribe(self, audio_path: str, beam_size: int = 5) -> Dict[str, Any]:
        """
        Transcribe a code-switching audio file and translate to English.

        Returns a dict matching FasterWhisperTranscriber.transcribe():
            - text: Full English translation
            - segments: List of segment dicts with translated text + timestamps
            - language: 'ar'
            - language_probability: 1.0
            - duration: Audio duration in seconds
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self.load_model()

        # Load + normalise audio
        audio_array, sample_rate = sf.read(audio_path, dtype="float32")
        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)  # stereo → mono
        if sample_rate != TARGET_SAMPLE_RATE:
            audio_array = self._resample(audio_array, sample_rate, TARGET_SAMPLE_RATE)
        duration = len(audio_array) / TARGET_SAMPLE_RATE

        # Chunk into 30-second windows and transcribe each
        chunk_size = CHUNK_SECONDS * TARGET_SAMPLE_RATE
        audio_chunks = [
            audio_array[i : i + chunk_size]
            for i in range(0, len(audio_array), chunk_size)
        ]

        segments: List[Dict[str, Any]] = []
        raw_texts: List[str] = []

        for idx, chunk in enumerate(audio_chunks):
            chunk_start = idx * CHUNK_SECONDS
            chunk_end = min(chunk_start + CHUNK_SECONDS, duration)

            raw_text = self._asr_chunk(chunk, beam_size=beam_size)
            translated = self._translate(raw_text)
            raw_texts.append(raw_text)

            segments.append(
                {
                    "id": idx,
                    "start": float(chunk_start),
                    "end": float(chunk_end),
                    "text": translated,
                }
            )

        full_translated = self._translate(" ".join(raw_texts))

        return {
            "text": full_translated,
            "segments": segments,
            "language": "ar",
            "language_probability": 1.0,
            "duration": duration,
        }

    def unload_model(self) -> None:
        """Free all model memory."""
        for attr in (
            "_asr_model",
            "_asr_processor",
            "_translation_model",
            "_tokenizer",
        ):
            obj = getattr(self, attr, None)
            if obj is not None:
                del obj
                setattr(self, attr, None)

        if self.device == "cuda" or torch.cuda.is_available():
            torch.cuda.empty_cache()

        self._model_loaded = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _asr_chunk(self, audio_chunk: np.ndarray, beam_size: int = 5) -> str:
        """Run fine-tuned Whisper ASR on one 30-second audio chunk."""
        inputs = self._asr_processor(
            audio_chunk,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt",
        )
        input_features = inputs.input_features.to(
            self.device,
            dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        with torch.no_grad():
            predicted_ids = self._asr_model.generate(
                input_features,
                num_beams=beam_size,
            )
        result = self._asr_processor.batch_decode(
            predicted_ids, skip_special_tokens=True
        )
        return result[0].strip() if result else ""

    def _translate(self, text: str) -> str:
        """
        Translate mixed Arabic/English text to English using the PEFT Llama 3 model.
        Uses the exact prompt template and output parsing from the official model card.
        """
        if not text.strip():
            return text

        prompt = _LLAMA_PROMPT.format(source=text)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            generated_ids = self._translation_model.generate(
                **inputs,
                use_cache=True,
                num_return_sequences=1,
                max_new_tokens=self.max_new_tokens,
                num_beams=1,
                eos_token_id=self._tokenizer.eos_token_id,
                pad_token_id=self._tokenizer.pad_token_id,
            )

        if self.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        output = self._tokenizer.batch_decode(generated_ids)[0]
        # Extract only the assistant reply (official parsing from model card)
        translation = output.split("assistant<|end_header_id|>\n\n")[-1]
        translation = translation.split("<|eot_id|>")[0]
        return translation.strip()

    @staticmethod
    def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample via linear interpolation (no librosa dependency needed)."""
        if orig_sr == target_sr:
            return audio
        target_length = int(len(audio) * target_sr / orig_sr)
        return np.interp(
            np.linspace(0, len(audio) - 1, target_length),
            np.arange(len(audio)),
            audio,
        ).astype(np.float32)
