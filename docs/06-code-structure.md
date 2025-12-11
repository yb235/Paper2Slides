# Code Structure

This document explains the organization of the Paper2Slides codebase to help developers understand where to find specific functionality and how modules interact.

## 📁 Project Structure Overview

```
Paper2Slides/
├── paper2slides/          # Core library (main package)
│   ├── core/              # Pipeline orchestration
│   ├── raganything/       # Document parsing
│   ├── rag/               # RAG client and queries
│   ├── summary/           # Content extraction
│   ├── generator/         # Planning and image generation
│   ├── prompts/           # LLM prompt templates
│   ├── utils/             # Utilities and helpers
│   ├── main.py            # CLI entry point
│   ├── __main__.py        # Package execution
│   └── .env.example       # Environment template
│
├── api/                   # Web API backend
│   └── server.py          # FastAPI application
│
├── frontend/              # React web interface
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── styles/        # CSS styles
│   │   ├── App.jsx        # Main app component
│   │   └── main.jsx       # Entry point
│   ├── package.json
│   └── vite.config.js
│
├── scripts/               # Shell scripts
│   ├── start.sh           # Start all services
│   ├── start_backend.sh   # Start backend only
│   ├── start_frontend.sh  # Start frontend only
│   ├── stop.sh            # Stop services
│   └── check_config.sh    # Config validation
│
├── outputs/               # Generated outputs (gitignored)
├── sources/               # Uploaded files (gitignored)
├── requirements.txt       # Python dependencies
├── README.md              # Main documentation
└── LICENSE                # MIT License
```

## 🎯 Core Package (`paper2slides/`)

The main Python package containing all processing logic.

### Entry Points

#### `main.py`
CLI entry point with argument parsing.

**Key Functions**:
```python
def main():
    """Main CLI entry point."""
    # Parse arguments
    # Normalize paths
    # Build configuration
    # Detect start stage
    # Run pipeline
```

**Responsibilities**:
- Command-line argument parsing
- Input path validation and normalization
- Configuration construction
- Pipeline invocation
- Output directory management

#### `__main__.py`
Enables running as module: `python -m paper2slides`

```python
from paper2slides.main import main

if __name__ == "__main__":
    main()
```

### Core Pipeline (`paper2slides/core/`)

Pipeline orchestration and state management.

#### `pipeline.py`
Main pipeline execution logic.

**Key Functions**:
```python
async def run_pipeline(
    base_dir: Path,
    config_dir: Path,
    config: Dict,
    from_stage: str,
    session_id: str = None,
    session_manager = None
):
    """Execute pipeline from specified stage."""
```

**Flow**:
1. Load or create state
2. Execute stages sequentially
3. Handle cancellation (for web interface)
4. Save state after each stage
5. Log progress and summary

```python
def list_outputs(output_dir: str):
    """List all processed documents and their states."""
```

Lists all projects with checkpoint status indicators.

#### `state.py`
State management and checkpoint detection.

**Key Constants**:
```python
STAGES = ["rag", "summary", "plan", "generate"]
```

**Key Functions**:
```python
def create_state(config: Dict) -> Dict:
    """Create initial state for new pipeline run."""

def load_state(config_dir: Path) -> Optional[Dict]:
    """Load existing state from config directory."""

def save_state(config_dir: Path, state: Dict):
    """Save current state to config directory."""

def detect_start_stage(base_dir: Path, config_dir: Path, config: Dict) -> str:
    """Determine which stage to start from based on checkpoints."""
```

**State Structure**:
```python
{
    "session_id": "uuid",
    "config": {...},
    "stages": {
        "rag": "completed|running|pending|failed|cancelled",
        "summary": "...",
        "plan": "...",
        "generate": "..."
    },
    "error": None,
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp"
}
```

#### `paths.py`
Centralized path management.

