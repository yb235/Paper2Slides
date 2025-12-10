# Architecture

## 🏛️ System Architecture Overview

Paper2Slides is built on a modular, pipeline-based architecture that processes documents through four distinct stages. The system is designed for reliability, efficiency, and extensibility.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Paper2Slides System                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   CLI Entry  │    │  Web API     │    │   Frontend   │        │
│  │   (main.py)  │    │  (server.py) │    │   (React)    │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│         │                   │                    │                 │
│         └───────────────────┴────────────────────┘                 │
│                             │                                       │
│                    ┌────────▼────────┐                             │
│                    │  Core Pipeline  │                             │
│                    │  Orchestrator   │                             │
│                    └────────┬────────┘                             │
│                             │                                       │
│         ┌───────────────────┼───────────────────┐                 │
│         │                   │                   │                  │
│    ┌────▼────┐         ┌───▼────┐         ┌───▼────┐             │
│    │   RAG   │────────▶│Summary │────────▶│  Plan  │─────┐       │
│    │  Stage  │         │ Stage  │         │ Stage  │     │       │
│    └─────────┘         └────────┘         └────────┘     │       │
│         │                   │                   │         │       │
│         │                   │                   │         │       │
│    ┌────▼──────┐       ┌───▼────────┐     ┌───▼─────┐   │       │
│    │checkpoint │       │checkpoint  │     │checkpoint│   │       │
│    │_rag.json  │       │_summary.json│    │_plan.json│   │       │
│    └───────────┘       └────────────┘     └──────────┘   │       │
│                                                            │       │
│                                                       ┌────▼────┐  │
│                                                       │Generate │  │
│                                                       │ Stage   │  │
│                                                       └────┬────┘  │
│                                                            │       │
│                                                       ┌────▼────┐  │
│                                                       │ Images  │  │
│                                                       │  & PDF  │  │
│                                                       └─────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🧩 Core Components

### 1. Entry Points

#### CLI Entry (`paper2slides/main.py`)
- **Purpose**: Command-line interface for direct invocation
- **Features**:
  - Argument parsing and validation
  - Path normalization
  - Configuration building
  - Pipeline invocation
- **Usage**: `python -m paper2slides --input paper.pdf --output slides`

#### Web API (`api/server.py`)
- **Purpose**: HTTP API for web interface and programmatic access
- **Framework**: FastAPI with CORS middleware
- **Features**:
  - File upload handling
  - Session management (prevents concurrent runs)
  - Background task execution
  - Progress tracking via state files
  - Static file serving
- **Endpoints**: See [API Reference](./04-api-reference.md)

#### Frontend (`frontend/src/`)
- **Purpose**: Web-based user interface
- **Framework**: React 18 + Vite
- **Features**:
  - Drag-and-drop file upload
  - Real-time progress tracking
  - Configuration controls
  - Result visualization
  - PDF/image preview

### 2. Core Pipeline (`paper2slides/core/`)

The core pipeline orchestrates the entire workflow through four stages.

#### Pipeline Orchestrator (`pipeline.py`)
```python
async def run_pipeline(base_dir, config_dir, config, from_stage, session_id, session_manager)
```

**Responsibilities**:
- Stage sequencing and execution
- State management and persistence
- Error handling and recovery
- Cancellation support (for web interface)
- Progress logging

**State Management** (`state.py`):
```python
STAGES = ["rag", "summary", "plan", "generate"]

state = {
    "session_id": "...",
    "config": {...},
    "stages": {
        "rag": "completed|running|pending|failed|cancelled",
        "summary": "...",
        "plan": "...",
        "generate": "..."
    },
    "error": None
}
```

#### Path Management (`paths.py`)
Centralizes all file path logic:
```python
# Directory structure
outputs/
  └── <project_name>/
      └── <content_type>/          # paper or general
          └── <mode>/               # fast or normal
              ├── checkpoint_rag.json
              ├── checkpoint_summary.json
              ├── summary.md
              └── <config_name>/    # e.g., slides_doraemon_medium
                  ├── state.json
                  ├── checkpoint_plan.json
                  └── <timestamp>/
                      ├── slide_01.png
                      └── slides.pdf
```

