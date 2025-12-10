# Configuration

Complete guide to setting up and configuring Paper2Slides.

## 🔧 Environment Setup

### 1. System Requirements

**Operating System**:
- Linux (Ubuntu 20.04+, Debian 11+, etc.)
- macOS (10.15+)
- Windows (via WSL2 recommended)

**Python**:
- Python 3.12 or higher
- pip (latest version)

**Memory**:
- Minimum: 4 GB RAM
- Recommended: 8 GB+ RAM

**Disk Space**:
- Installation: ~2 GB
- Per document: ~50-200 MB (including checkpoints and outputs)

**GPU** (Optional):
- Not required (all processing uses cloud APIs)
- Can help with local embedding models if used

### 2. Installation

#### Using Conda (Recommended)

```bash
# Clone repository
git clone https://github.com/HKUDS/Paper2Slides.git
cd Paper2Slides

# Create conda environment
conda create -n paper2slides python=3.12 -y
conda activate paper2slides

# Install dependencies
pip install -r requirements.txt
```

#### Using venv

```bash
# Clone repository
git clone https://github.com/HKUDS/Paper2Slides.git
cd Paper2Slides

# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. API Keys Configuration

Paper2Slides requires API keys for LLM services.

#### Create .env File

```bash
# Copy example file
cp paper2slides/.env.example paper2slides/.env

# Edit with your API keys
nano paper2slides/.env
```

#### Required Keys

**For OpenAI (RAG and content extraction)**:
```bash
RAG_LLM_API_KEY=sk-...your-openai-api-key...
RAG_LLM_BASE_URL=https://api.openai.com/v1
```

**For OpenRouter (image generation)**:
```bash
IMAGE_GEN_API_KEY=sk-or-...your-openrouter-key...
IMAGE_GEN_BASE_URL=https://openrouter.ai/api/v1
```

#### Getting API Keys

**OpenAI**:
1. Go to https://platform.openai.com/
2. Sign in or create account
3. Navigate to API Keys section
4. Create new secret key
5. Copy and save the key

**OpenRouter**:
1. Go to https://openrouter.ai/
2. Sign in or create account
3. Navigate to Keys section
4. Create API key
5. Copy and save the key

### 4. Verify Installation

```bash
# Test imports
python -c "import paper2slides; print('Installation successful!')"

# Check CLI
python -m paper2slides --help

# Verify API keys (if configured)
python -c "import os; from dotenv import load_dotenv; load_dotenv('paper2slides/.env'); print('RAG_LLM_API_KEY:', 'SET' if os.getenv('RAG_LLM_API_KEY') else 'NOT SET')"
```

## ⚙️ Configuration Options

### CLI Configuration

All configuration is done via command-line arguments. See [CLI Usage](./05-cli-usage.md) for complete reference.

**Quick Reference**:
```bash
python -m paper2slides \
  --input paper.pdf \           # Required: input file/directory
  --output slides \              # slides or poster
  --content paper \              # paper or general
  --style doraemon \             # academic, doraemon, or custom
  --length medium \              # short, medium, long (for slides)
  --density medium \             # sparse, medium, dense (for poster)
  --fast \                       # Enable fast mode
  --parallel 2 \                 # Number of parallel workers
  --output-dir ./outputs \       # Output directory
  --from-stage rag \             # Force restart stage
  --debug                        # Debug logging
```

### API Configuration

The API server has minimal configuration. Most settings are passed per request.

#### Server Configuration

**In `api/server.py`**:

```python
# Upload directory
UPLOAD_DIR = PROJECT_ROOT / "sources" / "uploads"

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        # Add production URLs here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Start Configuration

```bash
# Default port
./scripts/start_backend.sh

# Custom port
./scripts/start_backend.sh 8080

# Production with Uvicorn
uvicorn api.server:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend Configuration

**In `frontend/vite.config.js`**:

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,  // Frontend port
    proxy: {
      '/api': {
        target: 'http://localhost:8001',  // Backend URL
        changeOrigin: true,
      },
      '/outputs': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      }
    }
  }
})
```

## 📁 Directory Structure Configuration

### Output Directory Layout

```
outputs/                           # Configurable via --output-dir
  └── {project_name}/              # From input filename
      └── {content_type}/          # "paper" or "general"
          └── {mode}/               # "fast" or "normal"
              ├── checkpoint_rag.json
              ├── checkpoint_summary.json
              ├── summary.md
              ├── rag_output/      # Parsed markdown files
              └── {config_name}/   # e.g., "slides_doraemon_medium"
                  ├── state.json
                  ├── checkpoint_plan.json
                  └── {timestamp}/ # e.g., "20241210_123456"
                      ├── slide_01.png
                      ├── slide_02.png
                      └── slides.pdf
```

