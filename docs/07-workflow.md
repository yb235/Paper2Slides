# Workflow & Data Flow

This document traces the complete data flow through Paper2Slides, from input documents to generated presentations. Understanding this flow is essential for debugging, optimizing, and extending the system.

## 🔄 End-to-End Workflow

### Complete Pipeline Flow

```
┌─────────────────┐
│  User Input     │  Files + Configuration
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              Stage 1: RAG (Parse & Index)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Input Document(s)                                      │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────────┐                                      │
│  │ MinerU Parse │ → markdown + images                  │
│  └──────┬───────┘                                      │
│         │                                               │
│         ▼                                               │
│  Fast Mode?                                             │
│    Yes ─→ Direct GPT-4o Queries (with images)         │
│    No  ─→ LightRAG Index → RAG Queries                │
│         │                                               │
│         ▼                                               │
│  checkpoint_rag.json                                    │
│  {rag_results, markdown_paths}                         │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           Stage 2: Summary (Content Extraction)         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  checkpoint_rag.json + markdown files                   │
│       │                                                 │
│       ▼                                                 │
│  ┌────────────────────────┐                            │
│  │ Extract Paper Metadata │ (direct from markdown)     │
│  │ • Title, Authors       │                            │
│  │ • Affiliations         │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  ┌────────────────────────┐                            │
│  │ Extract Content        │ (from RAG results)         │
│  │ • Abstract             │                            │
│  │ • Sections             │                            │
│  │ • Key findings         │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  ┌────────────────────────┐                            │
│  │ Extract Figures/Tables │ (parse markdown)           │
│  │ • Figure IDs + paths   │                            │
│  │ • Table IDs + HTML     │                            │
│  │ • Captions             │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  checkpoint_summary.json + summary.md                   │
│  {content, origin {figures, tables}}                    │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│            Stage 3: Plan (Content Layout)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  checkpoint_summary.json + config                       │
│       │                                                 │
│       ▼                                                 │
│  ┌────────────────────────┐                            │
│  │ Select Prompt Template │                            │
│  │ • Paper vs General     │                            │
│  │ • Slides vs Poster     │                            │
│  │ • Length/Density       │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  ┌────────────────────────┐                            │
│  │ LLM Content Planning   │ (GPT-4o)                   │
│  │ • Decide sections      │                            │
│  │ • Assign content       │                            │
│  │ • Map figures/tables   │                            │
│  │ • Generate titles      │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  checkpoint_plan.json                                   │
│  {plan {sections, metadata}}                            │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│          Stage 4: Generate (Create Images)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  checkpoint_plan.json + origin                          │
│       │                                                 │
│       ▼                                                 │
│  ┌────────────────────────┐                            │
│  │ Process Custom Style   │ (if custom)                │
│  │ • LLM interprets       │                            │
│  │ • Extract elements     │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  For each section:                                      │
│  ┌────────────────────────┐                            │
│  │ Build Image Prompt     │                            │
│  │ • Content text         │                            │
│  │ • Style directives     │                            │
│  │ • Layout hints         │                            │
│  │ • Embed figures        │                            │
│  │ • Table data           │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  ┌────────────────────────┐                            │
│  │ Gemini 3 Pro Generate  │                            │
│  │ • Create image         │                            │
│  │ • Save incrementally   │                            │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  Sequential or Parallel?                                │
│    Sequential → One at a time                           │
│    Parallel   → N workers                               │
│           │                                             │
│           ▼                                             │
│  ┌────────────────────────┐                            │
│  │ Combine to PDF         │ (for slides)               │
│  └────────┬───────────────┘                            │
│           │                                             │
│           ▼                                             │
│  output_dir/{timestamp}/                                │
│  • slide_01.png, slide_02.png, ...                     │
│  • slides.pdf                                           │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Final Output   │  Images + PDF
└─────────────────┘
```

## 📊 Data Transformations

### Stage 1: Document → Structured Queries

**Input**: `paper.pdf`

**Transformation Process**:
1. **Parse**: PDF → Markdown + Images
2. **Index** (normal mode): Markdown → Vector DB + Knowledge Graph
3. **Query**: Questions → Context-aware Answers