**Key Functions**:
- `get_base_dir()`: Project/content-specific directory
- `get_config_dir()`: Configuration-specific directory
- `get_rag_checkpoint()`: RAG checkpoint path (mode-aware)
- `get_summary_checkpoint()`: Summary checkpoint path (mode-aware)
- `get_plan_checkpoint()`: Plan checkpoint path
- `get_output_dir()`: Final output directory

### 3. Stage Implementations (`paper2slides/core/stages/`)

Each stage is an independent module with clear inputs and outputs.

#### RAG Stage (`rag_stage.py`)
```python
async def run_rag_stage(base_dir: Path, config: Dict) -> Dict
```

**Two Modes**:

**Fast Mode**:
1. Parse documents using MinerU
2. Embed images as base64 in markdown
3. Query GPT-4o directly with content and images
4. Save results to checkpoint

**Normal Mode**:
1. Parse documents using MinerU
2. Index content in LightRAG
3. Query using RAG retrieval
4. Save results to checkpoint

**Output**: `checkpoint_rag.json`
```json
{
  "rag_results": {
    "paper_info": [...],
    "structure": [...],
    "methodology": [...],
    ...
  },
  "markdown_paths": ["path/to/file.md"],
  "input_path": "path/to/input",
  "content_type": "paper",
  "mode": "fast|normal"
}
```

#### Summary Stage (`summary_stage.py`)
```python
async def run_summary_stage(base_dir: Path, config: Dict) -> Dict
```

**Process**:
1. Load RAG checkpoint
2. Extract paper metadata from markdown (direct, bypassing RAG)
3. Extract content structure using LLM
4. Extract figures and tables from markdown
5. Save structured summary

**Output**: `checkpoint_summary.json` + `summary.md`
```json
{
  "content_type": "paper",
  "content": {
    "title": "...",
    "authors": [...],
    "abstract": "...",
    "sections": [...]
  },
  "origin": {
    "tables": [...],
    "figures": [...],
    "base_path": "..."
  },
  "markdown_paths": [...]
}
```

#### Plan Stage (`plan_stage.py`)
```python
async def run_plan_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict
```

**Process**:
1. Load summary checkpoint
2. Create GenerationInput with content and origin
3. Use ContentPlanner to generate layout
4. Assign figures/tables to sections
5. Save plan

**Output**: `checkpoint_plan.json`
```json
{
  "plan": {
    "output_type": "slides",
    "sections": [
      {
        "id": "slide_01",
        "title": "Title Slide",
        "type": "title",
        "content": "...",
        "tables": [],
        "figures": []
      },
      ...
    ],
    "metadata": {...}
  },
  "origin": {...},
  "content_type": "paper"
}
```

#### Generate Stage (`generate_stage.py`)
```python
async def run_generate_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict
```

**Process**:
1. Load plan and summary checkpoints
2. Reconstruct ContentPlan with figures/tables
3. Use ImageGenerator to create images
4. Save images incrementally (with callback)
5. Generate PDF for slides
6. Return output directory

**Output**: Directory with images and PDF
```
output_dir/
  ├── slide_01.png
  ├── slide_02.png
  ├── ...
  └── slides.pdf (for slides only)
```

### 4. RAG System (`paper2slides/raganything/` and `paper2slides/rag/`)

#### Document Parsing (`raganything/batch_parser.py`)
- **Parser**: MinerU (mineru library)
- **Capabilities**: PDF, DOCX, XLSX, PPTX, MD
- **Output**: Markdown with embedded images
- **Features**: Batch processing, progress tracking