**Key Functions**:
```python
def get_base_dir(output_dir: str, project_name: str, content_type: str) -> Path:
    """Get base directory: output_dir/project/content_type/"""

def get_mode_dir(base_dir: Path, fast_mode: bool) -> Path:
    """Get mode directory: base_dir/fast/ or base_dir/normal/"""

def get_config_name(config: Dict) -> str:
    """Generate config name: slides_doraemon_medium"""

def get_config_dir(base_dir: Path, config: Dict) -> Path:
    """Get config directory with mode awareness"""

def get_rag_checkpoint(base_dir: Path, config: Dict) -> Path:
    """Path to checkpoint_rag.json (mode-specific)"""

def get_summary_checkpoint(base_dir: Path, config: Dict) -> Path:
    """Path to checkpoint_summary.json (mode-specific)"""

def get_summary_md(base_dir: Path, config: Dict) -> Path:
    """Path to summary.md (mode-specific)"""

def get_plan_checkpoint(config_dir: Path) -> Path:
    """Path to checkpoint_plan.json"""

def get_output_dir(config_dir: Path) -> Path:
    """Path to timestamped output directory"""
```

**Directory Structure Logic**:
```
outputs/
  └── {project_name}/           # from get_project_name(input)
      └── {content_type}/       # "paper" or "general"
          └── {mode}/            # "fast" or "normal"
              ├── checkpoint_rag.json
              ├── checkpoint_summary.json
              ├── summary.md
              └── {config_name}/  # "slides_style_length"
                  ├── state.json
                  ├── checkpoint_plan.json
                  └── {timestamp}/ # "YYYYMMDD_HHMMSS"
```

#### `stages/` Directory

Individual stage implementations.

**`rag_stage.py`**:
```python
async def run_rag_stage(base_dir: Path, config: Dict) -> Dict:
    """Stage 1: Parse and index documents, run queries."""
```

**`summary_stage.py`**:
```python
async def run_summary_stage(base_dir: Path, config: Dict) -> Dict:
    """Stage 2: Extract structured content."""
```

**`plan_stage.py`**:
```python
async def run_plan_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict:
    """Stage 3: Generate content plan."""
```

**`generate_stage.py`**:
```python
async def run_generate_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict:
    """Stage 4: Generate images."""
```

### RAG System

#### `raganything/` - Document Parsing

**`batch_parser.py`**: High-level batch parsing interface
```python
class BatchParser:
    def __init__(self, parser_type="mineru", max_workers=4):
        """Initialize batch parser."""
    
    def process_batch(
        self,
        file_paths: List[str],
        output_dir: str,
        parse_method: str = "auto",
        recursive: bool = False,
    ) -> BatchResult:
        """Process multiple files in batch."""
```

**`parser.py`**: Core parsing logic using MinerU
```python
class DocumentParser:
    def parse(self, file_path: str, output_dir: str) -> ParseResult:
        """Parse single document to markdown."""
```

**`enhanced_markdown.py`**: Markdown processing utilities

**`modalprocessors.py`**: Multi-modal content processors

#### `rag/` - RAG Client

**`client.py`**: Main RAG interface
```python
class RAGClient:
    def __init__(self, config: RAGConfig):
        """Initialize RAG client with LightRAG."""
    
    async def index_batch(
        self,
        file_paths: List[str],
        output_dir: str,
        recursive: bool = False,
        show_progress: bool = True
    ) -> Dict:
        """Index documents for retrieval."""
    
    async def batch_query(
        self,
        queries: List[str],
        mode: str = "hybrid"
    ) -> List[Dict]:
        """Execute batch queries."""
    
    async def batch_query_by_category(
        self,
        queries_by_category: Dict[str, List[str]],
        modes_by_category: Dict[str, str] = None
    ) -> Dict[str, List[Dict]]:
        """Execute categorized batch queries."""
```

**`query.py`**: Query definitions
```python
# Predefined query sets
RAG_PAPER_QUERIES = {
    "paper_info": [...],
    "structure": [...],
    "methodology": [...],
    "results": [...],
    "figures_tables": [...]
}

RAG_QUERY_MODES = {
    "paper_info": "local",
    "structure": "hybrid",
    "methodology": "hybrid",
    "results": "hybrid",
    "figures_tables": "mix"
}

# Dynamic query generation
async def get_general_overview(rag_client, mode="mix") -> str:
    """Get document overview for general content."""

def generate_general_queries(rag_client, overview: str, count: int) -> List[str]:
    """Generate queries based on overview."""
```

**`config.py`**: RAG configuration
```python
@dataclass
class RAGConfig:
    storage_dir: str         # LightRAG storage
    output_dir: str          # Parser output
    model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    # ... more config options
    
    @classmethod
    def with_paths(cls, storage_dir: str, output_dir: str) -> 'RAGConfig':
        """Create config with custom paths."""
```