### Custom Output Directory

```bash
# Use custom directory
python -m paper2slides \
  --input paper.pdf \
  --output slides \
  --output-dir /path/to/custom/outputs
```

### Upload Directory (API only)

```
sources/
  └── uploads/
      ├── paper_{uuid}.pdf
      ├── report_{uuid}.docx
      └── ...
```

Configured in `api/server.py`:
```python
UPLOAD_DIR = PROJECT_ROOT / "sources" / "uploads"
```

## 🎨 Style Configuration

### Built-in Styles

#### Academic Style
```python
style = "academic"
```

Characteristics:
- Clean, professional design
- White or light background
- Minimal decorations
- Focus on content
- Sans-serif fonts
- High contrast for readability

#### Doraemon Style
```python
style = "doraemon"
```

Characteristics:
- Colorful, friendly design
- Character elements
- Warm color palette
- Rounded shapes
- Engaging visuals
- Suitable for general audiences

### Custom Styles

Describe your style in natural language:

```bash
# Minimalist
python -m paper2slides --input paper.pdf --style "minimalist with blue and white theme"

# Corporate
python -m paper2slides --input paper.pdf --style "professional corporate with charts and graphs"

# Creative
python -m paper2slides --input paper.pdf --style "warm and creative with soft colors"

# Technical
python -m paper2slides --input paper.pdf --style "modern tech style with dark mode and neon accents"
```

**Style Processing**:
LLM processes description to extract:
- Style name/theme
- Color tone
- Special elements
- Decorations

**Example Processing**:
```
Input: "elegant minimalist with pink and gold accents"

Processed:
  style_name: "Elegant Minimalist"
  color_tone: "Soft pink background with gold accent colors"
  special_elements: ""
  decorations: "Subtle geometric patterns"
```

## 🔢 Model Configuration

### RAG & Content Extraction

**Default Models** (in code):
```python
# RAG queries and planning
model = "gpt-4o"

# Content extraction
model = "gpt-4o-mini"

# Embeddings (for normal mode RAG)
embedding_model = "text-embedding-3-small"
```

**Environment Variable Override**:
```bash
# In paper2slides/.env
RAG_LLM_API_KEY=your-key
RAG_LLM_BASE_URL=https://api.openai.com/v1

# For custom models (code modification required)
```

### Image Generation

**Default Model**:
```python
model = "google/gemini-3-pro-image-preview"
```

This uses OpenRouter to access Gemini 3 Pro.

**Environment Configuration**:
```bash
# In paper2slides/.env
IMAGE_GEN_API_KEY=your-openrouter-key
IMAGE_GEN_BASE_URL=https://openrouter.ai/api/v1
```

## 🎛️ Advanced Configuration

### RAG Configuration

**In `paper2slides/rag/config.py`**:

```python
@dataclass
class RAGConfig:
    storage_dir: str                    # LightRAG storage
    output_dir: str                     # Parser output
    model: str = "gpt-4o"              # LLM model
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    max_tokens: int = 32768
    temperature: float = 0.3
    # ... more options
```

Most users don't need to modify this. Defaults work well.

### Parser Configuration

**In `paper2slides/raganything/batch_parser.py`**:

```python
class BatchParser:
    def __init__(
        self,
        parser_type: str = "mineru",
        max_workers: int = 4,           # Parallel parsing
        show_progress: bool = True,
        skip_installation_check: bool = True,
    ):
```

### Generation Configuration

**In `paper2slides/generator/config.py`**:

```python
@dataclass
class GenerationConfig:
    output_type: OutputType             # SLIDES or POSTER
    poster_density: PosterDensity       # SPARSE, MEDIUM, DENSE
    slides_length: SlidesLength         # SHORT, MEDIUM, LONG
    style: StyleType                    # ACADEMIC, DORAEMON, CUSTOM
    custom_style: Optional[str] = None
```

## 📝 Logging Configuration

### Log Levels

```bash
# Normal (INFO)
python -m paper2slides --input paper.pdf --output slides

# Debug (DEBUG)
python -m paper2slides --input paper.pdf --output slides --debug
```

### Log Format

Logs include:
- Timestamp
- Log level
- Module name
- Message

**Example Output**:
```
2024-12-10 12:34:56 INFO     paper2slides.main: Input: paper.pdf (file)
2024-12-10 12:34:56 INFO     paper2slides.core.pipeline: Starting from stage: rag
2024-12-10 12:34:57 INFO     paper2slides.core.stages.rag_stage: Running in NORMAL mode
```

