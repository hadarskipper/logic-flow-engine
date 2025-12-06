"""Main decision tree execution engine."""

import logging
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urlparse

import yaml

from engine.node_handlers import get_node_handler

logger = logging.getLogger(__name__)


class TreeExecutor:
    """Executes decision tree workflows based on YAML configuration."""
    
    def __init__(self, tree_config_path: str, commit_sha: Optional[str] = None):
        """
        Initialize the tree executor with a YAML configuration file or GitHub URL.
        
        Args:
            tree_config_path: Path to the YAML decision tree configuration (local file or GitHub URL)
            commit_sha: Optional commit SHA for GitHub URLs (defaults to latest/main branch)
        """
        self.tree_config_path = tree_config_path
        self.commit_sha = commit_sha
        self.tree_config: Dict[str, Any] = {}
        self.load_tree_config()
    
    def _is_url(self, path: str) -> bool:
        """Check if the path is a URL."""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def load_tree_config(self) -> None:
        """Load and validate the decision tree configuration from YAML file or URL."""
        try:
            # Check if it's a URL
            if self._is_url(self.tree_config_path):
                # Use GitHub client for caching
                from github_client import get_github_config
                config = get_github_config(self.commit_sha)
            else:
                # Local file
                with open(self.tree_config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            
            self.tree_config = config.get("tree", {})
            
            # Validate tree structure
            if not self.tree_config.get("start_node"):
                raise ValueError("Tree configuration must have a start_node")
            
            if not self.tree_config.get("nodes"):
                raise ValueError("Tree configuration must have nodes")
            
            source_info = f"from GitHub (commit: {self.commit_sha or 'latest'})" if self._is_url(self.tree_config_path) else f"from file: {self.tree_config_path}"
            logger.info(f"Loaded tree configuration: {self.tree_config.get('name')} {source_info}")
        
        except FileNotFoundError:
            logger.error(f"Tree configuration file not found: {self.tree_config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading tree configuration: {e}")
            raise
    
    def execute(self, initial_workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the decision tree with the given initial workflow data.
        
        Args:
            initial_workflow_data: Initial workflow data dictionary (e.g., audio_file, call_id)
            
        Returns:
            Dictionary containing execution results
        """
        start_time = time.time()
        workflow_data = initial_workflow_data.copy()
        execution_path: List[str] = []
        nodes = self.tree_config.get("nodes", {})
        current_node_id = self.tree_config.get("start_node")
        
        logger.info(f"Starting tree execution from node: {current_node_id}")
        
        # Execute nodes until we hit an exit node
        while current_node_id:
            if current_node_id not in nodes:
                raise ValueError(f"Node '{current_node_id}' not found in tree configuration")
            
            node_config = nodes[current_node_id]
            node_type = node_config.get("type")
            
            logger.info(f"Executing node: {current_node_id} (type: {node_type})")
            
            # Get handler for this node type
            handler = get_node_handler(node_type)
            
            # Execute the node and get next node ID
            workflow_data, next_node_id = handler(node_config, workflow_data)
            
            # Track execution path
            execution_path.append(current_node_id)
            
            # Check for exit condition
            if workflow_data.get("_exit"):
                logger.info(f"Reached exit node. Status: {workflow_data.get('_exit_status')}")
                break
            
            # Move to next node (handler returns None for exit nodes)
            current_node_id = next_node_id
        
        processing_time = time.time() - start_time
        
        # Prepare final output
        final_output = self._prepare_final_output(workflow_data)
        
        return {
            "status": workflow_data.get("_exit_status", "success"),
            "execution_path": execution_path,
            "final_output": final_output,
            "processing_time_seconds": round(processing_time, 2),
        }
    
    def _prepare_final_output(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the final output by filtering out internal keys.
        
        Args:
            workflow_data: Workflow data dictionary
            
        Returns:
            Cleaned output dictionary
        """
        # Remove internal keys (starting with _)
        output = {
            k: v for k, v in workflow_data.items() if not k.startswith("_")
        }
        return output
    
    def get_tree_structure(self) -> Dict[str, Any]:
        """
        Get the current tree structure.
        
        Returns:
            Dictionary containing tree structure information
        """
        return {
            "tree_name": self.tree_config.get("name", "Unknown"),
            "start_node": self.tree_config.get("start_node"),
            "nodes": self.tree_config.get("nodes", {}),
        }