### Summary System (`paper2slides/summary/`)

**`paper.py`**: Paper content extraction
```python
@dataclass
class PaperContent:
    title: str
    authors: List[str]
    affiliations: str
    abstract: str
    introduction: str
    methodology: str
    results: str
    discussion: str
    conclusion: str
    contributions: List[str]

async def extract_paper(
    rag_results: Dict[str, List[Dict]],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
    parallel: bool = True,
    max_concurrency: int = 5,
) -> PaperContent:
    """Extract structured paper content from RAG results."""

async def extract_paper_metadata_from_markdown(
    markdown_paths: List[str],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
    max_chars_per_file: int = 3000
) -> str:
    """Extract paper metadata directly from markdown."""
```

**`general.py`**: General content extraction
```python
@dataclass
class GeneralContent:
    content: str

async def extract_general(
    rag_results: List[Dict],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
) -> GeneralContent:
    """Extract general document content."""
```

**`models.py`**: Data models
```python
@dataclass
class TableInfo:
    table_id: str           # "Table1"
    caption: str
    html_content: str

@dataclass
class FigureInfo:
    figure_id: str          # "Figure1"
    caption: str
    image_path: str

@dataclass
class OriginalElements:
    tables: List[TableInfo]
    figures: List[FigureInfo]
    base_path: str
```

**`extractors/`**: Figure and table extraction
```python
def extract_tables_and_figures(markdown_path: str) -> OriginalElements:
    """Extract tables and figures from markdown."""
```

### Generator System (`paper2slides/generator/`)

**`config.py`**: Generation configuration
```python
class OutputType(Enum):
    SLIDES = "slides"
    POSTER = "poster"

class SlidesLength(Enum):
    SHORT = "short"     # 5-7 slides
    MEDIUM = "medium"   # 8-12 slides
    LONG = "long"       # 13-20 slides

class PosterDensity(Enum):
    SPARSE = "sparse"   # Minimal content
    MEDIUM = "medium"   # Balanced
    DENSE = "dense"     # Comprehensive

class StyleType(Enum):
    ACADEMIC = "academic"
    DORAEMON = "doraemon"
    CUSTOM = "custom"

@dataclass
class GenerationConfig:
    output_type: OutputType
    poster_density: PosterDensity
    slides_length: SlidesLength
    style: StyleType
    custom_style: Optional[str] = None

@dataclass
class GenerationInput:
    config: GenerationConfig
    content: Union[PaperContent, GeneralContent]
    origin: OriginalElements
```

**`content_planner.py`**: Content planning
```python
@dataclass
class TableRef:
    table_id: str
    extract: str = ""       # Optional: which part to show
    focus: str = ""         # Optional: what to emphasize

@dataclass
class FigureRef:
    figure_id: str
    focus: str = ""         # Optional: what to highlight

@dataclass
class Section:
    id: str
    title: str
    section_type: str       # "title", "content", "methods", etc.
    content: str
    tables: List[TableRef]
    figures: List[FigureRef]

@dataclass
class ContentPlan:
    output_type: str
    sections: List[Section]
    tables_index: Dict[str, TableInfo]
    figures_index: Dict[str, FigureInfo]
    metadata: Dict[str, Any]

class ContentPlanner:
    def __init__(self, api_key: str, base_url: str, model: str = "gpt-4o"):
        """Initialize content planner."""
    
    def plan(self, gen_input: GenerationInput) -> ContentPlan:
        """Generate content plan using LLM."""
```

**`image_generator.py`**: Image generation
```python
@dataclass
class GeneratedImage:
    section_id: str
    image_data: bytes
    mime_type: str

@dataclass
class ProcessedStyle:
    style_name: str
    color_tone: str
    special_elements: str
    decorations: str
    valid: bool
    error: Optional[str] = None

def process_custom_style(
    client: OpenAI,
    user_style: str,
    model: str = None
) -> ProcessedStyle:
    """Process custom style description using LLM."""

class ImageGenerator:
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "google/gemini-3-pro-image-preview",
    ):
        """Initialize image generator."""
    
    def generate(
        self,
        plan: ContentPlan,
        gen_input: GenerationInput,
        max_workers: int = 1,
        save_callback = None,
    ) -> List[GeneratedImage]:
        """Generate images for all sections."""

def save_images_as_pdf(images: List[GeneratedImage], pdf_path: str):
    """Combine images into PDF (for slides)."""
```

