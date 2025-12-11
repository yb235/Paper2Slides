# API Reference

This document describes the RESTful API provided by Paper2Slides for web interface and programmatic access.

## 🌐 API Overview

**Base URL**: `http://localhost:8001` (default)

**Framework**: FastAPI with automatic OpenAPI documentation

**Interactive Docs**: `http://localhost:8001/docs` (Swagger UI)

## 🚀 Starting the API Server

### Method 1: Using Scripts

```bash
# Start both backend and frontend
./scripts/start.sh

# Or start backend only
./scripts/start_backend.sh [port]
```

### Method 2: Direct Python

```bash
cd api
python server.py [port]  # Default port: 8001
```

### Method 3: Production (Uvicorn)

```bash
cd api
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📡 Core Endpoints

### Health Check

#### GET `/`
Basic server status check.

**Response**:
```json
{
  "message": "Paper2Slides API Server",
  "status": "running"
}
```

#### GET `/health`
Detailed health check.

**Response**:
```json
{
  "status": "healthy"
}
```

---

### Session Management

Paper2Slides allows only one generation task at a time to manage resources effectively.

#### GET `/api/session/running`
Check if a session is currently running.

**Response**:
```json
{
  "has_running_session": true,
  "running_session_id": "abc12345"  // First 8 chars of session ID
}
```

#### POST `/api/cancel/{session_id}`
Cancel a running session.

**Parameters**:
- `session_id` (path): Full session ID to cancel

**Response**:
```json
{
  "message": "Session abc12345 cancellation requested",
  "cancelled": true
}
```

**Error Response** (if not running):
```json
{
  "message": "Session abc12345 is not running",
  "cancelled": false
}
```

---

### Main Generation Endpoint

#### POST `/api/chat`
Main endpoint for generating slides/posters from uploaded documents.

**Content-Type**: `multipart/form-data`

**Form Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | string | No | "" | Additional instructions or context |
| `content` | string | No | "paper" | Content type: "paper" or "general" |
| `output_type` | string | No | "slides" | Output type: "slides" or "poster" |
| `style` | string | No | "doraemon" | Style: "academic", "doraemon", or custom |
| `length` | string | No | "short" | Slides length: "short", "medium", "long" |
| `density` | string | No | "medium" | Poster density: "sparse", "medium", "dense" |
| `fast` | boolean | No | false | Use fast mode (skip RAG indexing) |
| `parallel` | integer | No | 1 | Number of parallel workers for generation |
| `from_stage` | string | No | null | Force restart from: "rag", "summary", "plan", "generate" |
| `files` | file[] | Yes | - | Uploaded document file(s) |

**Request Example** (using curl):

```bash
curl -X POST "http://localhost:8001/api/chat" \
  -F "files=@paper.pdf" \
  -F "output_type=slides" \
  -F "style=academic" \
  -F "length=medium" \
  -F "fast=false" \
  -F "parallel=2"
```

**Request Example** (using JavaScript/Axios):

```javascript
const formData = new FormData();
formData.append('files', fileObject);
formData.append('output_type', 'slides');
formData.append('style', 'doraemon');
formData.append('length', 'medium');
formData.append('parallel', '2');

