import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

import streamlit as st
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.audio.FasterWhisper import FasterWhisperTranscriber
from backend.core.audio_pipelines.MeetingPipeline import MeetingPipeline


# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="🎙️ Mind Trace",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Language code mapping
LANGUAGE_CODES = {
    "Auto-detect": None,
    "English": "en",
    "Arabic": "ar",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh",
    "Japanese": "ja",
}

SUPPORTED_FORMATS = [
    "mp3",
    "wav",
    "m4a",
    "flac",
    "ogg",
    "wma",
    "aac",
    "mp4",
    "webm",
    "mpeg",
]


# =============================================================================
# Styles Loading
# =============================================================================


def load_css():
    """Load external CSS file."""
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ CSS file not found. Using default styles.")


# =============================================================================
# Session State Management
# =============================================================================


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "transcription_result": None,
        "diarization_result": None,
        "transcriber": None,
        "meeting_pipeline": None,
        "model_loaded": False,
        "pipeline_loaded": False,
        "current_model_config": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_model_loaded() -> bool:
    """Check if a model is currently loaded."""
    return (
        st.session_state.transcriber is not None
        and st.session_state.transcriber.model is not None
        and st.session_state.model_loaded
    )


def get_model_info() -> dict:
    """Get information about the currently loaded model."""
    if st.session_state.current_model_config:
        return st.session_state.current_model_config
    return None