**Output Data**:
```json
{
  "rag_results": {
    "paper_info": [{
      "query": "List paper title, authors...",
      "answer": "Title: Deep Learning for NLP\nAuthors: John Doe (MIT)...",
      "mode": "local",
      "success": true
    }],
    "structure": [...],
    "methodology": [...],
    "results": [...],
    "figures_tables": [...]
  },
  "markdown_paths": ["/path/to/paper.md"],
  "input_path": "/path/to/paper.pdf",
  "content_type": "paper",
  "mode": "normal"
}
```

### Stage 2: Queries → Structured Content

**Input**: RAG results (raw query-answer pairs)

**Transformation Process**:
1. **Metadata**: First ~3000 chars of markdown → Title, Authors, Affiliations
2. **Content**: Query answers → Structured sections
3. **Figures**: Markdown parsing → Figure catalog with IDs and paths
4. **Tables**: HTML parsing → Table catalog with IDs and content

**Output Data**:
```json
{
  "content": {
    "title": "Deep Learning for NLP",
    "authors": ["John Doe", "Jane Smith"],
    "abstract": "We propose...",
    "introduction": "NLP has...",
    "methodology": "Our approach...",
    "results": "Experiments show...",
    "conclusion": "We presented...",
    "contributions": ["Novel architecture", "SOTA results"]
  },
  "origin": {
    "figures": [
      {"id": "Figure1", "caption": "Architecture", "path": "/path/image1.png"}
    ],
    "tables": [
      {"id": "Table1", "caption": "Results", "html": "<table>...</table>"}
    ],
    "base_path": "/path/to/output"
  }
}
```

### Stage 3: Content → Layout Plan

**Input**: Structured content + Figures/Tables + Configuration

**Transformation Process**:
1. **Template Selection**: Config → Appropriate prompt template
2. **Context Building**: Content + Figures + Tables → LLM context
3. **LLM Planning**: Context → Organized sections with assignments
4. **Validation**: LLM output → ContentPlan object

**Output Data**:
```json
{
  "plan": {
    "output_type": "slides",
    "sections": [
      {
        "id": "slide_01",
        "title": "Deep Learning for NLP",
        "type": "title",
        "content": "Deep Learning for NLP\n\nJohn Doe, Jane Smith...",
        "figures": [],
        "tables": []
      },
      {
        "id": "slide_02",
        "title": "Problem Statement",
        "type": "content",
        "content": "Natural language processing faces...",
        "figures": [],
        "tables": []
      },
      {
        "id": "slide_03",
        "title": "Proposed Architecture",
        "type": "content",
        "content": "Our model consists of...",
        "figures": [
          {"figure_id": "Figure1", "focus": "Highlight encoder-decoder"}
        ],
        "tables": []
      },
      {
        "id": "slide_04",
        "title": "Experimental Results",
        "type": "results",
        "content": "We evaluated on...",
        "figures": [],
        "tables": [
          {"table_id": "Table1", "extract": "", "focus": "Compare with baselines"}
        ]
      }
    ],
    "metadata": {"total_slides": 8, "figures_used": 2, "tables_used": 1}
  }
}
```

### Stage 4: Plan → Visual Images

**Input**: ContentPlan + Style config

**Transformation Process**:
1. **Style Processing**: Custom description → Structured style parameters
2. **Prompt Building**: Section + Figures + Tables + Style → Image prompt
3. **Image Generation**: Prompt → Image bytes
4. **PDF Creation**: Images → Combined PDF (for slides)

**For Each Section**:
```
Section Data
    ↓
┌────────────────────────────┐
│ Build Prompt               │
│ • Format (slide/poster)    │
│ • Style hints              │
│ • Layout template          │
│ • Content text             │
│ • Figure references        │
│ • Table data               │
│ • Common rules             │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Embed Original Figures     │
│ • Base64 encode            │
│ • Add to prompt content    │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Call Gemini 3 Pro API      │
│ • Multi-modal input        │
│ • Text + Images            │
└────────┬───────────────────┘
         │
         ▼
   Image Bytes (PNG/JPEG)
```

**Output**: Image files + PDF

## 🔀 Conditional Flows

### Fast Mode vs Normal Mode

```
Input Document
    │
    ▼
Parse (MinerU)
    │
    ├──→ Fast Mode
    │     │
    │     ▼
    │   Embed images in markdown content
    │     │
    │     ▼
    │   Direct GPT-4o queries
    │     │
    │     └──→ RAG Results
    │
    └──→ Normal Mode
          │
          ▼
        Index in LightRAG (Vector + Graph)
          │
          ▼
        RAG retrieval queries
          │
          └──→ RAG Results
```