const response = await axios.post('http://localhost:8001/api/chat', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  }
});
```

**Success Response** (200 OK):

```json
{
  "message": "Processing completed successfully! Generated 8 slides.",
  "slides": [
    {
      "id": "slide_01",
      "url": "/outputs/paper/paper/normal/slides_academic_medium/20241210_123456/slide_01.png",
      "title": "Title Slide"
    },
    {
      "id": "slide_02",
      "url": "/outputs/paper/paper/normal/slides_academic_medium/20241210_123456/slide_02.png",
      "title": "Introduction"
    },
    // ... more slides
  ],
  "ppt_url": "/outputs/paper/paper/normal/slides_academic_medium/20241210_123456/slides.pdf",
  "poster_url": null,
  "session_id": "abc12345-6789-def0-1234-56789abcdef0",
  "uploaded_files": [
    {
      "filename": "paper.pdf",
      "size": 1234567,
      "url": "/uploads/paper_abc123.pdf"
    }
  ]
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Success or error message |
| `slides` | array | List of generated slide objects (if output_type="slides") |
| `ppt_url` | string | URL to PDF file (if output_type="slides") |
| `poster_url` | string | URL to poster image (if output_type="poster") |
| `session_id` | string | Unique session identifier |
| `uploaded_files` | array | Information about uploaded files |

**Slide Object**:
```json
{
  "id": "slide_01",
  "url": "/outputs/.../slide_01.png",
  "title": "Title from plan"
}
```

**Uploaded File Object**:
```json
{
  "filename": "original_name.pdf",
  "size": 1234567,
  "url": "/uploads/saved_name.pdf"
}
```

**Error Responses**:

**409 Conflict** (another session running):
```json
{
  "detail": "Another session is already running. Please wait or cancel it."
}
```

**400 Bad Request** (no files uploaded):
```json
{
  "detail": "No files uploaded"
}
```

**500 Internal Server Error** (processing failed):
```json
{
  "detail": "Pipeline error: [error message]"
}
```

---

### Progress Tracking

The API uses a state file system for progress tracking. Clients can poll the state file or implement WebSocket for real-time updates.

#### Polling State File

**State File Path**:
```
outputs/<project>/<content_type>/<mode>/<config>/state.json
```

**State Structure**:
```json
{
  "session_id": "abc12345-6789-def0-1234-56789abcdef0",
  "config": {
    "output_type": "slides",
    "style": "academic",
    "slides_length": "medium"
  },
  "stages": {
    "rag": "completed",
    "summary": "completed",
    "plan": "running",
    "generate": "pending"
  },
  "error": null,
  "created_at": "2024-12-10T12:34:56",
  "updated_at": "2024-12-10T12:35:30"
}
```

**Stage Status Values**:
- `pending`: Not started yet
- `running`: Currently executing
- `completed`: Successfully finished
- `failed`: Error occurred
- `cancelled`: User cancelled

**Example Polling** (JavaScript):

```javascript
async function pollProgress(stateFilePath) {
  const interval = 2000; // Poll every 2 seconds
  
  while (true) {
    try {
      const response = await fetch(stateFilePath);
      const state = await response.json();
      
      // Update UI with progress
      updateProgressBar(state.stages);
      
      // Check if complete
      if (state.stages.generate === 'completed') {
        return { success: true, state };
      }
      
      // Check if failed
      if (Object.values(state.stages).includes('failed')) {
        return { success: false, error: state.error };
      }
      
      // Check if cancelled
      if (Object.values(state.stages).includes('cancelled')) {
        return { success: false, error: 'Cancelled by user' };
      }
      
      await sleep(interval);
    } catch (error) {
      console.error('Polling error:', error);
      await sleep(interval);
    }
  }
}
```

---

## 🖼️ Static File Serving

The API serves static files from two directories:

### Generated Outputs

**Mount Point**: `/outputs`

**Directory**: `<project_root>/outputs/`

**Example URLs**:
```
http://localhost:8001/outputs/paper/paper/normal/slides_doraemon_medium/20241210_123456/slide_01.png
http://localhost:8001/outputs/paper/paper/normal/slides_doraemon_medium/20241210_123456/slides.pdf
```

### Uploaded Files

**Mount Point**: `/uploads`

**Directory**: `<project_root>/sources/uploads/`

**Example URLs**:
```
http://localhost:8001/uploads/paper_abc123.pdf
http://localhost:8001/uploads/report_def456.docx
```

---

## 🔐 CORS Configuration

The API is configured to allow requests from:
- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

**For Production**: Update CORS settings in `api/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔄 Background Task Processing

The `/api/chat` endpoint uses FastAPI's `BackgroundTasks` to process requests asynchronously:

```python
@app.post("/api/chat")
async def chat(background_tasks: BackgroundTasks, ...):
    # Save files immediately
    # Start processing in background
    background_tasks.add_task(process_pipeline, ...)
    # Return immediately with session info
    return response
```

This ensures:
- Quick response to client
- Non-blocking API
- Long-running tasks don't timeout
- Client can track progress via state files

---

## 📊 Session Manager

The API uses a global `SessionManager` to coordinate concurrent requests:

```python
class SessionManager:
    def __init__(self):
        self.running_session = None
        self.cancelled_sessions = set()
        self.lock = asyncio.Lock()
    
    async def start_session(self, session_id: str) -> bool:
        """Returns False if another session is running"""
        
    async def end_session(self, session_id: str):
        """Mark session as complete"""
        
    async def cancel_session(self, session_id: str) -> bool:
        """Request cancellation"""
        
    def is_cancelled(self, session_id: str) -> bool:
        """Check if cancelled"""
```

**Usage Flow**:

```python
session_id = str(uuid.uuid4())

# Try to start
if not await session_manager.start_session(session_id):
    raise HTTPException(409, "Another session running")

try:
    # Run pipeline with cancellation support
    await run_pipeline(
        ...,
        session_id=session_id,
        session_manager=session_manager
    )
finally:
    # Always cleanup
    await session_manager.end_session(session_id)
```

**Pipeline Cancellation Check**:

```python
async def run_pipeline(..., session_id, session_manager):
    for stage in STAGES:
        # Check before each stage
        if session_manager and session_manager.is_cancelled(session_id):
            raise Exception("Cancelled by user")
        
        # Execute stage
        await run_stage(...)
```

---

## 🧪 API Testing Examples

### Using cURL

**Generate Slides (Fast Mode)**:
```bash
curl -X POST "http://localhost:8001/api/chat" \
  -F "files=@paper.pdf" \
  -F "output_type=slides" \
  -F "style=doraemon" \
  -F "length=short" \
  -F "fast=true"
```

**Generate Poster (Normal Mode)**:
```bash
curl -X POST "http://localhost:8001/api/chat" \
  -F "files=@paper.pdf" \
  -F "output_type=poster" \
  -F "style=academic" \
  -F "density=medium"
```

**Custom Style**:
```bash
curl -X POST "http://localhost:8001/api/chat" \
  -F "files=@report.pdf" \
  -F "output_type=slides" \
  -F "style=modern minimalist with blue and white theme" \
  -F "length=medium"
```

### Using Python Requests

```python
import requests
import time

# Upload and start processing
files = {'files': open('paper.pdf', 'rb')}
data = {
    'output_type': 'slides',
    'style': 'academic',
    'length': 'medium',
    'parallel': '2'
}

response = requests.post('http://localhost:8001/api/chat', files=files, data=data)
result = response.json()

print(f"Session ID: {result['session_id']}")
print(f"Message: {result['message']}")

# Poll for progress
if result.get('slides'):
    print(f"Generated {len(result['slides'])} slides")
    for slide in result['slides']:
        print(f"  - {slide['title']}: {slide['url']}")
```

### Using JavaScript/Fetch

```javascript
// Upload files
const fileInput = document.querySelector('input[type="file"]');
const formData = new FormData();

for (const file of fileInput.files) {
  formData.append('files', file);
}

formData.append('output_type', 'slides');
formData.append('style', 'doraemon');
formData.append('length', 'medium');

// Start processing
const response = await fetch('http://localhost:8001/api/chat', {
  method: 'POST',
  body: formData
});

const result = await response.json();

if (response.ok) {
  console.log('Success:', result.message);
  console.log('Slides:', result.slides);
  console.log('PDF:', result.ppt_url);
} else {
  console.error('Error:', result.detail);
}
```

---

## 📁 Directory Structure

Understanding the API's directory layout:

```
project_root/
├── api/
│   └── server.py           # FastAPI application
├── sources/
│   └── uploads/            # Uploaded files stored here
└── outputs/                # Generated outputs stored here
    └── <project>/
        └── <content_type>/
            └── <mode>/
                └── <config>/
                    └── <timestamp>/
                        ├── slide_01.png
                        ├── slides.pdf
                        └── ...
```

---

## 🛡️ Security Considerations

### File Upload Security

1. **File Validation**:
   - Type checking (PDF, DOCX, etc.)
   - Size limits (configure in server)
   - Filename sanitization

2. **Storage**:
   - Unique filenames (UUID-based)
   - Isolated upload directory
   - Regular cleanup of old files

3. **Access Control**:
   - Static file serving with proper MIME types
   - No directory listing
   - CORS restrictions

### API Key Management

API keys are stored in `.env` file and loaded as environment variables:

```bash
# paper2slides/.env
RAG_LLM_API_KEY=your_openai_key
RAG_LLM_BASE_URL=https://api.openai.com/v1

IMAGE_GEN_API_KEY=your_openrouter_key
IMAGE_GEN_BASE_URL=https://openrouter.ai/api/v1
```

**Never expose these in API responses!**

---

## 🚀 Production Deployment

### Using Docker (Recommended)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### Using Systemd

```ini
[Unit]
Description=Paper2Slides API
After=network.target

[Service]
Type=simple
User=paper2slides
WorkingDirectory=/opt/paper2slides
Environment="PATH=/opt/paper2slides/venv/bin"
ExecStart=/opt/paper2slides/venv/bin/uvicorn api.server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Behind Nginx

```nginx
server {
    listen 80;
    server_name paper2slides.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Long timeout for processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

---

## 📚 API Client Libraries

### Python Client Example

```python
class Paper2SlidesClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    def generate_slides(self, file_path, **kwargs):
        """Generate slides from a document."""
        with open(file_path, 'rb') as f:
            files = {'files': f}
            data = {
                'output_type': kwargs.get('output_type', 'slides'),
                'style': kwargs.get('style', 'doraemon'),
                'length': kwargs.get('length', 'medium'),
                'parallel': kwargs.get('parallel', 2)
            }
            response = requests.post(
                f"{self.base_url}/api/chat",
                files=files,
                data=data
            )
            return response.json()
    
    def get_running_session(self):
        """Check if any session is running."""
        response = requests.get(f"{self.base_url}/api/session/running")
        return response.json()
    
    def cancel_session(self, session_id):
        """Cancel a running session."""
        response = requests.post(f"{self.base_url}/api/cancel/{session_id}")
        return response.json()

# Usage
client = Paper2SlidesClient()
result = client.generate_slides('paper.pdf', style='academic', length='long')
print(result)
```

---

## 🐛 Debugging Tips

1. **Enable Debug Logging**:
   ```python
   # In server.py
   setup_logging(level=logging.DEBUG)
   ```

2. **Check Logs**:
   ```bash
   tail -f logs/backend.log
   ```

3. **Test Endpoints**:
   - Visit `http://localhost:8001/docs` for interactive API docs
   - Use curl/Postman for manual testing

4. **Common Issues**:
   - Port already in use: Change port or kill process
   - CORS errors: Update allowed origins
   - File upload fails: Check file size limits
   - Processing timeout: Increase proxy timeouts

---

## 📖 Next Steps

- **[CLI Usage](./05-cli-usage.md)**: Learn command-line interface
- **[Configuration](./08-configuration.md)**: Environment setup and options
- **[Troubleshooting](./10-troubleshooting.md)**: Common problems and solutions
