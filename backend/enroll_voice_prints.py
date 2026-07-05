#!/usr/bin/env python3
"""
enroll_voice_prints.py
======================
Batch-enroll employee voice-prints into the Mind-Trace database.

Usage
-----
    python enroll_voice_prints.py --audio-dir <path> [OPTIONS]

Audio directory layout
-----------------------
Each audio file must be named after the **exact employee name** stored in the
database (spaces are fine).  The file extension can be any format that
``soundfile`` / ``librosa`` supports (wav, mp3, flac, ogg, …).

    voice_samples/
        Alice Johnson.wav
        Bob Smith.flac
        Carol White.mp3

Options
-------
    --audio-dir   Directory containing voice-sample files   (required)
    --company-id  Company ID to scope the employee lookup   (default: 1)
    --dry-run     Print what would happen without writing   (flag)
    --overwrite   Re-enroll even if voice_print already set (flag)

Examples
--------
    # Enroll everyone in the samples folder for company 1
    python enroll_voice_prints.py --audio-dir ./voice_samples

    # Preview without touching the database
    python enroll_voice_prints.py --audio-dir ./voice_samples --dry-run

    # Re-enroll a single employee even if already enrolled
    python enroll_voice_prints.py --audio-dir ./voice_samples --overwrite
"""

import argparse
import asyncio
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Allow running from either the repo root or the backend/ directory.
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# ---------------------------------------------------------------------------
# Imports (heavy ML libs are deferred to avoid loading them on --help)
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".opus"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enroll employee voice-prints from audio files into the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--audio-dir",
        required=True,
        type=Path,
        metavar="DIR",
        help="Directory containing one audio file per employee (filename = employee name).",
    )
    parser.add_argument(
        "--company-id",
        type=int,
        default=1,
        metavar="ID",
        help="Company ID used to look up employees (default: 1).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing to the database.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-enroll employees that already have a voice_print stored.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Core async enrollment logic
# ---------------------------------------------------------------------------

async def enroll(audio_dir: Path, company_id: int, dry_run: bool, overwrite: bool) -> None:
    """Main enrollment coroutine."""

    # --- lazy-load heavy dependencies ----------------------------------------
    from core.database.postgresDatabase import PostgresDatabase
    from core.database.repos import EmployeesRepository
    from core.database.tables_data import EmployeeUpdate
    from models.audio.SpeakerIdentification import extract_voice_embedding

    db = PostgresDatabase()
    emp_repo = EmployeesRepository(db.get_session_maker())

    # --- discover audio files ------------------------------------------------
    audio_files = sorted(
        f for f in audio_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not audio_files:
        print(f"[!] No supported audio files found in '{audio_dir}'.")
        print(f"    Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  Mind-Trace — Voice-Print Enrollment")
    print(f"{'=' * 60}")
    print(f"  Audio directory : {audio_dir.resolve()}")
    print(f"  Company ID      : {company_id}")
    print(f"  Files found     : {len(audio_files)}")
    print(f"  Dry-run         : {dry_run}")
    print(f"  Overwrite       : {overwrite}")
    print(f"{'=' * 60}\n")

    # --- fetch all employees for the company ---------------------------------
    all_employees = await emp_repo.get_all(company_id)
    employee_map: dict[str, object] = {emp.name: emp for emp in all_employees}

    if not employee_map:
        print(f"[!] No employees found for company_id={company_id}. Aborting.")
        sys.exit(1)

    print(f"[i] {len(employee_map)} employees loaded from DB.\n")

    # --- process each audio file ---------------------------------------------
    stats = {"enrolled": 0, "skipped": 0, "not_found": 0, "failed": 0}

    for audio_path in audio_files:
        employee_name = audio_path.stem          # filename without extension
        print(f"  ► Processing : '{audio_path.name}'  →  employee='{employee_name}'")

        # 1. Look up the employee
        employee = employee_map.get(employee_name)
        if employee is None:
            print(f"    [SKIP] Employee '{employee_name}' not found in DB.\n")
            stats["not_found"] += 1
            continue

        # 2. Skip if already enrolled (unless --overwrite)
        if employee.voice_print is not None and not overwrite:
            print(f"    [SKIP] Already enrolled (use --overwrite to re-enroll).\n")
            stats["skipped"] += 1
            continue

        # 3. Extract embedding
        try:
            print(f"    [INFO] Extracting WavLM embedding …")
            embedding: list[float] = extract_voice_embedding(str(audio_path)).tolist()
            print(f"    [INFO] Embedding extracted — dim={len(embedding)}")
        except Exception as exc:
            print(f"    [FAIL] Could not extract embedding: {exc}\n")
            stats["failed"] += 1
            continue

        # 4. Persist to DB
        if dry_run:
            print(f"    [DRY-RUN] Would update voice_print for '{employee_name}'.\n")
            stats["enrolled"] += 1
            continue

        try:
            update_data = EmployeeUpdate(voice_print=embedding)
            success = await emp_repo.update(employee_name, update_data)
            if success:
                print(f"    [OK] Voice-print saved for '{employee_name}'.\n")
                stats["enrolled"] += 1
            else:
                print(f"    [FAIL] DB update returned False for '{employee_name}'.\n")
                stats["failed"] += 1
        except Exception as exc:
            print(f"    [FAIL] DB error for '{employee_name}': {exc}\n")
            stats["failed"] += 1

    # --- summary -------------------------------------------------------------
    print(f"{'=' * 60}")
    print(f"  Enrollment Summary")
    print(f"{'=' * 60}")
    print(f"  Enrolled  : {stats['enrolled']}")
    print(f"  Skipped   : {stats['skipped']}  (already enrolled)")
    print(f"  Not found : {stats['not_found']}  (name not in DB)")
    print(f"  Failed    : {stats['failed']}  (extraction or DB error)")
    print(f"{'=' * 60}\n")

    if dry_run:
        print("[i] Dry-run complete. No data was written.\n")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()

    audio_dir: Path = args.audio_dir.resolve()
    if not audio_dir.is_dir():
        print(f"[!] '{audio_dir}' is not a directory or does not exist.")
        sys.exit(1)

    asyncio.run(enroll(
        audio_dir=audio_dir,
        company_id=args.company_id,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    ))


if __name__ == "__main__":
    main()