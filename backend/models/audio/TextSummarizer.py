"""
Text Summarization and Embedding for Meeting Transcripts
Chunks meeting dialogue, generates summaries, and creates embeddings for semantic search.
"""

from core.rag.models import EMBED_MODEL
import torch
from typing import Optional, List, Dict, Any
from transformers import AutoModel, AutoTokenizer, pipeline
from langchain_ollama import OllamaEmbeddings


class TextSummarizer:
    """
    Text summarization and embedding for meeting transcripts.

    Provides:
    1. Intelligent chunking of long meeting dialogues
    2. Summarization of each chunk using fine-tuned models
    3. Semantic embeddings for search and retrieval

    Attributes:
        device: Device to run inference on (cuda, cpu)
        summarization_model: Model name for summarization
        embedding_model: Model name for embeddings
    """

    def __init__(
        self,
        device: str = "auto",
        summarization_model: str = "knkarthick/MEETING_SUMMARY",
        embedding_model: str = "mxbai-embed-large",
        max_tokens: int = 500,
        overlap_tokens: int = 100,
        summary_max_length: int = 150,
        summary_min_length: int = 50,
    ):
        """
        Initialize the text summarizer.

        Args:
            device: Device for inference ('cuda', 'cpu', or 'auto')
            summarization_model: HuggingFace model for summarization
            embedding_model: HuggingFace model for embeddings
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of overlapping tokens between chunks
            summary_max_length: Maximum length of generated summaries
            summary_min_length: Minimum length of generated summaries
        """
        self.device = self._resolve_device(device)
        self.summarization_model_name = summarization_model
        self.embedding_model_name = embedding_model
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.summary_max_length = summary_max_length
        self.summary_min_length = summary_min_length

        # Models (lazy loading)
        self.tokenizer = None
        self.summarizer = None
        self.tokenizer_embed = None
        self.embedder = None

        self._models_loaded = False

    def _resolve_device(self, device: str) -> str:
        """Resolve 'auto' device to actual device."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def load_models(self) -> None:
        """Load summarization and embedding models."""
        if self._models_loaded:
            return

        # Load summarization model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.summarization_model_name)

        # For transformers 5.0+, we need to use the model directly
        # instead of the pipeline for summarization
        from transformers import AutoModelForSeq2SeqLM

        summarization_model = AutoModelForSeq2SeqLM.from_pretrained(
            self.summarization_model_name
        )

        # Move to device
        if self.device == "cuda":
            summarization_model = summarization_model.cuda()

        self.summarizer = summarization_model

        # This Was The Code For The Dummy Embedding Model
        # Load embedding model
        # self.tokenizer_embed = AutoTokenizer.from_pretrained(self.embedding_model_name)
        # self.embedder = AutoModel.from_pretrained(self.embedding_model_name)

        self.embedder = OllamaEmbeddings(model=EMBED_MODEL)

        # Move embedder to device
        if self.device == "cuda":
            self.embedder = self.embedder.cuda()

        self._models_loaded = True

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        if not self._models_loaded:
            self.load_models()

        return len(
            self.tokenizer(text, return_tensors="pt", truncation=False)["input_ids"][0]
        )

    def summarize_text(self, text: str) -> str:
        """
        Generate a summary for the given text.

        Args:
            text: Input text to summarize

        Returns:
            Summary text
        """
        if not self._models_loaded:
            self.load_models()

        # Tokenize input
        inputs = self.tokenizer(
            text, return_tensors="pt", max_length=1024, truncation=True
        )

        # Move to device
        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Generate summary
        with torch.no_grad():
            summary_ids = self.summarizer.generate(
                inputs["input_ids"],
                max_length=self.summary_max_length,
                min_length=self.summary_min_length,
                num_beams=4,
                early_stopping=True,
            )

        # Decode summary
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary.strip()

    def generate_embedding(self, text: str) -> Any:
        """
        Generate semantic embedding for the given text.

        Args:
            text: Input text

        Returns:
            Numpy array of embeddings
        """
        if not self._models_loaded:
            self.load_models()

        inputs = self.tokenizer_embed(
            text, return_tensors="pt", truncation=True, padding=True
        )

        # Move to device
        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.embedder(**inputs)

        # Mean pooling over token embeddings
        embedding_vector = outputs.last_hidden_state.mean(dim=1)[0].cpu().numpy()

        return embedding_vector

    def finalize_chunk(
        self,
        chunk_index: int,
        start_time: float,
        end_time: float,
        speakers: set,
        raw_text: str,
        generate_summary: bool = True,
        generate_embedding: bool = True,
    ) -> Dict[str, Any]:
        """
        Finalize a chunk by generating summary and embedding.

        Args:
            chunk_index: Index of the chunk
            start_time: Start time in seconds
            end_time: End time in seconds
            speakers: Set of speaker IDs in this chunk
            raw_text: Raw text content
            generate_summary: Whether to generate summary
            generate_embedding: Whether to generate embedding

        Returns:
            Dictionary with chunk information
        """
        summary_text = None
        embedding_vector = None

        # Generate summary
        if generate_summary:
            summary_text = self.summarize_text(raw_text)

        # Generate embedding
        if generate_embedding:
            embedding_vector = self.generate_embedding(raw_text)

        return {
            "chunk_index": chunk_index,
            "start_time_sec": start_time,
            "end_time_sec": end_time,
            "speaker_ids": list(speakers),
            "raw_text": raw_text.strip(),
            "summary_text": summary_text,
            "embedding": embedding_vector,
        }

    def chunk_meeting_dialogue(
        self,
        meeting_json: Dict[str, Any],
        generate_summary: bool = True,
        generate_embedding: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Chunk meeting dialogue into manageable pieces with summaries and embeddings.

        Args:
            meeting_json: Meeting JSON with 'dialogue' key containing list of turns
            generate_summary: Whether to generate summaries
            generate_embedding: Whether to generate embeddings

        Returns:
            List of chunk dictionaries with summaries and embeddings
        """
        if not self._models_loaded:
            self.load_models()

        chunks = []

        current_text = ""
        current_start = None
        current_end = None
        current_speakers = set()
        chunk_index = 0

        for turn in meeting_json["dialogue"]:
            speaker = turn["speaker"]
            text = turn["text"].strip()
            start_sec = turn["start"]
            end_sec = turn["end"]

            if current_start is None:
                current_start = start_sec

            # Add turn
            current_text += f"{speaker}: {text} "
            current_end = end_sec
            current_speakers.add(speaker)

            # Check if we've reached the token threshold
            if self.count_tokens(current_text) >= self.max_tokens:
                chunks.append(
                    self.finalize_chunk(
                        chunk_index,
                        current_start,
                        current_end,
                        current_speakers,
                        current_text,
                        generate_summary,
                        generate_embedding,
                    )
                )

                chunk_index += 1

                # Create overlap for next chunk
                tokens = self.tokenizer(
                    current_text, return_tensors="pt", truncation=False
                )["input_ids"][0]

                overlap_tokens_list = tokens[-self.overlap_tokens :]
                overlap_text = self.tokenizer.decode(
                    overlap_tokens_list, skip_special_tokens=True
                )

                current_text = overlap_text + " "
                current_start = start_sec
                current_speakers = {speaker}

        # Add final chunk if there's remaining text
        if current_text.strip():
            chunks.append(
                self.finalize_chunk(
                    chunk_index,
                    current_start,
                    current_end,
                    current_speakers,
                    current_text,
                    generate_summary,
                    generate_embedding,
                )
            )

        return chunks

    def unload_models(self) -> None:
        """Unload models from memory."""
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        if self.summarizer:
            del self.summarizer
            self.summarizer = None

        if self.tokenizer_embed:
            del self.tokenizer_embed
            self.tokenizer_embed = None

        if self.embedder:
            del self.embedder
            self.embedder = None

        # Clear CUDA cache if using GPU
        if self.device == "cuda":
            torch.cuda.empty_cache()

        self._models_loaded = False
