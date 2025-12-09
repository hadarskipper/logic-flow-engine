"""Logging utilities for per-request log files."""

import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@contextmanager
def call_logging_context(call_id: str, job_submission_datetime: datetime, commit_sha: str, logs_dir: Optional[Path] = None):
    """
    Context manager for setting up per-call logging.
    
    Creates a dedicated log file for a specific call_id, commit_sha, and datetime,
    and ensures all logs during the context are written to that file.
    
    Args:
        call_id: Call identifier
        job_submission_datetime: Datetime when the job was submitted
        commit_sha: Commit SHA to include in filename
        logs_dir: Directory for log files (defaults to logs/ in project root)
        
    Yields:
        Path to the log file
    """
    if logs_dir is None:
        logs_dir = Path(__file__).parent.parent / "logs"
    
    logs_dir.mkdir(exist_ok=True)
    
    # Create log filename with call_id, commit_sha, and datetime
    # Use job_submission_datetime for the timestamp
    timestamp = job_submission_datetime.strftime("%Y%m%d_%H%M%S")
    # Sanitize call_id for filename (remove invalid characters)
    safe_call_id = "".join(c for c in call_id if c.isalnum() or c in ("-", "_"))[:50]
    # Sanitize commit_sha for filename (use first 8 characters, remove invalid characters)
    safe_commit_sha = "".join(c for c in commit_sha if c.isalnum())[:8]
    log_filename = f"call_{safe_call_id}_{safe_commit_sha}_{timestamp}.log"
    log_filepath = logs_dir / log_filename
    
    # Create file handler for this call
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    
    # Add handler to root logger to capture all logs
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    try:
        commit_info = f", commit_sha: {commit_sha}"
        job_submission_info = f", job_submission_datetime: {job_submission_datetime.isoformat()}"
        root_logger.info(f"Started logging for call_id: {call_id}{commit_info}{job_submission_info} to file: {log_filepath}")
        yield log_filepath
    finally:
        # Log completion before removing handler
        commit_info = f", commit_sha: {commit_sha}"
        job_submission_info = f", job_submission_datetime: {job_submission_datetime.isoformat()}"
        root_logger.info(f"Completed logging for call_id: {call_id}{commit_info}{job_submission_info}")
        # Remove handler and close file
        root_logger.removeHandler(file_handler)
        file_handler.close()


def get_latest_log_file(call_id: str, commit_sha: str, logs_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find the latest log file for a specific call_id and commit_sha.
    
    Args:
        call_id: Call identifier
        commit_sha: Commit SHA (full or partial)
        logs_dir: Directory for log files (defaults to logs/ in project root)
        
    Returns:
        Path to the latest log file, or None if not found
    """
    if logs_dir is None:
        logs_dir = Path(__file__).parent.parent / "logs"
    
    if not logs_dir.exists():
        return None
    
    # Sanitize call_id and commit_sha the same way as in call_logging_context
    safe_call_id = "".join(c for c in call_id if c.isalnum() or c in ("-", "_"))[:50]
    safe_commit_sha = "".join(c for c in commit_sha if c.isalnum())[:8]
    
    # Pattern: call_{call_id}_{commit_sha}_{timestamp}.log
    pattern = f"call_{safe_call_id}_{safe_commit_sha}_*.log"
    
    # Find all matching log files
    matching_files = list(logs_dir.glob(pattern))
    
    if not matching_files:
        return None
    
    # Sort by modification time (most recent first) and return the latest
    matching_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matching_files[0]