# =============================================================================
# Helper Functions
# =============================================================================


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_timestamp(seconds: float) -> str:
    """Format timestamp to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# =============================================================================
# UI Components
# =============================================================================


def render_header():
    """Render the app header."""
    st.markdown('<h1 class="main-header">🎙️ Mind Trace</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Transform your audio into text with AI-powered transcription</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


def render_model_status():
    """Render the model status indicator."""
    if is_model_loaded():
        model_info = get_model_info()
        st.markdown(
            f"""
        <div class="model-status model-loaded">
            <span class="status-icon">✅</span>
            <span class="status-text">Model Loaded: {model_info['model_size']} ({model_info['device']})</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <div class="model-status model-not-loaded">
            <span class="status-icon">⚠️</span>
            <span class="status-text">No Model Loaded</span>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_sidebar() -> dict:
    """Render the sidebar with settings and model controls."""
    with st.sidebar:
        st.markdown("### 🤖 Model Management")
        st.markdown("---")

        # Model status
        render_model_status()

        # Model settings
        model_size = st.selectbox(
            "📦 Model Size",
            options=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            index=4,  # Default to large-v2
            help="Larger models are more accurate but slower",
        )

        device = st.selectbox(
            "💻 Device",
            options=["auto", "cuda", "cpu"],
            index=0,
            help="Select computation device",
        )

        compute_type = st.selectbox(
            "⚡ Compute Type",
            options=["float16", "int8", "int8_float16", "float32"],
            index=0,
            help="Precision type for computation",
        )

        # Model control buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 Load Model", use_container_width=True, type="primary"):
                load_model(model_size, device, compute_type)

        with col2:
            if st.button(
                "🗑️ Unload", use_container_width=True, disabled=not is_model_loaded()
            ):
                unload_model()

        st.markdown("---")
        st.markdown("### 🎛️ Transcription Options")

        # Language selection
        language = st.selectbox(
            "🌍 Language",
            options=list(LANGUAGE_CODES.keys()),
            index=0,
            help="Select audio language or auto-detect",
        )

        # Task selection
        task = st.radio(
            "📝 Task",
            options=["Transcribe", "Translate to English"],
            index=0,
            help="Transcribe in original language or translate to English",
        )

        # VAD filter
        vad_filter = st.checkbox(
            "🔇 VAD Filter",
            value=True,
            help="Filter out silent parts for faster processing",
        )

        # Word timestamps
        word_timestamps = st.checkbox(
            "⏱️ Word Timestamps", value=True, help="Include word-level timestamps"
        )

        st.markdown("---")
        st.markdown("### 🗣️ Speaker Diarization")

        # Speaker diarization toggle
        enable_diarization = st.checkbox(
            "👥 Enable Speaker Diarization",
            value=False,
            help="Identify different speakers in the audio (requires HF_TOKEN)",
        )

        num_speakers = None
        enable_speaker_identification = False
        if enable_diarization:
            speaker_mode = st.radio(
                "Speaker Detection",
                options=["Auto-detect", "Specify number"],
                index=0,
                help="Auto-detect or specify the number of speakers",
            )

            if speaker_mode == "Specify number":
                num_speakers = st.number_input(
                    "Number of speakers",
                    min_value=2,
                    max_value=10,
                    value=2,
                    help="Exact number of speakers in the audio",
                )
                
            enable_speaker_identification = st.checkbox(
                "🔍 Identify Speakers using Enrolled DB",
                value=False,
                help="Use the tempDB to match detected speakers with enrolled voiceprints."
            )

        st.markdown("---")
        st.markdown("### 📊 Text Summarization")

        # Summarization toggle
        enable_summarization = st.checkbox(
            "📝 Enable Summarization",
            value=False,
            help="Generate summaries and embeddings for meeting chunks",
        )

        summarization_config = {}
        if enable_summarization:
            with st.expander("⚙️ Advanced Settings", expanded=False):
                max_tokens = st.slider(
                    "Max tokens per chunk",
                    min_value=200,
                    max_value=1000,
                    value=500,
                    step=50,
                    help="Maximum tokens in each chunk",
                )

                overlap_tokens = st.slider(
                    "Overlap tokens",
                    min_value=0,
                    max_value=200,
                    value=100,
                    step=25,
                    help="Number of overlapping tokens between chunks",
                )

                summarization_config = {
                    "max_tokens": max_tokens,
                    "overlap_tokens": overlap_tokens,
                }

        st.markdown("---")
        st.markdown("### 🔤 Code-Switching (Arabic)")

        enable_code_switching = st.checkbox(
            "🌐 Enable Arabic Code-Switching",
            value=False,
            help="When Arabic is detected, use a fine-tuned Whisper + PEFT Llama 3 to transcribe and translate code-switched speech to English",
        )

        code_switching_config = {}
        if enable_code_switching:
            with st.expander("⚙️ Model Settings", expanded=False):
                cs_whisper_model = st.text_input(
                    "ASR Model (HuggingFace ID)",
                    value="ahmedheakl/arazn-whisper-small-v2",
                    help="Fine-tuned Whisper model for Arabic-English code-switching",
                )
                cs_translation_model = st.text_input(
                    "Translation Model (HuggingFace PEFT ID)",
                    value="ahmedheakl/arazn-llama3-english",
                    help="PEFT/LoRA adapter on Llama 3 for Arabic→English translation (loaded via HuggingFace, no Ollama needed)",
                )
                code_switching_config = {
                    "whisper_model_id": cs_whisper_model,
                    "translation_model_id": cs_translation_model,
                }

        st.markdown("---")
        st.markdown(
            """
        <div class="info-box">
            <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">
                💡 <strong>Tip:</strong> Load the model first, then upload your audio file for transcription.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        return {
            "model_size": model_size,
            "device": device,
            "compute_type": compute_type,
            "language": LANGUAGE_CODES[language],
            "task": "transcribe" if task == "Transcribe" else "translate",
            "vad_filter": vad_filter,
            "word_timestamps": word_timestamps,
            "enable_diarization": enable_diarization,
            "num_speakers": num_speakers,
            "enable_summarization": enable_summarization,
            "summarization_config": summarization_config,
            "enable_code_switching": enable_code_switching,
            "code_switching_config": code_switching_config,
            "enable_speaker_identification": enable_speaker_identification,
        }


def render_upload_section():
    """Render the file upload section."""
    st.markdown("### 📁 Upload Audio File")

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=SUPPORTED_FORMATS,
        help=f"Supported formats: {', '.join(f.upper() for f in SUPPORTED_FORMATS)}",
    )

    return uploaded_file


def render_results(result: dict):
    """Render the transcription results."""
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📊 Transcription Results")

    # Stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{result['language'].upper()}</div>
            <div class="stat-label">Language</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{result['language_probability']:.1%}</div>
            <div class="stat-label">Confidence</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{format_duration(result['duration'])}</div>
            <div class="stat-label">Duration</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{len(result['segments'])}</div>
            <div class="stat-label">Segments</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(
        ["📝 Full Transcript", "⏱️ With Timestamps", "🔍 Segments"]
    )

    with tab1:
        st.markdown(
            f"""
        <div class="transcript-container">
            <p class="transcript-text">{result['text']}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label="📋 Download Transcript",
            data=result["text"],
            file_name="transcript.txt",
            mime="text/plain",
        )

    with tab2:
        transcript_with_timestamps = ""
        for segment in result["segments"]:
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            transcript_with_timestamps += f"[{start} → {end}] {segment['text']}\n\n"

        st.markdown(
            f"""
        <div class="transcript-container">
            <pre class="transcript-text" style="white-space: pre-wrap;">{transcript_with_timestamps}</pre>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label="📋 Download with Timestamps",
            data=transcript_with_timestamps,
            file_name="transcript_timestamps.txt",
            mime="text/plain",
        )

    with tab3:
        for i, segment in enumerate(result["segments"]):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])

            with st.expander(f"Segment {i+1} [{start} → {end}]"):
                st.markdown(f"**Text:** {segment['text']}")
                st.markdown(
                    f"**Start:** {segment['start']:.2f}s | **End:** {segment['end']:.2f}s"
                )

                if "words" in segment and segment["words"]:
                    st.markdown("**Words:**")
                    words_df = {
                        "Word": [w["word"] for w in segment["words"]],
                        "Start": [f"{w['start']:.2f}s" for w in segment["words"]],
                        "End": [f"{w['end']:.2f}s" for w in segment["words"]],
                        "Confidence": [
                            f"{w['probability']:.1%}" for w in segment["words"]
                        ],
                    }
                    st.dataframe(words_df, use_container_width=True)


# Speaker colors for dialogue view
SPEAKER_COLORS = [
    "#60a5fa",  # Blue
    "#34d399",  # Green
    "#f472b6",  # Pink
    "#fbbf24",  # Yellow
    "#a78bfa",  # Purple
    "#fb923c",  # Orange
    "#2dd4bf",  # Teal
    "#f87171",  # Red
]


def render_dialogue_results(result: dict):
    """Render the speaker diarization dialogue results."""
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 🗣️ Meeting Dialogue")

    # Check if we have chunks (summarization enabled)
    has_summaries = "chunks" in result and result["chunks"]

    # Stats row
    if has_summaries:
        col1, col2, col3, col4, col5 = st.columns(5)
    else:
        col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{result['num_speakers']}</div>
            <div class="stat-label">Speakers</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{result['language'].upper()}</div>
            <div class="stat-label">Language</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{format_duration(result['duration'])}</div>
            <div class="stat-label">Duration</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-value">{len(result['dialogue'])}</div>
            <div class="stat-label">Turns</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if has_summaries:
        with col5:
            st.markdown(
                f"""
            <div class="stat-card">
                <div class="stat-value">{len(result['chunks'])}</div>
                <div class="stat-label">Summaries</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Create speaker color mapping
    speaker_colors = {}
    for i, speaker in enumerate(result.get("speakers", [])):
        speaker_colors[speaker] = SPEAKER_COLORS[i % len(SPEAKER_COLORS)]

    # Tabs for different views
    if has_summaries:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["💬 Dialogue View", "📋 Summaries", "📝 Text Format", "📊 JSON Export"]
        )
    else:
        tab1, tab2, tab3 = st.tabs(
            ["💬 Dialogue View", "📝 Text Format", "📊 JSON Export"]
        )

    with tab1:
        for entry in result["dialogue"]:
            speaker = entry["speaker"]
            color = speaker_colors.get(speaker, "#94a3b8")
            start = format_timestamp(entry["start"])
            end = format_timestamp(entry["end"])

            st.markdown(
                f"""
            <div style="margin-bottom: 1rem; padding: 0.75rem; background: rgba(30, 41, 59, 0.5); border-radius: 8px; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: {color}; font-weight: 600;">{speaker}</span>
                    <span style="color: #64748b; font-size: 0.85rem;">{start} → {end}</span>
                </div>
                <p style="margin: 0; color: #e2e8f0;">{entry['text']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Summaries tab (only if summarization was enabled)
    if has_summaries:
        with tab2:
            st.markdown("#### 📋 Meeting Summaries")
            st.markdown(
                "AI-generated summaries of meeting chunks with semantic embeddings."
            )
            st.markdown("<br>", unsafe_allow_html=True)

            for chunk in result["chunks"]:
                with st.expander(
                    f"📌 Chunk {chunk['chunk_index'] + 1} ({format_timestamp(chunk['start_time_sec'])} → {format_timestamp(chunk['end_time_sec'])})",
                    expanded=True,
                ):
                    # Summary
                    st.markdown("**Summary:**")
                    st.info(chunk["summary_text"])

                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Duration",
                            f"{chunk['end_time_sec'] - chunk['start_time_sec']:.1f}s",
                        )
                    with col2:
                        st.metric("Speakers", len(chunk["speaker_ids"]))
                    with col3:
                        if chunk["embedding"] is not None:
                            st.metric("Embedding Dim", len(chunk["embedding"]))

                    # Speakers involved
                    st.markdown(f"**Speakers:** {', '.join(chunk['speaker_ids'])}")

                    # Raw text preview
                    with st.expander("📄 View Raw Text", expanded=False):
                        st.text(
                            chunk["raw_text"][:500] + "..."
                            if len(chunk["raw_text"]) > 500
                            else chunk["raw_text"]
                        )

            # Download summaries
            st.markdown("<br>", unsafe_allow_html=True)
            summaries_text = ""
            for chunk in result["chunks"]:
                summaries_text += f"=== Chunk {chunk['chunk_index'] + 1} ==="
                summaries_text += f"\nTime: {format_timestamp(chunk['start_time_sec'])} → {format_timestamp(chunk['end_time_sec'])}\n"
                summaries_text += f"Speakers: {', '.join(chunk['speaker_ids'])}\n"
                summaries_text += f"Summary: {chunk['summary_text']}\n\n"

            st.download_button(
                label="📥 Download All Summaries",
                data=summaries_text,
                file_name="meeting_summaries.txt",
                mime="text/plain",
            )

    # Text format tab
    tab_idx = 3 if has_summaries else 2
    with tab3 if has_summaries else tab2:
        dialogue_text = ""
        for entry in result["dialogue"]:
            dialogue_text += f"{entry['speaker']}: {entry['text']}\n\n"

        st.markdown(
            f"""
        <div class="transcript-container">
            <pre class="transcript-text" style="white-space: pre-wrap;">{dialogue_text}</pre>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label="📋 Download Dialogue",
            data=dialogue_text,
            file_name="meeting_dialogue.txt",
            mime="text/plain",
        )

    # JSON export tab
    with tab4 if has_summaries else tab3:
        import json

        # Convert numpy arrays to lists for JSON serialization
        result_copy = result.copy()
        if "chunks" in result_copy:
            for chunk in result_copy["chunks"]:
                if chunk.get("embedding") is not None:
                    chunk["embedding"] = chunk["embedding"].tolist()

        json_output = json.dumps(result_copy, indent=2, ensure_ascii=False)

        st.code(json_output, language="json")

        st.download_button(
            label="📋 Download JSON",
            data=json_output,
            file_name="meeting_dialogue.json",
            mime="application/json",
        )