### Content Type Flow

```
Content Type?
    │
    ├──→ "paper"
    │     │
    │     ├─→ Use RAG_PAPER_QUERIES
    │     │   (paper_info, structure, methodology, results, figures_tables)
    │     │
    │     ├─→ extract_paper()
    │     │   (PaperContent with formal sections)
    │     │
    │     └─→ Paper-specific planning prompts
    │
    └──→ "general"
          │
          ├─→ get_general_overview()
          │   generate_general_queries()
          │   (Dynamic queries based on content)
          │
          ├─→ extract_general()
          │   (GeneralContent with flexible structure)
          │
          └─→ General-purpose planning prompts
```

### Output Type Flow

```
Output Type?
    │
    ├──→ "slides"
    │     │
    │     ├─→ Use slides_length parameter (short/medium/long)
    │     │
    │     ├─→ SLIDES_PLANNING_PROMPT
    │     │
    │     ├─→ Generate multiple sections (5-20)
    │     │
    │     └─→ Combine to PDF
    │
    └──→ "poster"
          │
          ├─→ Use poster_density parameter (sparse/medium/dense)
          │
          ├─→ POSTER_PLANNING_PROMPT
          │
          ├─→ Generate single comprehensive section
          │
          └─→ Single image output
```

### Style Processing Flow

```
Style Parameter?
    │
    ├──→ "academic"
    │     │
    │     └─→ Use SLIDE_STYLE_HINTS["academic"]
    │         "Clean, professional, white background..."
    │
    ├──→ "doraemon"
    │     │
    │     └─→ Use SLIDE_STYLE_HINTS["doraemon"]
    │         "Colorful, friendly, character elements..."
    │
    └──→ Custom description
          │
          ▼
        process_custom_style(LLM)
          │
          ▼
        ProcessedStyle {
          style_name: "...",
          color_tone: "...",
          special_elements: "...",
          decorations: "..."
        }
```

## 🔄 Checkpoint Reuse Logic

### Automatic Stage Detection

```python
def detect_start_stage(base_dir, config_dir, config):
    """
    Determine which stage to start from based on:
    1. Existing checkpoints
    2. Configuration changes
    3. Mode changes
    """
    
    # Check mode-specific checkpoints
    mode_dir = get_mode_dir(base_dir, config["fast_mode"])
    rag_checkpoint = mode_dir / "checkpoint_rag.json"
    summary_checkpoint = mode_dir / "checkpoint_summary.json"
    plan_checkpoint = config_dir / "checkpoint_plan.json"
    
    # No RAG checkpoint → start from RAG
    if not rag_checkpoint.exists():
        return "rag"
    
    # No Summary checkpoint → start from Summary
    if not summary_checkpoint.exists():
        return "summary"
    
    # No Plan checkpoint OR config changed → start from Plan
    if not plan_checkpoint.exists() or config_changed(config_dir, config):
        return "plan"
    
    # All checkpoints exist, config same → start from Generate
    return "generate"
```

### Configuration Change Detection

```python
def config_changed(config_dir, new_config):
    """Check if config differs from what was used in plan."""
    state = load_state(config_dir)
    if not state:
        return True
    
    old_config = state.get("config", {})
    
    # These changes require re-planning
    plan_affecting_keys = [
        "output_type",      # slides → poster
        "style",            # academic → doraemon
        "slides_length",    # short → long
        "poster_density",   # sparse → dense
        "custom_style"      # style description changed
    ]
    
    for key in plan_affecting_keys:
        if old_config.get(key) != new_config.get(key):
            return True
    
    return False
```

### Checkpoint Reuse Scenarios

**Scenario 1: Change Style**
```
Existing: checkpoint_rag.json ✓, checkpoint_summary.json ✓, checkpoint_plan.json ✓
New Config: style changed from "doraemon" to "academic"
→ Start from: plan
→ Reuse: RAG + Summary
→ Regenerate: Plan + Generate
```

**Scenario 2: Change Length**
```
Existing: checkpoint_rag.json ✓, checkpoint_summary.json ✓, checkpoint_plan.json ✓
New Config: length changed from "short" to "long"
→ Start from: plan
→ Reuse: RAG + Summary
→ Regenerate: Plan + Generate
```

