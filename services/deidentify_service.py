"""Mock de-identification service."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def deidentify_text(text: str) -> str:
    """
    Mock de-identification function that replaces PII-like patterns.
    
    Args:
        text: Input text containing potential PII
        
    Returns:
        Text with PII replaced by [REDACTED]
    """
    logger.info("Mock De-identify: Processing text for PII")
    
    # Simple pattern matching for common PII patterns
    # Phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED]', text)
    
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', text)
    
    # Common name patterns (simple heuristic - in production, use NER)
    # This is a very basic mock - real implementation would use NER models
    common_names = ["John Doe", "Jane Smith", "John", "Jane"]
    for name in common_names:
        text = text.replace(name, "[REDACTED]")
    
    # SSN patterns
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED]', text)
    
    return text

