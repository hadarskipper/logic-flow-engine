"""FastAPI application for healthcare call processing."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from engine.tree_executor import TreeExecutor
from github_client import get_default_github_url, get_latest_commit_sha
from models.schemas import HealthResponse, LogFileResponse, ProcessCallResponse, ResultResponse, TreeStructureResponse
from utils.logging_utils import call_logging_context, get_latest_log_file

# Configure base logging (console output)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Console only, file handlers added per request
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Decision Tree Call Processing API",
    description="Process healthcare call audio files using YAML-based decision tree workflow",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from your webapp
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Default GitHub config URL (from github_client)
DEFAULT_GITHUB_CONFIG_URL = get_default_github_url()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status response
    """
    return HealthResponse(status="healthy", message="API is running")


@app.get("/tree-structure", response_model=TreeStructureResponse)
async def get_tree_structure(
    commit_sha: Optional[str] = Query(None, description="Optional commit SHA for GitHub config (defaults to latest)")
):
    """
    Get the current decision tree structure.
    
    Args:
        commit_sha: Optional commit SHA for GitHub config (defaults to latest/main branch)
        
    Returns:
        Tree structure information
    """
    try:
        # Get latest commit SHA if not provided
        if commit_sha is None:
            commit_sha = get_latest_commit_sha()
            logger.info(f"Fetched latest commit SHA: {commit_sha}")
        
        tree_executor = TreeExecutor(DEFAULT_GITHUB_CONFIG_URL, commit_sha=commit_sha)
        structure = tree_executor.get_tree_structure()
        return TreeStructureResponse(**structure)
    except Exception as e:
        logger.error(f"Error retrieving tree structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_call_background(
    audio_content: bytes,
    filename: str,
    call_id: str,
    commit_sha: str,
    job_submission_datetime: datetime
):
    """Background task to process the call asynchronously."""
    # Set up per-call logging with call_id, commit_sha, and job submission datetime
    with call_logging_context(call_id, job_submission_datetime, commit_sha) as log_filepath:
        try:
            logger.info(f"Processing call: {call_id}, File: {filename}, Commit SHA: {commit_sha or 'latest'}")
            logger.info(f"Log file: {log_filepath}")
            
            # Prepare initial workflow data
            initial_workflow_data = {
                "audio_file": audio_content,  # Store file content for processing
                "call_id": call_id,
                "filename": filename,
                "job_submission_datetime": job_submission_datetime.isoformat(),
            }
            
            # Create tree executor with GitHub config and commit SHA
            tree_executor = TreeExecutor(DEFAULT_GITHUB_CONFIG_URL, commit_sha=commit_sha)
            
            # Execute decision tree (this will save results internally)
            result = tree_executor.execute(initial_workflow_data)
            
            logger.info(f"Call processing completed: {result['status']}")
        
        except Exception as e:
            logger.error(f"Error processing call in background: {e}", exc_info=True)


@app.post("/process-call")
async def process_call(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(..., description="MP3 audio file to process"),
    call_id: str = "default",
    commit_sha: Optional[str] = Query(None, description="Optional commit SHA for GitHub config (defaults to latest)")
):
    """
    Process a healthcare call audio file through the decision tree.
    
    Args:
        audio_file: MP3 audio file uploaded via multipart form
        call_id: Optional call identifier for metadata lookup
        commit_sha: Optional commit SHA for GitHub config (defaults to latest/main branch)
        
    Returns:
        Immediate response indicating job registration
    """
    # Get latest commit SHA if not provided
    if commit_sha is None:
        try:
            commit_sha = get_latest_commit_sha()
            logger.info(f"Fetched latest commit SHA: {commit_sha}")
        except Exception as e:
            logger.error(f"Failed to fetch latest commit SHA: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch latest commit SHA from GitHub: {str(e)}"
            )
    
    # Validate file type
    if not audio_file.filename.endswith((".mp3", ".MP3")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only MP3 files are supported.",
        )
    
    # Read audio file content
    audio_content = await audio_file.read()
    
    # Create job submission datetime
    job_submission_datetime = datetime.now()
    
    # Add background task to process the call
    background_tasks.add_task(
        _process_call_background,
        audio_content=audio_content,
        filename=audio_file.filename,
        call_id=call_id,
        commit_sha=commit_sha,
        job_submission_datetime=job_submission_datetime
    )
    
    # Return immediately
    return JSONResponse(
        status_code=200,
        content={"message": f"job registered with call id {call_id}"}
    )


@app.get("/logs/{call_id}", response_model=LogFileResponse)
async def get_log_file(
    call_id: str,
    commit_sha: str = Query(..., description="Commit SHA to filter log files")
):
    """
    Get the latest log file for a specific call_id and commit_sha.
    
    Args:
        call_id: Call identifier
        commit_sha: Commit SHA to filter log files
        
    Returns:
        Log file content and metadata
    """
    try:
        log_file_path = get_latest_log_file(call_id, commit_sha)
        
        if log_file_path is None or not log_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No log file found for call_id: {call_id}, commit_sha: {commit_sha}"
            )
        
        # Read log file content
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error reading log file: {str(e)}"
            )
        
        # Get file metadata
        file_stat = log_file_path.stat()
        last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        
        return LogFileResponse(
            call_id=call_id,
            commit_sha=commit_sha,
            log_file_path=str(log_file_path),
            log_content=log_content,
            file_size_bytes=file_stat.st_size,
            last_modified=last_modified
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving log file: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving log file: {str(e)}")


@app.get("/results/{call_id}", response_model=ResultResponse)
async def get_result(
    call_id: str,
    commit_sha: str = Query(..., description="Commit SHA to filter result files")
):
    """
    Get the result file for a specific call_id and commit_sha.
    
    Args:
        call_id: Call identifier
        commit_sha: Commit SHA to filter result files
        
    Returns:
        Result file content and metadata
    """
    try:
        import json
        
        # Construct result file path - only supports new format: call_{safe_call_id}_{safe_commit_sha}_{timestamp}.json
        # This matches the format used in tree_executor._save_results()
        results_dir = Path(__file__).parent / "results"
        
        # Sanitize call_id and commit_sha the same way as in _save_results
        safe_call_id = "".join(c for c in call_id if c.isalnum() or c in ("-", "_"))[:50]
        safe_commit_sha = "".join(c for c in commit_sha if c.isalnum())[:8]
        
        # Search for files matching the new format pattern: call_{call_id}_{commit_sha}_{timestamp}.json
        # Note: Only files with the new format (including timestamp) are supported
        pattern = f"call_{safe_call_id}_{safe_commit_sha}_*.json"
        matching_files = list(results_dir.glob(pattern))
        
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"No result file found for call_id: {call_id}, commit_sha: {commit_sha}"
            )
        
        # Sort by modification time (most recent first) and return the latest
        matching_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        result_file_path = matching_files[0]
        
        # Read result file content
        try:
            with open(result_file_path, "r", encoding="utf-8") as f:
                result_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON in result file {result_file_path}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing result file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error reading result file {result_file_path}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error reading result file: {str(e)}"
            )
        
        # Get file metadata
        file_stat = result_file_path.stat()
        last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        
        return ResultResponse(
            call_id=call_id,
            commit_sha=commit_sha,
            result_file_path=str(result_file_path),
            result=result_data,
            file_size_bytes=file_stat.st_size,
            last_modified=last_modified
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving result file: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving result file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