**Scenario 3: Same Config**
```
Existing: checkpoint_rag.json ✓, checkpoint_summary.json ✓, checkpoint_plan.json ✓
New Config: (no changes)
→ Start from: generate
→ Reuse: RAG + Summary + Plan
→ Regenerate: Generate only
```

**Scenario 4: Switch Mode**
```
Existing: normal/checkpoint_rag.json ✓, normal/checkpoint_summary.json ✓
New Config: fast_mode=true
→ Start from: rag
→ Reuse: none (different mode path)
→ Regenerate: All stages
```

## 🔐 API Request Flow

### Web Interface Request

```
Browser
    │
    ▼
┌──────────────────────────────┐
│ User uploads files           │
│ Selects configuration        │
│ Clicks "Generate"            │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ POST /api/chat               │
│ • FormData with files        │
│ • Config parameters          │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ SessionManager               │
│ • Check if session running   │
│ • Start new session          │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Save uploaded files          │
│ • UUID-based filenames       │
│ • To sources/uploads/        │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Start Background Task        │
│ • run_pipeline()             │
│ • With session_id            │
│ • With session_manager       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Return immediately           │
│ • session_id                 │
│ • uploaded_files info        │
└────────┬─────────────────────┘
         │
         ▼
Browser receives response
    │
    ▼
┌──────────────────────────────┐
│ Poll state.json              │
│ • Every 2 seconds            │
│ • Update progress bar        │
│ • Check for completion       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Display results              │
│ • Show generated slides      │
│ • PDF download link          │
└──────────────────────────────┘
```

### Background Pipeline Execution

```
Background Task
    │
    ▼
┌──────────────────────────────┐
│ run_pipeline()               │
│ • base_dir                   │
│ • config_dir                 │
│ • config                     │
│ • from_stage (auto-detected) │
│ • session_id                 │
│ • session_manager            │
└────────┬─────────────────────┘
         │
         ▼
For each stage in STAGES:
    │
    ├─→ Check cancellation
    │   (session_manager.is_cancelled())
    │
    ├─→ Update state: "running"
    │   (save_state())
    │
    ├─→ Execute stage
    │   (run_rag_stage, run_summary_stage, etc.)
    │
    ├─→ Update state: "completed"
    │   (save_state())
    │
    └─→ Continue to next stage
```

## 💾 State Persistence

### State File Updates

```
Pipeline Start
    │
    ▼
Create/Load state.json
    │
    └─→ {
          session_id: "...",
          config: {...},
          stages: {
            rag: "pending",
            summary: "pending",
            plan: "pending",
            generate: "pending"
          }
        }
    │
    ▼
Begin RAG Stage
    │
    └─→ Update state: stages.rag = "running"
        Save state.json
    │
    ▼
RAG Complete
    │
    └─→ Update state: stages.rag = "completed"
        Save state.json
        Save checkpoint_rag.json
    │
    ▼
Begin Summary Stage
    │
    └─→ Update state: stages.summary = "running"
        Save state.json
    │
    ▼
Summary Complete
    │
    └─→ Update state: stages.summary = "completed"
        Save state.json
        Save checkpoint_summary.json
    │
    ▼
... (continue for all stages)
```

## 🚦 Error Handling Flow

```
Stage Execution
    │
    ├─→ Success
    │     │
    │     ├─→ Save checkpoint
    │     ├─→ Update state: "completed"
    │     └─→ Continue to next stage
    │
    └─→ Error
          │
          ├─→ Catch exception
          ├─→ Update state: "failed"
          ├─→ Save state with error message
          ├─→ Log error details
          └─→ Stop pipeline execution
```

### Cancellation Flow

```
User clicks "Cancel"
    │
    ▼
POST /api/cancel/{session_id}
    │
    ▼
session_manager.cancel_session(session_id)
    │
    └─→ Add to cancelled_sessions set
    │
    ▼
Pipeline checks before each stage:
    │
    └─→ if session_manager.is_cancelled(session_id):
          │
          ├─→ Update state: stage = "cancelled"
          ├─→ Save state with error: "Cancelled by user"
          └─→ Raise exception to stop pipeline
```

## 📚 Next Steps

- **[Configuration](./08-configuration.md)**: Environment and settings
- **[Development Guide](./09-development-guide.md)**: Contributing and extending
- **[Troubleshooting](./10-troubleshooting.md)**: Common issues and solutions
