from core.audio_pipelines.MeetingPipeline import MeetingPipeline
from core.database.repos import MeetingChunkRepository, MeetingRepository
from core.config_loader import ConfigLoader
from core.database.tables_data import Meeting, MeetingChunk
from core.database.postgresDatabase import PostgresDatabase

config_loader = ConfigLoader()


def get_language_code(language: str) -> str:
    language_mapping = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "Arabic": "ar",
        "German": "de",
    }
    return language_mapping.get(language, "en")


# can add meta data later if needed, for now it is set to None
async def process_meeting_audio(
    file_path: str,
    language: str,
    project_name: str,
    title: str,
    date: str,
    company_id: int,
):
    # process meeting audio
    meetingPipeline = MeetingPipeline(
        enable_summarization=True, hf_token=config_loader.get("HF_TOKEN")
    )
    results = meetingPipeline.process(
        audio_path=file_path, language=get_language_code(language)
    )

    # return results
    try:
        meeting_data = Meeting(
            **{
                "title": title,
                "date": date,
                "language": results.get("language"),
                "duration_sec": results.get("duration"),
                "project_name": project_name,
                "meta": None,
                "company_id": company_id,
            }
        )
    except Exception as e:
        print(f"--- Error creating Meeting instance: {e} ---")
        return False

    # save to DB
    db = PostgresDatabase()
    meeting_repo = MeetingRepository(db.get_session_maker())
    try:
        meeting_id = await meeting_repo.create(meeting_data)
    except Exception as e:
        print(f"--- Error creating meeting in DB: {e} ---")
        return False
    if meeting_id:
        try:
            chunk_repo = MeetingChunkRepository(db.get_session_maker())
            for chunk in results.get("chunks", []):
                chunk_data = MeetingChunk(
                    **{
                        "raw_text": chunk.get("raw_text"),
                        "summary_text": chunk.get("summary_text"),
                        "start_time_sec": chunk.get("start_time_sec"),
                        "end_time_sec": chunk.get("end_time_sec"),
                        "embedding": chunk.get("embedding"),
                        "speaker_names": chunk.get("speaker_names", []),
                        "meeting_id": meeting_id,
                        "meta": None,
                    }
                )
                await chunk_repo.create(chunk_data)
        except Exception as e:
            print(f"--- Error creating meeting chunks in DB: {e} ---")
            return False
    else:
        print(f"--- Error: Meeting ID not returned after creation ---")
        return False