def render_empty_state():
    """Render the empty state when no file is uploaded."""
    st.markdown(
        """
    <div class="empty-state">
        <p class="empty-state-icon">🎵</p>
        <p class="empty-state-title">Drop your audio file here</p>
        <p class="empty-state-subtitle">Supported formats: MP3, WAV, M4A, FLAC, and more</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Model Operations
# =============================================================================


def load_model(model_size: str, device: str, compute_type: str):
    """Load the Whisper model with the specified configuration."""
    with st.spinner(f"Loading {model_size} model..."):
        try:
            # Unload existing model if any
            if st.session_state.transcriber is not None:
                st.session_state.transcriber.unload_model()

            # Create new transcriber and load model
            transcriber = FasterWhisperTranscriber(
                model_size=model_size, device=device, compute_type=compute_type
            )
            transcriber.load_model()

            # Update session state
            st.session_state.transcriber = transcriber
            st.session_state.model_loaded = True
            st.session_state.current_model_config = {
                "model_size": model_size,
                "device": device,
                "compute_type": compute_type,
            }

            st.success(f"✅ Model '{model_size}' loaded successfully!")
            st.rerun()

        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Failed to load model: {error_msg}")

            # Provide specific help for Windows permission errors
            if "WinError 1314" in error_msg or "privilege" in error_msg.lower():
                st.markdown(
                    """
                <div class="warning-box">
                    <p style="margin: 0; color: #f59e0b;">
                        <strong>⚠️ Windows Permission Issue Detected</strong><br><br>
                        This error occurs due to Windows symlink restrictions. Try one of these solutions:
                    </p>
                    <ol style="color: #f59e0b; margin-top: 0.5rem; margin-bottom: 0;">
                        <li><strong>Run as Administrator:</strong> Right-click on your terminal/PowerShell and select "Run as Administrator", then restart the app.</li>
                        <li><strong>Enable Developer Mode:</strong> Go to Settings → Update & Security → For Developers → Enable Developer Mode (Windows 10/11).</li>
                        <li><strong>Clear Cache & Retry:</strong> Delete the folder <code>C:\\Users\\windows 11\\.cache\\huggingface</code> and try again.</li>
                    </ol>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.session_state.model_loaded = False


def unload_model():
    """Unload the current model from memory."""
    try:
        if st.session_state.transcriber is not None:
            st.session_state.transcriber.unload_model()

        st.session_state.transcriber = None
        st.session_state.model_loaded = False
        st.session_state.current_model_config = None

        st.success("✅ Model unloaded successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to unload model: {str(e)}")


def transcribe_audio(audio_path: str, settings: dict) -> dict:
    """Transcribe an audio file using the loaded model."""
    if not is_model_loaded():
        raise RuntimeError("No model is loaded. Please load a model first.")

    return st.session_state.transcriber.transcribe(
        audio_path=audio_path,
        language=settings["language"],
        task=settings["task"],
        vad_filter=settings["vad_filter"],
        word_timestamps=settings["word_timestamps"],
    )


# =============================================================================
# Main Application
# =============================================================================


def main():
    """Main application entry point."""
    # Initialize
    load_css()
    init_session_state()

    # Render UI
    render_header()
    
    app_mode = st.sidebar.radio("Navigation", ["📝 Meeting Transcription", "🎙️ Speaker Enrollment"])
    st.sidebar.markdown("---")
    
    if app_mode == "📝 Meeting Transcription":
        settings = render_sidebar()

        # Main content area
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = render_upload_section()

        with col2:
            if uploaded_file:
                st.markdown("### 🎵 Audio Preview")
                st.audio(uploaded_file, format=uploaded_file.type)

        # Transcription section
        if uploaded_file:
            st.markdown("<br>", unsafe_allow_html=True)

            # Determine mode and model requirements
            use_diarization = settings.get("enable_diarization", False)

            if use_diarization:
                # For diarization mode (token is configured in model files)
                if st.button("🚀 Process Meeting", use_container_width=True):
                    run_diarization(uploaded_file, settings)

                # Display diarization results if available
                if st.session_state.diarization_result:
                    render_dialogue_results(st.session_state.diarization_result)
            else:
                # Standard transcription mode
                if not is_model_loaded():
                    st.markdown(
                        """
                    <div class="warning-box">
                        <p style="margin: 0; color: #f59e0b;">
                            ⚠️ <strong>Model Required:</strong> Please load a model from the sidebar before transcribing.
                        </p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "🚀 Transcribe Audio", use_container_width=True, disabled=True
                    )
                else:
                    if st.button("🚀 Transcribe Audio", use_container_width=True):
                        run_transcription(uploaded_file, settings)

                # Display transcription results if available
                if st.session_state.transcription_result:
                    render_results(st.session_state.transcription_result)
        else:
            render_empty_state()
    else:
        render_enrollment_page()

def render_enrollment_page():
    st.markdown("## 🎙️ Speaker Enrollment")
    st.markdown("Enroll new speakers into the database for automatic identification during meeting transcription.")
    
    from Models.audio.tempDB.database_manager import DatabaseManager
    from Models.audio.SpeakerIdentification import extract_voice_embedding
    
    db = DatabaseManager()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Add New Speaker")
        name = st.text_input("Speaker Name", help="Full name of the speaker")
        company = st.text_input("Company/Role", help="Optional organizational role")
        
        # Audio upload for enrollment
        enroll_audio = st.file_uploader("Upload Voice Sample (min 3-5 seconds)", type=SUPPORTED_FORMATS, key="enroll_audio")
        
        if st.button("💾 Enroll Voiceprint", type="primary"):
            if not name:
                st.error("Please enter a speaker name.")
            elif not enroll_audio:
                st.error("Please upload a voice sample.")
            else:
                with st.spinner("Extracting voiceprint..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(enroll_audio.name).suffix) as tmp_file:
                        tmp_file.write(enroll_audio.getvalue())
                        tmp_path = tmp_file.name
                        
                    try:
                        embedding = extract_voice_embedding(tmp_path)
                        success = db.add_speaker(name, company, embedding)
                        if success:
                            st.success(f"✅ Successfully enrolled {name}!")
                        else:
                            st.error(f"❌ Speaker '{name}' already exists in database.")
                    except Exception as e:
                        st.error(f"Failed to process audio: {str(e)}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                            
    with col2:
        st.markdown("### Enrolled Speakers")
        speakers = db.get_all_speakers()
        if speakers:
            for spk in speakers:
                with st.expander(f"👤 {spk['name']} - {spk.get('company', '')}"):
                    if st.button("Delete Speaker", key=f"del_{spk['id']}"):
                        db.delete_speaker(spk['id'])
                        st.rerun()
        else:
            st.info("No speakers enrolled yet.")


def run_transcription(uploaded_file, settings: dict):
    """Run the transcription process."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Save uploaded file temporarily
    status_text.markdown("📥 **Processing audio file...**")
    progress_bar.progress(10)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(uploaded_file.name).suffix
    ) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Transcribe
        status_text.markdown("🎙️ **Transcribing audio...**")
        progress_bar.progress(50)

        result = transcribe_audio(tmp_path, settings)

        progress_bar.progress(100)
        status_text.markdown("✅ **Transcription complete!**")

        # Store result
        st.session_state.transcription_result = result

    except Exception as e:
        st.error(f"❌ Transcription failed: {str(e)}")

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def run_diarization(uploaded_file, settings: dict):
    """Run the speaker diarization pipeline."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Save uploaded file temporarily
    status_text.markdown("📥 **Processing audio file...**")
    progress_bar.progress(10)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(uploaded_file.name).suffix
    ) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Initialize pipeline if not loaded
        status_text.markdown("🔧 **Loading diarization models...**")
        progress_bar.progress(20)

        if st.session_state.meeting_pipeline is None:
            st.session_state.meeting_pipeline = MeetingPipeline(
                whisper_model_size=settings["model_size"],
                device=settings["device"],
                compute_type=settings["compute_type"],
                use_vad=settings["vad_filter"],
                enable_summarization=settings.get("enable_summarization", False),
                summarization_config=settings.get("summarization_config", {}),
                enable_code_switching=settings.get("enable_code_switching", False),
                code_switching_config=settings.get("code_switching_config", {}),
                enable_speaker_identification=settings.get("enable_speaker_identification", False),
            )

        # Run diarization
        status_text.markdown("🗣️ **Identifying speakers...**")
        progress_bar.progress(40)

        status_text.markdown("🎙️ **Transcribing with speaker labels...**")
        progress_bar.progress(60)

        result = st.session_state.meeting_pipeline.process(
            tmp_path,
            language=settings["language"],
            num_speakers=settings.get("num_speakers"),
        )

        progress_bar.progress(100)
        status_text.markdown("✅ **Meeting processing complete!**")

        # Store result
        st.session_state.diarization_result = result

    except Exception as e:
        st.error(f"❌ Diarization failed: {str(e)}")
        import traceback

        st.error(traceback.format_exc())

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    main()
