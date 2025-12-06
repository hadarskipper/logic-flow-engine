"""Mock Speech-to-Text service."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def transcribe_audio(audio_file: Any) -> str:
    """
    Mock STT function that returns sample transcribed text.
    
    Args:
        audio_file: Audio file object (not actually processed in mock)
        
    Returns:
        Sample transcribed text string
    """
    logger.info("Mock STT: Transcribing audio file")
    
    # Mock transcription - in real implementation, this would process the audio
    sample_transcription = (
        "Hello, this is a sample healthcare call. "
        "The patient is experiencing some symptoms and may need a home visit. "
        "Please schedule a follow-up appointment. "
        "The patient's name is John Doe and their phone number is 555-1234."
    )
    
    return sample_transcription

