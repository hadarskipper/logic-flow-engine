"""Mock LLM service for various processing tasks."""

import logging

logger = logging.getLogger(__name__)


def process_llm_request(text: str, prompt: str) -> str:
    """
    Process LLM request with given text and prompt.
    
    Args:
        text: Input text to process
        prompt: Prompt to guide the LLM processing
        
    Returns:
        Processed result as string
    """
    logger.info(f"Processing LLM request with prompt: {prompt[:50]}...")
    
    # In a real implementation, this would send the prompt and text to an LLM API
    # For the mock, we use simple keyword-based logic based on the prompt content
    prompt_lower = prompt.lower()
    text_lower = text.lower()
    
    # Route based on prompt content
    if "home visit" in prompt_lower or "visit needed" in prompt_lower:
        # Determine if home visit is needed
        if any(keyword in text_lower for keyword in ["home visit", "house call", "visit home"]):
            return "yes"
        elif any(keyword in text_lower for keyword in ["no visit", "not needed", "unnecessary"]):
            return "no"
        else:
            return "unclear"
    
    elif "sentiment" in prompt_lower:
        # Extract sentiment
        positive_words = ["good", "great", "excellent", "thank", "appreciate", "helpful"]
        negative_words = ["bad", "terrible", "worried", "concerned", "problem", "issue"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    elif "care plan" in prompt_lower or "recommendations" in prompt_lower:
        # Generate care plan updates
        return (
            "Based on the call, recommend scheduling a home visit within 48 hours. "
            "Patient requires follow-up monitoring. Update medication schedule as discussed."
        )
    
    else:
        # Default: return a generic response
        logger.warning(f"Unknown prompt type, using default handler")
        return f"Processed text based on prompt: {prompt[:50]}..."

