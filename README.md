# Decision Tree Call Processing API

A Python FastAPI project that processes healthcare call audio files using a YAML-based decision tree workflow.

## Overview

This API accepts MP3 audio files and processes them through a configurable decision tree workflow defined in YAML. The workflow includes steps for speech-to-text conversion, de-identification, LLM-based analysis, and conditional branching logic.

## Features

- **YAML-based Decision Tree**: Configure workflows using simple YAML files
- **Multiple Node Types**: Support for processing, LLM processing, condition, and exit nodes
- **Mock Services**: Includes mock implementations for STT, LLM, SQL, and de-identification services
- **Execution Tracking**: Tracks execution path and intermediate results
- **Clean Architecture**: Modular design for easy service replacement

## Project Structure

```
project/
├── main.py                 # FastAPI app entry point
├── config/
│   └── decision_tree.yaml  # The YAML configuration
├── engine/
│   ├── __init__.py
│   ├── tree_executor.py    # Main decision tree execution logic
│   └── node_handlers.py    # Handlers for different node types
├── services/
│   ├── __init__.py
│   ├── stt_service.py      # Mock STT service
│   ├── llm_service.py      # Mock LLM service
│   ├── sql_service.py      # Mock SQL service
│   └── deidentify_service.py  # Mock de-identification
├── models/
│   ├── __init__.py
│   └── schemas.py          # Pydantic models for API
├── requirements.txt
└── README.md
```

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server

Run the FastAPI application:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

#### 2. Get Tree Structure
```bash
GET /tree-structure
```

Returns the current decision tree configuration.

**Response:**
```json
{
  "tree_name": "Healthcare Call Processing",
  "start_node": "node1",
  "nodes": { ... }
}
```

#### 3. Process Call
```bash
POST /process-call
```

Processes an MP3 audio file through the decision tree workflow.

**Parameters:**
- `audio_file` (file): MP3 audio file (multipart form data)
- `call_id` (query parameter, optional): Call identifier for metadata lookup (default: "default")

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/process-call?call_id=call_123" \
  -F "audio_file=@sample_call.mp3"
```

**Response:**
```json
{
  "status": "success",
  "execution_path": ["node1", "node2", "node3", "node4", "node5", "node6", "node8"],
  "final_output": {
    "call_id": "call_123",
    "filename": "sample_call.mp3",
    "call_metadata": { ... },
    "transcribed_text": "...",
    "deidentified_text": "...",
    "home_visit_recommendation": "yes",
    "care_plan_updates": "..."
  },
  "processing_time_seconds": 0.15
}
```

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Decision Tree Configuration

The decision tree is configured in `config/decision_tree.yaml`. The structure includes:

- **start_node**: The entry point of the workflow
- **nodes**: Dictionary of node configurations

### Node Types

1. **processing**: Executes a service action (STT, SQL, de-identification)
2. **llm_processing**: Executes LLM-based processing
3. **condition**: Conditional branching based on context values
4. **exit**: Terminates the workflow

### Example Node Configuration

```yaml
node1:
  type: "processing"
  name: "Load Call Metadata"
  service: "sql"
  action: "get_call_metadata"
  output_key: "call_metadata"
  next_node: "node2"
```

## Mock Services

All services are currently implemented as mocks:

- **STT Service**: Returns sample transcribed text
- **LLM Service**: Provides keyword-based responses for home visit checks, sentiment analysis, and care plan generation
- **SQL Service**: Returns mock call metadata from an in-memory dictionary
- **De-identification Service**: Uses regex patterns to replace PII-like content

### Replacing Mock Services

To replace mock services with real implementations:

1. Update the service functions in the `services/` directory
2. Maintain the same function signatures
3. The tree executor will automatically use the new implementations

## Development

### Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Add docstrings to all functions and classes
- Keep functions focused and under ~30 lines

### Testing

The code is structured to be easily testable. Mock services can be swapped out for test doubles during unit testing.

### Logging

The application uses Python's logging module. Logs are output to the console with INFO level by default.

## Future Enhancements

- Add real STT integration (e.g., Google Cloud Speech-to-Text, AWS Transcribe)
- Integrate with actual LLM APIs (OpenAI, Anthropic, etc.)
- Connect to real SQL database
- Implement proper NER-based de-identification
- Add authentication and authorization
- Implement request validation and rate limiting
- Add comprehensive test suite

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
