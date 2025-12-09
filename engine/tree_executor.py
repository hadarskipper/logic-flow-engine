"""Main decision tree execution engine."""

import json
import logging
import time
from datetime import datetime
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
            commit_sha: Commit SHA for GitHub URLs (required)
            
        Raises:
            ValueError: If commit_sha is not provided
        """
        if commit_sha is None:
            raise ValueError("commit_sha is required")
        
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
            
        Raises:
            ValueError: If call_id is not provided in initial_workflow_data
        """
        if "call_id" not in initial_workflow_data or not initial_workflow_data.get("call_id"):
            raise ValueError("call_id is required in initial_workflow_data")
        
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
        
        result = {
            "status": workflow_data.get("_exit_status", "success"),
            "execution_path": execution_path,
            "final_output": final_output,
            "processing_time_seconds": round(processing_time, 2),
        }
        
        # Save results to file
        self._save_results(result, workflow_data, self.commit_sha)
        
        return result
    
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
    
    def _save_results(self, result: Dict[str, Any], workflow_data: Dict[str, Any], commit_sha: str) -> None:
        """
        Save execution results to a results directory.
        
        Args:
            result: Execution result dictionary
            workflow_data: Workflow data dictionary containing call_id and job_submission_datetime
            commit_sha: Commit SHA for filename
            
        Raises:
            ValueError: If call_id, commit_sha, or job_submission_datetime is not provided
        """
        
        call_id = workflow_data.get("call_id")
        if not call_id:
            raise ValueError("call_id is required in workflow_data to save results")
        
        if not commit_sha:
            raise ValueError("commit_sha is required to save results")
        
        # Get job_submission_datetime from workflow_data (stored as ISO format string)
        job_submission_datetime_str = workflow_data.get("job_submission_datetime")
        if not job_submission_datetime_str:
            raise ValueError("job_submission_datetime is required in workflow_data to save results")
        
        # Parse ISO format string back to datetime
        try:
            job_submission_datetime = datetime.fromisoformat(job_submission_datetime_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid job_submission_datetime format in workflow_data: {e}")
        
        logger.info("Starting _save_results")
        
        # Create results directory
        results_dir = Path(__file__).parent.parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Use same filename format as log files: call_{safe_call_id}_{safe_commit_sha}_{timestamp}.json
        timestamp = job_submission_datetime.strftime("%Y%m%d_%H%M%S")
        # Sanitize call_id for filename (remove invalid characters)
        safe_call_id = "".join(c for c in call_id if c.isalnum() or c in ("-", "_"))[:50]
        # Sanitize commit_sha for filename (use first 8 characters, remove invalid characters)
        safe_commit_sha = "".join(c for c in commit_sha if c.isalnum())[:8]
        filename = f"call_{safe_call_id}_{safe_commit_sha}_{timestamp}.json"
        result_filepath = results_dir / filename
        
        # Safely log result keys (convert to strings to avoid serialization issues)
        try:
            result_keys = [str(k) for k in result.keys()]
            logger.info(f"Result keys before processing: {result_keys}")
        except Exception as e:
            logger.warning(f"Could not log result keys: {e}")
        
        # Create a copy of result and remove bytes objects (like audio_file) for JSON serialization
        result_to_save = result.copy()
        logger.info("Created copy of result")
        
        if "final_output" in result_to_save:
            logger.info("Processing final_output")
            final_output = result_to_save["final_output"].copy()
            
            # Safely log final output keys
            try:
                final_output_keys = [str(k) for k in final_output.keys()]
                logger.info(f"Final output keys: {final_output_keys}")
            except Exception as e:
                logger.warning(f"Could not log final output keys: {e}")
            
            # Remove all bytes objects, not just audio_file
            removed_keys = []
            for key, value in list(final_output.items()):
                if isinstance(value, bytes):
                    try:
                        logger.warning(f"Removing bytes object from final_output.{key} (size: {len(value)} bytes)")
                    except Exception:
                        logger.warning(f"Removing bytes object from final_output.{key}")
                    removed_keys.append(str(key))
                    del final_output[key]
            
            if removed_keys:
                logger.info(f"Removed {len(removed_keys)} bytes field(s): {removed_keys}")
            
            result_to_save["final_output"] = final_output
            
            # Safely log final output keys after cleaning
            try:
                final_output_keys_after = [str(k) for k in final_output.keys()]
                logger.info(f"Final output keys after cleaning: {final_output_keys_after}")
            except Exception as e:
                logger.warning(f"Could not log final output keys after cleaning: {e}")
        
        # Safely log result keys to save
        try:
            result_keys_to_save = [str(k) for k in result_to_save.keys()]
            logger.info(f"Result keys to save: {result_keys_to_save}")
        except Exception as e:
            logger.warning(f"Could not log result keys to save: {e}")
        
        # Save result as JSON
        try:
            logger.info("Attempting to save results to JSON")
            with open(result_filepath, "w", encoding="utf-8") as f:
                json.dump(result_to_save, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {result_filepath}")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to save results: {e}")
            # Find which field is causing the issue
            for key, value in result_to_save.items():
                try:
                    json.dumps({key: value})
                except (TypeError, ValueError) as field_error:
                    logger.error(f"Problematic field: '{key}' (type: {type(value).__name__}) - {field_error}")
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            try:
                                json.dumps({sub_key: sub_value})
                            except (TypeError, ValueError) as sub_error:
                                logger.error(f"Problematic nested field: '{key}.{sub_key}' (type: {type(sub_value).__name__}) - {sub_error}")
            raise
    
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