#### RAG Client (`rag/client.py`)
```python
class RAGClient:
    async def index_batch(file_paths, output_dir, recursive)
    async def batch_query(queries, mode)
    async def batch_query_by_category(queries_by_category, modes_by_category)
```

**Indexing**:
- Uses LightRAG for graph-enhanced retrieval
- Stores vectors and graph structure
- Handles multiple files with unified index

**Querying**:
- **Mode**: `local` (keyword), `global` (overview), `hybrid` (both), `mix` (auto)
- **Batching**: Concurrent queries with configurable concurrency
- **Categorization**: Group queries by category for organized results

#### Query Sets (`rag/query.py`)
Predefined queries for different content types:

```python
RAG_PAPER_QUERIES = {
    "paper_info": ["List paper title, authors, affiliations..."],
    "structure": ["What are main sections?", ...],
    "methodology": ["What methods are used?", ...],
    "results": ["What are key findings?", ...],
    "figures_tables": ["Describe all figures and tables..."],
}
```

### 5. Summary System (`paper2slides/summary/`)

#### Paper Content Extraction (`summary/paper.py`)
```python
async def extract_paper(rag_results, llm_client, model, parallel)
async def extract_paper_metadata_from_markdown(markdown_paths, llm_client)
```

**Extracts**:
- Title, authors, affiliations
- Abstract
- Sections (intro, methods, results, discussion, conclusion)
- Key findings and contributions

**Output**: `PaperContent` dataclass

#### General Content Extraction (`summary/general.py`)
```python
async def extract_general(rag_results, llm_client, model)
```

For non-paper documents, extracts general content based on queries.

#### Figure & Table Extraction (`summary/extractors/`)
Parses markdown to extract:
- Figure references with captions and image paths
- Table references with captions and HTML content
- Maintains base path for relative image resolution

### 6. Generator System (`paper2slides/generator/`)

#### Content Planner (`generator/content_planner.py`)
```python
class ContentPlanner:
    def plan(gen_input: GenerationInput) -> ContentPlan
```

**Process**:
1. Load appropriate prompt template (paper/general, slides/poster)
2. Build context with content, figures, tables
3. Query LLM for structured plan
4. Parse JSON response into ContentPlan
5. Validate and return

**Prompts** (`paper2slides/prompts/content_planning.py`):
- `PAPER_SLIDES_PLANNING_PROMPT`: For paper slides
- `PAPER_POSTER_PLANNING_PROMPT`: For paper posters
- `GENERAL_SLIDES_PLANNING_PROMPT`: For general slides
- `GENERAL_POSTER_PLANNING_PROMPT`: For general posters

#### Image Generator (`generator/image_generator.py`)
```python
class ImageGenerator:
    def generate(plan, gen_input, max_workers, save_callback) -> List[GeneratedImage]
```

**Process**:
1. Process custom style (if specified) using LLM
2. Prepare prompts for each section with:
   - Content text
   - Figure/table references
   - Style directives
   - Layout hints
3. Generate images (sequential or parallel)
4. Call save callback for each completed image
5. Return all generated images

**Parallel Generation**:
- Uses ThreadPoolExecutor
- Configurable worker count (`--parallel N`)
- Progress tracking per image

**Style Processing**:
- Built-in styles: `academic`, `doraemon`
- Custom styles: Natural language → Structured style
- LLM processes custom descriptions into style parameters

### 7. Utilities (`paper2slides/utils/`)

#### Logging (`utils/__init__.py`)
```python
def setup_logging(level)
def log_section(title)  # Visual section separators
```

#### Path Utilities (`utils/path_utils.py`)
```python
def normalize_input_path(path)      # Relative → Absolute
def get_project_name(path)          # Extract project name
def parse_style(style_str)          # Parse style parameter
```

#### File I/O (`utils/__init__.py`)
```python
def load_json(path)
def save_json(path, data)
def save_text(path, text)
```

## 🔄 Data Flow

### Full Pipeline Data Flow

