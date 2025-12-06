"""Test file for TreeExecutor.execute() method."""

import logging
from pathlib import Path
from datetime import datetime
from engine.tree_executor import TreeExecutor

# Configure logging to write to a file in logs directory
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Create log filename with timestamp
log_filename = f"test_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = log_dir / log_filename

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filepath, encoding='utf-8'),
        logging.StreamHandler(),  # Also output to console
    ],
)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured. Log file: {log_filepath}")


def test_tree_executor_execute():
    """Test TreeExecutor.execute() with mock data."""
    config_path = Path(__file__).parent / "config" / "decision_tree.yaml"
    tree_executor = TreeExecutor(str(config_path))
    
    # Prepare initial workflow data as specified
    initial_workflow_data = {
        "audio_file": b"",  # Empty audio content
        "call_id": "1",
        "filename": "testing_mock",
    }
    
    # Execute the decision tree
    result = tree_executor.execute(initial_workflow_data)
    
    # Assertions
    assert result is not None, "Result should not be None"
    assert "status" in result, "Result should contain 'status'"
    assert "execution_path" in result, "Result should contain 'execution_path'"
    assert "final_output" in result, "Result should contain 'final_output'"
    assert "processing_time_seconds" in result, "Result should contain 'processing_time_seconds'"
    
    # Check status
    assert result["status"] == "success", f"Status should be 'success', got '{result['status']}'"
    
    # Check execution path contains expected nodes
    execution_path = result["execution_path"]
    assert len(execution_path) > 0, "Execution path should not be empty"
    assert "node1" in execution_path, "Execution path should contain node1"
    assert "node2" in execution_path, "Execution path should contain node2"
    assert "node3" in execution_path, "Execution path should contain node3"
    assert "node4" in execution_path, "Execution path should contain node4"
    assert "node5" in execution_path, "Execution path should contain node5"
    assert "node8" in execution_path, "Execution path should contain node8"
    
    # Check that path starts with node1
    assert execution_path[0] == "node1", f"Path should start with node1, got '{execution_path[0]}'"
    
    # Check that path ends with node8
    assert execution_path[-1] == "node8", f"Path should end with node8, got '{execution_path[-1]}'"
    
    # Check final output contains expected keys
    final_output = result["final_output"]
    assert "call_id" in final_output, "Final output should contain 'call_id'"
    assert final_output["call_id"] == "1", f"call_id should be '1', got '{final_output['call_id']}'"
    assert "filename" in final_output, "Final output should contain 'filename'"
    assert final_output["filename"] == "testing_mock", f"filename should be 'testing_mock', got '{final_output['filename']}'"
    assert "call_metadata" in final_output, "Final output should contain 'call_metadata'"
    assert "transcribed_text" in final_output, "Final output should contain 'transcribed_text'"
    assert "deidentified_text" in final_output, "Final output should contain 'deidentified_text'"
    assert "home_visit_recommendation" in final_output, "Final output should contain 'home_visit_recommendation'"
    
    # Check processing time is a non-negative number
    assert result["processing_time_seconds"] >= 0, "Processing time should be non-negative"
    
    print(f"\n✓ All assertions passed!")
    print(f"Execution Path: {execution_path}")
    print(f"Status: {result['status']}")
    print(f"Processing Time: {result['processing_time_seconds']} seconds")
    print(f"Final Output Keys: {list(final_output.keys())}")
    
    return result


def test_tree_executor_execute_with_home_visit_yes():
    """Test execution path when home visit recommendation is 'yes'."""
    config_path = Path(__file__).parent / "config" / "decision_tree.yaml"
    tree_executor = TreeExecutor(str(config_path))
    
    initial_workflow_data = {
        "audio_file": b"test audio with home visit needed",
        "call_id": "1",
        "filename": "testing_mock",
    }
    
    result = tree_executor.execute(initial_workflow_data)
    
    execution_path = result["execution_path"]
    final_output = result["final_output"]
    
    # Should go through node6 (care plan) if home visit is yes
    # or node7 (sentiment) if home visit is no/unclear
    assert "node6" in execution_path or "node7" in execution_path, "Should go through node6 or node7"
    
    # Check that home_visit_recommendation exists
    assert "home_visit_recommendation" in final_output, "Should have home_visit_recommendation"
    
    # If home visit is yes, should have care_plan_updates
    # If no/unclear, should have sentiment
    if final_output.get("home_visit_recommendation") == "yes":
        assert "care_plan_updates" in final_output, "Should have care_plan_updates when home visit is yes"
        assert "node6" in execution_path, "Should go through node6 when home visit is yes"
    else:
        assert "sentiment" in final_output, "Should have sentiment when home visit is no/unclear"
        assert "node7" in execution_path, "Should go through node7 when home visit is no/unclear"
    
    print(f"\n✓ Conditional path test passed!")
    print(f"Home visit recommendation: {final_output.get('home_visit_recommendation')}")
    print(f"Execution Path: {execution_path}")


if __name__ == "__main__":
    print("="*60)
    print("Running TreeExecutor.execute() Tests")
    print("="*60)
    
    # Run the main test
    print("\n[Test 1] Basic execution test with empty audio content")
    print("-" * 60)
    try:
        result = test_tree_executor_execute()
        print("✓ Test 1 PASSED\n")
    except AssertionError as e:
        print(f"✗ Test 1 FAILED: {e}\n")
    except Exception as e:
        print(f"✗ Test 1 ERROR: {e}\n")
    
    # Run the conditional path test
    print("\n[Test 2] Conditional path test")
    print("-" * 60)
    try:
        test_tree_executor_execute_with_home_visit_yes()
        print("✓ Test 2 PASSED\n")
    except AssertionError as e:
        print(f"✗ Test 2 FAILED: {e}\n")
    except Exception as e:
        print(f"✗ Test 2 ERROR: {e}\n")
    
    print("="*60)
    print("All tests completed!")
    print("="*60)

