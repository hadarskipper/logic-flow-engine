"""Handlers for different node types in the decision tree."""

import logging
from typing import Any, Dict, Optional, Tuple

from services import stt_service, llm_service, sql_service, deidentify_service

logger = logging.getLogger(__name__)


def handle_stt_node(node_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle STT (Speech-to-Text) node type.
    
    Args:
        node_config: Node configuration from YAML (contains node_config dict)
        workflow_data: Current workflow data
        
    Returns:
        Tuple of (updated workflow data dictionary, next node ID)
    """
    config = node_config.get("node_config", {})
    input_key = config.get("input_key")
    output_key = config.get("output_key")
    
    logger.info(f"STT node: {node_config.get('name')}")
    
    if input_key != "audio_file":
        raise ValueError(f"STT node requires 'audio_file' as input_key, got '{input_key}'")
    
    if input_key not in workflow_data:
        raise ValueError(f"STT node requires '{input_key}' in workflow_data")
    
    input_value = workflow_data.get(input_key)
    
    result = stt_service.transcribe_audio(input_value)
    
    if output_key:
        workflow_data[output_key] = result
    
    next_node = node_config.get("next_node")
    return workflow_data, next_node


def handle_sql_node(node_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle SQL node type.
    
    Args:
        node_config: Node configuration from YAML (contains node_config dict)
        workflow_data: Current workflow data
        
    Returns:
        Tuple of (updated workflow data dictionary, next node ID)
    """
    config = node_config.get("node_config", {})
    output_key = config.get("output_key")
    
    logger.info(f"SQL node: {node_config.get('name')}")
    
    call_id = workflow_data.get("call_id", "default")
    result = sql_service.get_call_metadata(call_id)
    
    if output_key:
        workflow_data[output_key] = result
    
    next_node = node_config.get("next_node")
    return workflow_data, next_node


def handle_deidentify_node(node_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle de-identification node type.
    
    Args:
        node_config: Node configuration from YAML (contains node_config dict)
        workflow_data: Current workflow data
        
    Returns:
        Tuple of (updated workflow data dictionary, next node ID)
    """
    config = node_config.get("node_config", {})
    input_key = config.get("input_key")
    output_key = config.get("output_key")
    
    logger.info(f"De-identify node: {node_config.get('name')}")
    
    input_value = workflow_data.get(input_key)
    if not input_value:
        raise ValueError(f"De-identify node requires '{input_key}' in workflow_data")
    
    result = deidentify_service.deidentify_text(input_value)
    
    if output_key:
        workflow_data[output_key] = result
    
    next_node = node_config.get("next_node")
    return workflow_data, next_node


def handle_llm_node(node_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle LLM node type.
    
    Args:
        node_config: Node configuration from YAML (contains prompt and node_config dict)
        workflow_data: Current workflow data
        
    Returns:
        Tuple of (updated workflow data dictionary, next node ID)
    """
    config = node_config.get("node_config", {})
    prompt = config.get("prompt")
    input_key = config.get("input_key")
    output_key = config.get("output_key")
    
    logger.info(f"LLM node: {node_config.get('name')}")
    
    if not prompt:
        raise ValueError(f"LLM node requires 'prompt' field in node_config")
    
    input_value = workflow_data.get(input_key)
    if not input_value:
        raise ValueError(f"LLM node requires '{input_key}' in workflow_data")
    
    result = llm_service.process_llm_request(input_value, prompt)
    
    if output_key:
        workflow_data[output_key] = result
    
    next_node = node_config.get("next_node")
    return workflow_data, next_node


def handle_condition_node(node_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle condition node type for branching logic.
    
    Args:
        node_config: Node configuration from YAML (contains node_config dict)
        workflow_data: Current workflow data
        
    Returns:
        Tuple of (updated workflow data dictionary, next node ID)
    """
    config = node_config.get("node_config", {})
    condition_key = config.get("condition_key")
    condition_value = config.get("condition_value")
    true_node = config.get("true_node")
    false_node = config.get("false_node")
    
    logger.info(f"Condition node: {node_config.get('name')} - Checking {condition_key} == {condition_value}")
    
    # Get value from workflow data
    actual_value = workflow_data.get(condition_key)
    
    # Determine next node based on condition
    if actual_value == condition_value:
        next_node = true_node
        logger.info(f"Condition TRUE - Next node: {true_node}")
    else:
        next_node = false_node
        logger.info(f"Condition FALSE - Next node: {false_node}")
    
    return workflow_data, next_node


def handle_exit_node(node_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle exit node type.
    
    Args:
        node_config: Node configuration from YAML (contains node_config dict)
        workflow_data: Current workflow data
        
    Returns:
        Tuple of (updated workflow data dictionary, None to indicate exit)
    """
    config = node_config.get("node_config", {})
    status = config.get("status", "success")
    
    logger.info(f"Exit node: {node_config.get('name')} - Status: {status}")
    
    workflow_data["_exit"] = True
    workflow_data["_exit_status"] = status
    
    return workflow_data, None


def get_node_handler(node_type: str):
    """
    Get the appropriate handler function for a node type.
    
    Args:
        node_type: Type of node (stt, sql, deidentify, llm, condition, exit)
        
    Returns:
        Handler function
    """
    handlers = {
        "stt": handle_stt_node,
        "sql": handle_sql_node,
        "deidentify": handle_deidentify_node,
        "llm": handle_llm_node,
        "condition": handle_condition_node,
        "exit": handle_exit_node,
    }
    
    handler = handlers.get(node_type)
    if not handler:
        raise ValueError(f"Unknown node type: {node_type}")
    
    return handler