### Prompts (`paper2slides/prompts/`)

**`content_planning.py`**: Planning prompt templates
```python
PAPER_SLIDES_PLANNING_PROMPT = """..."""
PAPER_POSTER_PLANNING_PROMPT = """..."""
GENERAL_SLIDES_PLANNING_PROMPT = """..."""
GENERAL_POSTER_PLANNING_PROMPT = """..."""

PAPER_POSTER_DENSITY_GUIDELINES = {...}
GENERAL_POSTER_DENSITY_GUIDELINES = {...}
```

**`image_generation.py`**: Image generation prompts
```python
STYLE_PROCESS_PROMPT = """..."""
FORMAT_POSTER = """..."""
FORMAT_SLIDE = """..."""

POSTER_STYLE_HINTS = {
    "academic": "...",
    "doraemon": "..."
}

SLIDE_STYLE_HINTS = {
    "academic": "...",
    "doraemon": "..."
}

SLIDE_LAYOUTS_ACADEMIC = {
    "title": "...",
    "content": "...",
    "methods": "...",
    "results": "..."
}

SLIDE_COMMON_STYLE_RULES = """..."""
CONSISTENCY_HINT = """..."""
VISUALIZATION_HINTS = """..."""
```

**`paper_extraction.py`**: Content extraction prompts
```python
EXTRACT_PAPER_METADATA_PROMPT = """..."""
EXTRACT_PAPER_CONTENT_PROMPT = """..."""
```

### Utilities (`paper2slides/utils/`)

**`__init__.py`**: Core utilities
```python
def setup_logging(level=logging.INFO):
    """Configure logging for Paper2Slides."""

def log_section(title: str):
    """Print section separator."""

def load_json(path: Path) -> Optional[Dict]:
    """Load JSON file safely."""

def save_json(path: Path, data: Dict):
    """Save data as JSON."""

def save_text(path: Path, text: str):
    """Save text file."""
```

**`path_utils.py`**: Path utilities
```python
def normalize_input_path(path: str) -> str:
    """Convert relative path to absolute."""

def get_project_name(input_path: str) -> str:
    """Extract project name from input path."""

def parse_style(style_str: str) -> Tuple[str, Optional[str]]:
    """Parse style parameter into type and custom description."""
```

## 🌐 Web API (`api/`)

**`server.py`**: FastAPI application

```python
# Configuration
UPLOAD_DIR = PROJECT_ROOT / "sources" / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Session management
class SessionManager:
    """Coordinate concurrent requests."""
    async def start_session(self, session_id: str) -> bool
    async def end_session(self, session_id: str)
    async def cancel_session(self, session_id: str) -> bool
    def is_cancelled(self, session_id: str) -> bool

session_manager = SessionManager()

# FastAPI app
app = FastAPI(title="Paper2Slides API", version="1.0.0")

# CORS configuration
app.add_middleware(CORSMiddleware, ...)

# Static file serving
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)))
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)))

# Endpoints
@app.get("/")
@app.get("/health")
@app.get("/api/session/running")
@app.post("/api/cancel/{session_id}")
@app.post("/api/chat")  # Main generation endpoint
```

## 🎨 Frontend (`frontend/`)

