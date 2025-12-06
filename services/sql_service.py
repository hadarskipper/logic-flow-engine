"""Mock SQL database service."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Mock database - in-memory dictionary
MOCK_DATABASE: Dict[str, Dict[str, Any]] = {
    "call_123": {
        "call_id": "call_123",
        "call_type": "patient_followup",
        "calling_team": "nursing",
        "patient_id": "patient_456",
        "timestamp": "2024-01-15T10:30:00Z",
        "duration_seconds": 180,
    },
    "default": {
        "call_id": "default_call",
        "call_type": "general_inquiry",
        "calling_team": "support",
        "patient_id": "patient_000",
        "timestamp": "2024-01-15T10:00:00Z",
        "duration_seconds": 120,
    },
}


def get_call_metadata(call_id: str = "default") -> Dict[str, Any]:
    """
    Mock SQL function to retrieve call metadata.
    
    Args:
        call_id: Call identifier (optional, defaults to "default")
        
    Returns:
        Dictionary containing call metadata
    """
    logger.info(f"Mock SQL: Retrieving call metadata for {call_id}")
    
    # Return metadata from mock database
    metadata = MOCK_DATABASE.get(call_id, MOCK_DATABASE["default"])
    return metadata.copy()  # Return a copy to avoid mutation