```
Input Document(s)
      │
      ▼
┌─────────────┐
│ RAG Stage   │  Parse + Index/Query
└──────┬──────┘
       │ checkpoint_rag.json
       │ {rag_results, markdown_paths, input_path, content_type, mode}
       ▼
┌─────────────┐
│Summary Stage│  Extract Content + Figures/Tables
└──────┬──────┘
       │ checkpoint_summary.json + summary.md
       │ {content_type, content, origin, markdown_paths}
       ▼
┌─────────────┐
│ Plan Stage  │  Layout Planning + Figure/Table Assignment
└──────┬──────┘
       │ checkpoint_plan.json
       │ {plan, origin, content_type}
       ▼
┌─────────────┐
│Generate Stage│ Image Generation + PDF Creation
└──────┬──────┘
       │
       ▼
Output Directory
├── slide_01.png
├── slide_02.png
├── ...
└── slides.pdf
```

### Checkpoint Reuse

```
Change Style Only:
  checkpoint_rag.json ──┐
  checkpoint_summary.json ──┐
                         │  │
                         ▼  ▼
                    Plan Stage (regenerate)
                         │
                         ▼
                   Generate Stage (regenerate)

Change Length/Density:
  Same as style change (Plan + Generate)

Force Full Restart:
  Start from RAG Stage (all stages regenerate)
```

## 🎨 Design Principles

### 1. Modularity
- Each stage is independent and testable
- Clear interfaces between stages
- Pluggable components (parsers, LLMs, generators)

### 2. Reliability
- Checkpoint after every stage
- Graceful error handling
- Resume capability
- Cancellation support

### 3. Efficiency
- Reuse checkpoints when possible
- Parallel processing where beneficial
- Lazy loading of resources
- Configurable concurrency

### 4. Extensibility
- Easy to add new content types
- Pluggable style systems
- Custom query sets
- Multiple LLM backends

### 5. Transparency
- Comprehensive logging
- Intermediate results saved
- Clear progress indicators
- Traceable decisions

## 🔌 External Dependencies

### LLM Services
- **OpenAI API**: For RAG queries, content extraction, planning
  - Models: GPT-4o, GPT-4o-mini
  - Configured via: `RAG_LLM_API_KEY`, `RAG_LLM_BASE_URL`

- **OpenRouter API**: For image generation
  - Model: Gemini 3 Pro Image Preview
  - Configured via: `IMAGE_GEN_API_KEY`, `IMAGE_GEN_BASE_URL`

### Libraries
- **LightRAG**: Graph-enhanced RAG framework
- **MinerU**: Document parsing (PDF, DOCX, etc.)
- **FastAPI**: Web framework
- **React**: Frontend framework

## 📦 Deployment Architecture

### Development
```
Terminal 1: Backend API (port 8001)
Terminal 2: Frontend Dev Server (port 5173)
```

### Production (Recommended)
```
Nginx/Caddy
    ├── /api → Backend (Uvicorn workers)
    └── / → Frontend (Static build)
```

## 🔐 Security Considerations

- **API Keys**: Stored in `.env` file, never committed
- **File Upload**: Saved to dedicated upload directory
- **Static Files**: Served with proper MIME types
- **CORS**: Configured for specific origins
- **Session Management**: Prevents concurrent runs, tracks cancellation

## 🚀 Performance Optimizations

1. **Parallel RAG Queries**: Concurrent execution with semaphore
2. **Async Pipeline**: Async/await for I/O-bound operations
3. **Incremental Saving**: Images saved as generated
4. **Smart Checkpointing**: Reuse previous work when possible
5. **Configurable Workers**: Parallel image generation
6. **Lazy Loading**: Load checkpoints only when needed

## 🧪 Testing Strategy

While not extensively covered in code, recommended testing:
- **Unit Tests**: Individual stage functions
- **Integration Tests**: Full pipeline runs
- **API Tests**: Endpoint validation
- **End-to-End Tests**: CLI and web interface
