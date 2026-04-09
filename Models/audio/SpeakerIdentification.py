# Models/audio/SpeakerIdentification.py
"""Speaker Identification utilities.

This module provides a lightweight interface for generating speaker
embeddings using WavLM X-Vector, and performing fast similarity searches.

The public API includes:
* `compute_cosine_similarity` – cosine similarity between two vectors.
* `extract_voice_embedding` – convenience wrapper around a global `SpeakerEncoder`.
* `identify_speaker_by_embedding` – return the most similar known speaker name and score, or `("-1", 0.0)`.
* `generate_similarity_matrix_string` – returns a string representation of similarity scores.

"""

import os
import numpy as np
from typing import Dict, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  

# ---------------------------------------------------------------------------
# Configuration (read from .env or defaults)
# ---------------------------------------------------------------------------
SPEAKER_MODEL = os.getenv("SPEAKER_MODEL", "wavlm")
SPEAKER_SIMILARITY_THRESHOLD = float(os.getenv("SPEAKER_SIMILARITY_THRESHOLD", "0.7"))

# ---------------------------------------------------------------------------
# Model abstraction
# ---------------------------------------------------------------------------
class SpeakerEncoder:
    """Wraps a speaker embedding model using Whisper for speaker verification."""

    def __init__(self, model_name: str = "wavlm"):
        self.model_name = model_name.lower()
        if self.model_name in ("wavlm", "whisper"): # fallback alias
            # Use WavLM's X-Vector states as embeddings
            from transformers import AutoFeatureExtractor, AutoModelForAudioXVector
            import torch

            model_id = "microsoft/wavlm-base-plus-sv"
            
            # Set HF_TOKEN if available
            hf_token = os.getenv("HF_TOKEN")
            token_kwargs = {"token": hf_token} if hf_token else {}
            
            self.processor = AutoFeatureExtractor.from_pretrained(model_id, **token_kwargs)
            self.model = AutoModelForAudioXVector.from_pretrained(model_id, **token_kwargs)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model.eval()
        else:
            raise ValueError(f"Unsupported speaker model: {model_name}")
    
    def encode(self, audio_path: str) -> np.ndarray:
        """Return a normalized embedding for ``audio_path``.

        The audio is loaded with ``soundfile`` and resampled to 16kHz.
        """
        import soundfile as sf
        import torch

        # Load and resample to 16 kHz mono
        wav, sr = sf.read(audio_path)
        if wav.ndim > 1:
            wav = np.mean(wav, axis=1)
        if sr != 16000:
            import librosa
            wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
            sr = 16000
        wav = wav.astype(np.float32)

        # WavLM path
        inputs = self.processor(wav, sampling_rate=sr, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            # Get natively pooled x-vector outputs
            outputs = self.model(**inputs)
            
        # Extract the 512-dim embedding
        embedding = outputs.embeddings.squeeze().cpu().numpy()

        # L2‑normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

# Global encoder instance (lazy‑loaded on first use)
_encoder_instance: SpeakerEncoder | None = None

def _get_encoder() -> SpeakerEncoder:
    global _encoder_instance
    if _encoder_instance is None:
        _encoder_instance = SpeakerEncoder(SPEAKER_MODEL)
    return _encoder_instance

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Cosine similarity between two L2‑normalized vectors."""
    if emb1.shape != emb2.shape:
        raise ValueError("Embedding shapes do not match for similarity computation")
    return float(np.dot(emb1, emb2))

def extract_voice_embedding(audio_path: str) -> np.ndarray:
    """Convenient wrapper that returns a normalized embedding for ``audio_path``."""
    encoder = _get_encoder()
    return encoder.encode(audio_path)

def identify_speaker_by_embedding(
    query_emb: np.ndarray, 
    known_speakers: Dict[str, np.ndarray], 
    threshold: float = SPEAKER_SIMILARITY_THRESHOLD
) -> Tuple[str, float]:
    """Return the most similar speaker name and their similarity score.
    
    If no match exceeds `threshold`, returns ("-1", highest_score).
    """
    if not known_speakers:
        return "-1", 0.0
        
    best_name = "-1"
    best_score = -1.0
    
    for name, stored_emb in known_speakers.items():
        score = compute_cosine_similarity(query_emb, stored_emb)
        if score > best_score:
            best_score = score
            best_name = name
            
    if best_score >= threshold:
        return best_name, best_score
        
    return "-1", best_score




# used in testing only 
def generate_similarity_matrix_string(known_speakers: Dict[str, np.ndarray]) -> str:
    """Generate a formatted string of similarity scores between all enrolled speakers."""
    if not known_speakers:
        return "No speakers enrolled yet."

    speakers = list(known_speakers.keys())
    
    lines = []
    lines.append(f"Similarity matrix for {len(speakers)} speakers:")
    lines.append("-" * (len(speakers) * 8 + 15))

    # Header
    header = " " * 12
    for name in speakers:
        header += f"{name[:7]:>8}"
    lines.append(header)

    # Matrix
    for i, name1 in enumerate(speakers):
        row = f"{name1[:12]:<12}"
        for j, name2 in enumerate(speakers):
            if i == j:
                row += "  1.000  "
            else:
                similarity = compute_cosine_similarity(known_speakers[name1], known_speakers[name2])
                row += f"{similarity:>8.3f}"
        lines.append(row)
        
    return "\n".join(lines)