**React + Vite structure**:

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx      # Drag-and-drop file upload
│   │   ├── ConfigPanel.jsx     # Configuration controls
│   │   ├── ProgressBar.jsx     # Stage progress display
│   │   ├── ResultsView.jsx     # Generated slides/poster
│   │   └── ErrorMessage.jsx    # Error display
│   │
│   ├── styles/
│   │   └── index.css           # Global styles (Tailwind)
│   │
│   ├── App.jsx                 # Main application
│   ├── main.jsx                # Entry point
│   └── utils.js                # Helper functions
│
├── public/                     # Static assets
├── index.html                  # HTML template
├── package.json                # Dependencies
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
└── postcss.config.js           # PostCSS configuration
```

**Key Components**:

```javascript
// App.jsx - Main application
function App() {
  const [files, setFiles] = useState([]);
  const [config, setConfig] = useState({...});
  const [progress, setProgress] = useState({});
  const [results, setResults] = useState(null);
  
  const handleUpload = async () => {
    // Upload files and start processing
    // Poll for progress
    // Display results
  };
  
  return (
    <>
      <FileUpload onFilesSelected={setFiles} />
      <ConfigPanel config={config} onChange={setConfig} />
      <ProgressBar progress={progress} />
      <ResultsView results={results} />
    </>
  );
}
```

## 🔧 Scripts (`scripts/`)

**`start.sh`**: Start all services
- Finds available backend port
- Starts backend with retry logic
- Starts frontend
- Cleanup on exit

**`start_backend.sh`**: Start backend only
```bash
python api/server.py [port]
```

**`start_frontend.sh`**: Start frontend only
```bash
npm run dev
```

**`stop.sh`**: Stop all services
```bash
pkill -f "python api/server.py"
pkill -f "npm run dev"
```

**`check_config.sh`**: Validate configuration
```bash
# Check for .env file
# Validate API keys
# Test connectivity
```

## 📦 Dependencies

### Python Dependencies (`requirements.txt`)

**Core RAG**:
- `lightrag-hku`: Graph-enhanced RAG
- `mineru[core]`: Document parsing
- `huggingface_hub`: Model downloads

**Image Processing**:
- `Pillow`: Image manipulation
- `reportlab`: PDF generation

**API**:
- `openai`: LLM API client
- `python-dotenv`: Environment variables

**Web API**:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `python-multipart`: File upload handling

**Data Processing**:
- `pyyaml`: YAML configuration
- `requests`: HTTP client
- `tqdm`: Progress bars

### Frontend Dependencies (`package.json`)

**React**:
- `react`: UI framework
- `react-dom`: DOM rendering

**UI**:
- `lucide-react`: Icon library
- `tailwindcss`: Utility-first CSS

**HTTP**:
- `axios`: API client

**Build**:
- `vite`: Build tool and dev server
- `@vitejs/plugin-react`: React plugin

## 🔄 Module Interactions

```
CLI (main.py)
    ↓
Core Pipeline (pipeline.py)
    ↓
    ├──→ RAG Stage (rag_stage.py)
    │       ↓
    │       ├──→ BatchParser (raganything/)
    │       └──→ RAGClient (rag/)
    │
    ├──→ Summary Stage (summary_stage.py)
    │       ↓
    │       ├──→ extract_paper/extract_general (summary/)
    │       └──→ extract_tables_and_figures (summary/extractors/)
    │
    ├──→ Plan Stage (plan_stage.py)
    │       ↓
    │       └──→ ContentPlanner (generator/)
    │               ↓
    │               └──→ Prompts (prompts/)
    │
    └──→ Generate Stage (generate_stage.py)
            ↓
            └──→ ImageGenerator (generator/)
                    ↓
                    ├──→ process_custom_style()
                    └──→ Prompts (prompts/)

Web API (server.py)
    ↓
    ├──→ SessionManager (concurrency control)
    ├──→ Core Pipeline (background tasks)
    └──→ Static Files (outputs/, uploads/)
        ↑
        │
    Frontend (React)
```

## 🎯 Key Design Patterns

### 1. Pipeline Pattern
Sequential stage execution with checkpoints.

### 2. Factory Pattern
Configuration-based object creation (parsers, generators).

### 3. Strategy Pattern
Different modes (fast/normal) with same interface.

### 4. Observer Pattern
Progress tracking via state files.

### 5. Template Method Pattern
Prompt templates with variable substitution.

### 6. Async/Await Pattern
Concurrent I/O operations (queries, file operations).

## 🧪 Testing Approach

While not extensively covered, here's the recommended structure:

```
tests/
├── unit/
│   ├── test_parser.py
│   ├── test_rag_client.py
│   ├── test_content_planner.py
│   └── test_image_generator.py
│
├── integration/
│   ├── test_pipeline.py
│   ├── test_stages.py
│   └── test_checkpoints.py
│
├── e2e/
│   ├── test_cli.py
│   └── test_api.py
│
└── fixtures/
    ├── sample_paper.pdf
    ├── sample_markdown.md
    └── expected_outputs/
```

## 📚 Next Steps

- **[Workflow & Data Flow](./07-workflow.md)**: Understand how data flows through the system
- **[Configuration](./08-configuration.md)**: Setup and configuration details
- **[Development Guide](./09-development-guide.md)**: Contributing and extending