### Section Separators

Important sections are highlighted:
```
========================================
STAGE: RAG
========================================
```

## 🐛 Debug Configuration

### Enable Debug Mode

```bash
python -m paper2slides --input paper.pdf --output slides --debug
```

**Additional Debug Info**:
- Detailed API calls
- Checkpoint operations
- File operations
- LLM prompts and responses
- Error stack traces

### Inspect Checkpoints

```bash
# View RAG results
cat outputs/paper/paper/normal/checkpoint_rag.json | jq .

# View summary
cat outputs/paper/paper/normal/checkpoint_summary.json | jq .

# View plan
cat outputs/paper/paper/normal/slides_doraemon_medium/checkpoint_plan.json | jq .

# View state
cat outputs/paper/paper/normal/slides_doraemon_medium/state.json | jq .
```

## 🌐 Production Configuration

### Environment Variables for Production

```bash
# Production .env
RAG_LLM_API_KEY=your-production-key
RAG_LLM_BASE_URL=https://api.openai.com/v1
IMAGE_GEN_API_KEY=your-production-key
IMAGE_GEN_BASE_URL=https://openrouter.ai/api/v1

# Optional: Set custom output directory
PAPER2SLIDES_OUTPUT_DIR=/var/lib/paper2slides/outputs
```

### API Server Production

```bash
# Using Uvicorn with workers
uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 4 \
  --log-level info

# Or using Gunicorn
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name paper2slides.example.com;

    # Increase upload size
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Longer timeout for processing
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

### Docker Configuration

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=""

# Create directories
RUN mkdir -p outputs sources/uploads logs

EXPOSE 8001

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  paper2slides:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./outputs:/app/outputs
      - ./sources:/app/sources
      - ./logs:/app/logs
      - ./paper2slides/.env:/app/paper2slides/.env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

## 💾 Storage Configuration

### Checkpoint Storage

Checkpoints are JSON files:
- Small size (~1-10 MB each)
- Plain text (readable)
- Can be version controlled (if desired)

### Image Storage

Generated images:
- PNG/JPEG format
- ~500 KB - 2 MB per image
- Stored in timestamped directories

### Cleanup Strategy

```bash
# Remove old outputs (older than 30 days)
find outputs/ -type d -name "20*" -mtime +30 -exec rm -rf {} +

# Remove specific project
rm -rf outputs/paper_name/

# Keep checkpoints, remove images
find outputs/ -type d -name "20*" -exec rm -rf {} +
```

## 🔒 Security Configuration

### API Key Security

**Never commit .env file**:
```bash
# .gitignore includes
paper2slides/.env
```

**Use environment variables in production**:
```bash
export RAG_LLM_API_KEY="..."
export IMAGE_GEN_API_KEY="..."
```

**Rotate keys regularly**:
- Update keys every 90 days
- Use separate keys for dev/prod

### File Upload Security

**Size limits** (configure in API):
```python
# In api/server.py
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
```

**Allowed file types**:
- Enforced by parser: PDF, DOCX, XLSX, PPTX, MD

**Filename sanitization**:
- UUID-based filenames prevent path traversal
- Original names stored in metadata

## 📚 Configuration Examples

### Development Setup

```bash
# Fast iteration
python -m paper2slides \
  --input test_paper.pdf \
  --output slides \
  --style doraemon \
  --length short \
  --fast \
  --parallel 2 \
  --debug
```

### Production Setup

```bash
# High quality
python -m paper2slides \
  --input paper.pdf \
  --output slides \
  --style academic \
  --length long \
  --parallel 2 \
  --output-dir /var/lib/paper2slides/outputs
```

### Batch Processing

```bash
# Process all papers in directory
python -m paper2slides \
  --input ./papers/ \
  --output slides \
  --style academic \
  --length medium \
  --parallel 2
```

## 🔧 Troubleshooting Configuration

### API Key Issues

```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $RAG_LLM_API_KEY"

# Test OpenRouter key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $IMAGE_GEN_API_KEY"
```

### Permission Issues

```bash
# Fix directory permissions
chmod -R 755 outputs sources

# Fix file permissions
chmod 600 paper2slides/.env
```

### Path Issues

```bash
# Use absolute paths
python -m paper2slides --input /absolute/path/to/paper.pdf

# Or ensure current directory is project root
cd /path/to/Paper2Slides
python -m paper2slides --input paper.pdf
```

## 📚 Next Steps

- **[Development Guide](./09-development-guide.md)**: Contributing and extending
- **[Troubleshooting](./10-troubleshooting.md)**: Common issues and solutions
- **[API Reference](./04-api-reference.md)**: API details
