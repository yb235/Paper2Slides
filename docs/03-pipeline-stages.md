# Pipeline Stages

This document provides an in-depth explanation of each stage in the Paper2Slides pipeline. Understanding these stages is crucial for debugging, extending, or optimizing the system.

## 🔄 Pipeline Overview

Paper2Slides processes documents through four sequential stages:

```
1. RAG Stage      → Parse & Index documents, run intelligent queries
2. Summary Stage  → Extract structured content from RAG results
3. Plan Stage     → Generate content layout and organization
4. Generate Stage → Create final images and PDF
```

Each stage:
- Takes inputs from previous stages (via checkpoints)
- Performs specific transformations
- Saves outputs to checkpoints
- Can be rerun independently

## 🔍 Stage 1: RAG (Retrieval-Augmented Generation)

**File**: `paper2slides/core/stages/rag_stage.py`

**Purpose**: Parse input documents and extract relevant information through intelligent querying.

### 1.1 Inputs

- **From Config**:
  - `input_path`: File or directory path
  - `content_type`: "paper" or "general"
  - `fast_mode`: Boolean (True = fast mode, False = normal mode)

### 1.2 Process Flow

#### Fast Mode Process

```
Input Document(s)
      │
      ▼
┌──────────────────┐
│  Batch Parsing   │  MinerU converts to markdown
│  (MinerU)        │  Images extracted and referenced
└────────┬─────────┘
         │ markdown files with image references
         ▼
┌──────────────────┐
│  Image Embedding │  Base64 encode images
│  (at original    │  Maintain document positions
│   positions)     │
└────────┬─────────┘
         │ content_parts = [text, image, text, image, ...]
         ▼
┌──────────────────┐
│  Direct GPT-4o   │  Vision-enabled queries
│  Queries         │  All images in context
└────────┬─────────┘
         │
         ▼
   query_results
```

**Key Function**: `_run_fast_queries_by_category()`
```python
async def _run_fast_queries_by_category(
    client,
    markdown_content: str,
    markdown_paths: List[str],
    queries_by_category: Dict[str, List[str]],
    model: str = "gpt-4o",
    max_concurrency: int = 10,
) -> Dict[str, List[Dict]]
```

**Process**:
1. Read all markdown files
2. For each file, find image references using regex:
   - Markdown format: `![alt](path/to/image.jpg)`
   - MinerU format: `Image Path: path/to/image.jpg`
3. Encode images to base64 at their original positions
4. Build message structure:
   ```python
   {
     "role": "user",
     "content": [
       {"type": "text", "text": "Document Content\n\n"},
       {"type": "text", "text": "...text before image..."},
       {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
       {"type": "text", "text": "...text after image..."},
       # ... more content
       {"type": "text", "text": "\n\nQuestion\n\n{query}"}
     ]
   }
   ```
5. Execute queries concurrently (semaphore-controlled)
6. Return categorized results

**Advantages**:
- No indexing overhead (~30-60s saved)
- Images at original positions (better context)
- Good for short documents that fit in LLM context
- Faster iteration during development

#### Normal Mode Process

```
Input Document(s)
      │
      ▼
┌──────────────────┐
│  Batch Parsing   │  MinerU converts to markdown
│  (MinerU)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RAG Indexing    │  LightRAG creates:
│  (LightRAG)      │  - Vector embeddings
│                  │  - Knowledge graph
│                  │  - Searchable index
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  RAG Queries     │  Retrieve relevant chunks
│  (by category)   │  Query modes: local/global/hybrid/mix
└────────┬─────────┘
         │
         ▼
   query_results
```

**Key Component**: `RAGClient` from `paper2slides/rag/client.py`

```python
async with RAGClient(config=rag_config) as rag:
    # Index documents
    batch_result = await rag.index_batch(
        file_paths=[input_path],
        output_dir=str(output_dir),
        recursive=True,
        show_progress=True
    )
    
    # Query by category
    rag_results = await rag.batch_query_by_category(
        queries_by_category=RAG_PAPER_QUERIES,
        modes_by_category=RAG_QUERY_MODES,
    )
```

**Query Categories for Papers**:
```python
RAG_PAPER_QUERIES = {
    "paper_info": [
        "List the paper title, author names and their institutional affiliations.",
    ],
    "structure": [
        "What are the main sections of this paper?",
        "Outline the logical structure and flow of the paper.",
    ],
    "methodology": [
        "What research methodology is used in this paper?",
        "What are the key technical approaches or algorithms?",
    ],
    "results": [
        "What are the main experimental results and findings?",
        "What metrics or evaluations are reported?",
    ],
    "figures_tables": [
        "Describe all figures and tables in the paper.",
        "What visualizations are presented?",
    ],
}
```

**Query Modes**:
- `local`: Keyword-based retrieval (fast, specific)
- `global`: Document-level overview (broad understanding)
- `hybrid`: Combination of local and global
- `mix`: Automatically select best mode per query

**Advantages**:
- Handles long documents (beyond LLM context window)
- Better retrieval for multi-file inputs
- Graph-enhanced understanding
- More accurate for complex papers

### 1.3 Output

**Checkpoint**: `checkpoint_rag.json` (saved in mode-specific directory: `fast/` or `normal/`)

```json
{
  "rag_results": {
    "paper_info": [
      {
        "query": "List the paper title...",
        "answer": "Title: Deep Learning for NLP\nAuthors: John Doe (MIT), Jane Smith (Stanford)",
        "mode": "fast_direct_with_vision" | "local" | "global" | "hybrid" | "mix",
        "success": true
      }
    ],
    "structure": [...],
    "methodology": [...],
    "results": [...],
    "figures_tables": [...]
  },
  "markdown_paths": [
    "/path/to/output/file.md"
  ],
  "input_path": "/path/to/input/paper.pdf",
  "content_type": "paper",
  "mode": "fast" | "normal"
}
```

### 1.4 Key Implementation Details

**Image Encoding** (`_encode_image_to_base64()`):
```python
def _encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string
```

**MIME Type Detection** (`_get_image_mime_type()`):
```python
def _get_image_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        # ... more types
    }
    return mime_types.get(ext, 'image/jpeg')
```

**Concurrent Query Execution**:
```python
semaphore = asyncio.Semaphore(max_concurrency)

async def query_one(category, idx, query):
    async with semaphore:
        # Execute query
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(...)
        )
        return (category, idx, result)

# Execute all queries concurrently
all_results = await asyncio.gather(*tasks)
```

### 1.5 Performance Characteristics

**Fast Mode**:
- Time: ~30-60 seconds for typical paper
- API Calls: ~20-30 GPT-4o calls
- Cost: Higher per-call (vision model) but fewer calls
- Memory: Higher (all images in memory)

**Normal Mode**:
- Time: ~60-120 seconds for typical paper
- API Calls: ~30-40 calls (indexing + queries)
- Cost: Lower per-call but more calls
- Memory: Lower (streaming processing)
- Storage: Additional (~10-50 MB for index)

---

## 📊 Stage 2: Summary

**File**: `paper2slides/core/stages/summary_stage.py`

**Purpose**: Extract structured content from RAG results and identify figures/tables.

### 2.1 Inputs

- **From RAG Checkpoint**:
  - `rag_results`: Query responses by category
  - `markdown_paths`: List of processed markdown files
  - `content_type`: "paper" or "general"

### 2.2 Process Flow

```
RAG Results
      │
      ▼
┌──────────────────┐
│  Metadata        │  Extract from markdown directly
│  Extraction      │  (bypasses RAG for accuracy)
│  (Direct)        │  • Title, authors, affiliations
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Content         │  LLM structures RAG responses:
│  Extraction      │  • Abstract
│  (LLM)           │  • Sections (intro, methods, etc.)
│                  │  • Key findings
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Figure & Table  │  Parse markdown:
│  Extraction      │  • Regex for figures
│  (Regex)         │  • HTML tables
│                  │  • Captions
└────────┬─────────┘
         │
         ▼
   Structured Content
```

### 2.3 Content Extraction

#### Paper Metadata (Direct from Markdown)

**Function**: `extract_paper_metadata_from_markdown()`

```python
async def extract_paper_metadata_from_markdown(
    markdown_paths: List[str],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
    max_chars_per_file: int = 3000
) -> str
```

**Process**:
1. Read first N characters from each markdown file
2. Send to LLM with extraction prompt
3. LLM identifies: title, authors, affiliations
4. Returns formatted metadata string

**Why Direct Extraction?**
- More reliable than RAG (exact text match)
- Metadata usually at document start
- Faster (no RAG overhead)
- Higher accuracy

#### Content Structure (from RAG Results)

**Function**: `extract_paper()` for papers, `extract_general()` for general docs

```python
async def extract_paper(
    rag_results: Dict[str, List[Dict]],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini",
    parallel: bool = True,
    max_concurrency: int = 5,
) -> PaperContent
```

**Output**: `PaperContent` dataclass
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
```

**Extraction Process**:
1. For each category in RAG results, aggregate query responses
2. Use LLM to structure raw responses into clean sections
3. Extract lists (authors, contributions) from text
4. Run extractions in parallel for speed

#### Figure & Table Extraction

**Function**: `extract_tables_and_figures()` from `paper2slides/summary/extractors/`

```python
def extract_tables_and_figures(markdown_path: str) -> OriginalElements
```

**Figure Extraction**:
- **Pattern**: `![caption](path/to/image.jpg)` or `Image Path: path`
- **Extracts**: Caption, image path
- **Assigns**: Figure IDs (Figure 1, Figure 2, etc.)

**Table Extraction**:
- **Pattern**: HTML tables in markdown: `<table>...</table>`
- **Extracts**: Caption (from preceding text), HTML content
- **Assigns**: Table IDs (Table 1, Table 2, etc.)

**Multi-Document Handling**:
```python
if len(markdown_paths) > 1:
    doc_prefix = f"Doc{i+1}"
    # Prefix IDs to avoid conflicts
    table.table_id = f"{doc_prefix}_{table.table_id}"  # e.g., "Doc1_Table1"
    figure.figure_id = f"{doc_prefix}_{figure.figure_id}"  # e.g., "Doc2_Figure1"
```

### 2.4 Output

**Checkpoint**: `checkpoint_summary.json`

```json
{
  "content_type": "paper",
  "content": {
    "title": "Deep Learning for Natural Language Processing",
    "authors": ["John Doe", "Jane Smith"],
    "affiliations": "MIT, Stanford University",
    "abstract": "We propose a novel approach...",
    "introduction": "Natural language processing has...",
    "methodology": "Our method consists of...",
    "results": "Experiments show that...",
    "discussion": "The results indicate...",
    "conclusion": "In this work, we presented...",
    "contributions": [
      "Novel architecture for NLP",
      "State-of-the-art results on benchmarks"
    ]
  },
  "origin": {
    "tables": [
      {
        "id": "Table1",
        "caption": "Performance comparison on benchmark datasets",
        "html": "<table><tr><th>Model</th><th>Accuracy</th></tr>...</table>"
      }
    ],
    "figures": [
      {
        "id": "Figure1",
        "caption": "Architecture overview of the proposed model",
        "path": "/path/to/output/image_001.png"
      }
    ],
    "base_path": "/path/to/output"
  },
  "markdown_paths": ["/path/to/output/paper.md"]
}
```

**Summary Markdown**: `summary.md` (human-readable version)

```markdown
# Deep Learning for Natural Language Processing

## Authors
- John Doe (MIT)
- Jane Smith (Stanford University)

## Abstract
We propose a novel approach...

## Introduction
Natural language processing has...

...

## Figures
- Figure 1: Architecture overview
- Figure 2: Performance comparison

## Tables
- Table 1: Results on benchmark datasets
```

### 2.5 Key Implementation Details

**Parallel Extraction**:
```python
tasks = []
for category, responses in rag_results.items():
    task = extract_section(category, responses)
    tasks.append(task)

results = await asyncio.gather(*tasks)
```

**Table HTML Parsing**:
```python
# Find all HTML tables
tables = re.findall(r'<table.*?</table>', markdown_content, re.DOTALL)

# Look for caption in preceding text
caption_match = re.search(r'(?:Table \d+[:.])([^\n]+)', preceding_text)
```

**Figure Path Resolution**:
```python
# Handle relative paths
if not Path(image_path).is_absolute():
    image_path = str(Path(markdown_base_path) / image_path)
```

---

## 📋 Stage 3: Plan

**File**: `paper2slides/core/stages/plan_stage.py`

**Purpose**: Generate content layout and organization strategy for slides/poster.

### 3.1 Inputs

- **From Summary Checkpoint**:
  - `content`: Structured paper/general content
  - `origin`: Figures and tables catalog
- **From Config**:
  - `output_type`: "slides" or "poster"
  - `slides_length`: "short", "medium", "long"
  - `poster_density`: "sparse", "medium", "dense"
  - `style`: "academic", "doraemon", or custom
  - `custom_style`: Custom style description (if provided)

### 3.2 Process Flow

```
Summary + Origin + Config
      │
      ▼
┌──────────────────┐
│  Prepare Input   │  Build GenerationInput
│                  │  • Config parameters
│                  │  • Content structure
│                  │  • Figures/tables catalog
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Select Prompt   │  Based on:
│  Template        │  • Content type (paper/general)
│                  │  • Output type (slides/poster)
│                  │  • Density/length setting
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  LLM Planning    │  GPT-4o generates:
│  (GPT-4o)        │  • Section titles
│                  │  • Content for each section
│                  │  • Figure/table assignments
│                  │  • Ordering and flow
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Parse & Validate│  Parse JSON response
│                  │  Build ContentPlan object
└────────┬─────────┘
         │
         ▼
    Content Plan
```

### 3.3 Content Planning

**Class**: `ContentPlanner` from `paper2slides/generator/content_planner.py`

```python
class ContentPlanner:
    def plan(self, gen_input: GenerationInput) -> ContentPlan
```

**Planning Process**:

1. **Select Prompt Template**:
   ```python
   if content_type == "paper":
       if output_type == "slides":
           prompt = PAPER_SLIDES_PLANNING_PROMPT
       else:  # poster
           prompt = PAPER_POSTER_PLANNING_PROMPT
   else:  # general
       if output_type == "slides":
           prompt = GENERAL_SLIDES_PLANNING_PROMPT
       else:
           prompt = GENERAL_POSTER_PLANNING_PROMPT
   ```

2. **Build Context**:
   ```python
   context = {
       "content": content.to_dict(),
       "figures": [{"id": f.figure_id, "caption": f.caption} for f in figures],
       "tables": [{"id": t.table_id, "caption": t.caption} for t in tables],
       "config": {
           "length": "medium",  # or "short", "long"
           "density": "medium",  # for posters
           "style": "academic"
       }
   }
   ```

3. **LLM Call**:
   ```python
   response = client.chat.completions.create(
       model="gpt-4o",
       messages=[{"role": "user", "content": prompt.format(**context)}],
       response_format={"type": "json_object"},
   )
   ```

4. **Parse Response**:
   ```python
   plan_dict = json.loads(response.choices[0].message.content)
   
   sections = []
   for s in plan_dict["sections"]:
       section = Section(
           id=s["id"],
           title=s["title"],
           section_type=s["type"],
           content=s["content"],
           tables=[TableRef(**t) for t in s.get("tables", [])],
           figures=[FigureRef(**f) for f in s.get("figures", [])],
       )
       sections.append(section)
   ```

### 3.4 Prompt Templates

Prompts are in `paper2slides/prompts/content_planning.py`

**Example: Paper Slides Planning Prompt** (simplified):

```
You are an expert at creating academic presentation slides from research papers.

Given the following paper content:
{content}

Available figures:
{figures}

Available tables:
{tables}

Create a {length} slide deck (short=5-7, medium=8-12, long=13-20 slides).

Output JSON format:
{
  "sections": [
    {
      "id": "slide_01",
      "title": "Title Slide",
      "type": "title",
      "content": "[Title]\n[Authors]\n[Affiliations]",
      "figures": [],
      "tables": []
    },
    {
      "id": "slide_02",
      "title": "Research Problem",
      "type": "content",
      "content": "Brief description of the problem...",
      "figures": [{"figure_id": "Figure1", "focus": "highlight architecture"}],
      "tables": []
    },
    ...
  ]
}

Guidelines:
- Start with title slide
- Include key contributions
- Show important figures/tables
- End with conclusion/future work
- Balance text and visuals
```

**Density Guidelines (for Posters)**:
- **Sparse**: Minimal text, focus on visuals, ~3-5 main sections
- **Medium**: Balanced text/visuals, ~5-8 sections
- **Dense**: Comprehensive content, ~8-12 sections

### 3.5 Output

**Checkpoint**: `checkpoint_plan.json`

```json
{
  "plan": {
    "output_type": "slides",
    "sections": [
      {
        "id": "slide_01",
        "title": "Deep Learning for NLP",
        "type": "title",
        "content": "Deep Learning for Natural Language Processing\n\nJohn Doe, Jane Smith\nMIT, Stanford University",
        "tables": [],
        "figures": []
      },
      {
        "id": "slide_02",
        "title": "Introduction",
        "type": "content",
        "content": "Natural language processing...\n• Challenge 1\n• Challenge 2",
        "tables": [],
        "figures": []
      },
      {
        "id": "slide_03",
        "title": "Proposed Architecture",
        "type": "content",
        "content": "Our method consists of...",
        "tables": [],
        "figures": [
          {
            "figure_id": "Figure1",
            "focus": "Highlight the encoder-decoder structure"
          }
        ]
      },
      {
        "id": "slide_04",
        "title": "Results",
        "type": "content",
        "content": "Experimental results demonstrate...",
        "tables": [
          {
            "table_id": "Table1",
            "extract": "Show only accuracy columns",
            "focus": "Compare with baseline"
          }
        ],
        "figures": []
      }
    ],
    "metadata": {
      "total_slides": 8,
      "figures_used": 2,
      "tables_used": 1
    }
  },
  "origin": {...},
  "content_type": "paper"
}
```

### 3.6 Section Types

- **title**: Title slide with authors/affiliations
- **content**: Regular content slide
- **methods**: Methodology-focused slide
- **results**: Results/findings slide
- **conclusion**: Concluding slide

### 3.7 Figure/Table References

**TableRef**:
```python
@dataclass
class TableRef:
    table_id: str           # "Table1"
    extract: str = ""       # "Show only accuracy columns" (optional)
    focus: str = ""         # "Emphasize best results" (optional)
```

**FigureRef**:
```python
@dataclass
class FigureRef:
    figure_id: str          # "Figure1"
    focus: str = ""         # "Highlight encoder component" (optional)
```

These provide hints to the image generator about which parts to emphasize.

---

## 🎨 Stage 4: Generate

**File**: `paper2slides/core/stages/generate_stage.py`

**Purpose**: Generate final images for slides/poster using AI image generation.

### 4.1 Inputs

- **From Plan Checkpoint**:
  - `plan`: Complete content plan with sections
  - `origin`: Figures and tables (for embedding)
- **From Summary Checkpoint**:
  - `content`: Original content for context
- **From Config**:
  - `output_type`: "slides" or "poster"
  - `style`: Style configuration
  - `max_workers`: Parallel generation worker count

### 4.2 Process Flow

```
Plan + Origin + Config
      │
      ▼
┌──────────────────┐
│  Style           │  If custom style:
│  Processing      │  • LLM interprets description
│  (Optional)      │  • Extracts color tone, elements
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Prompt          │  For each section:
│  Generation      │  • Build image generation prompt
│                  │  • Add content text
│                  │  • Add figure/table references
│                  │  • Add style directives
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Image           │  Gemini 3 Pro generates:
│  Generation      │  • Sequential or parallel
│  (AI)            │  • Save callback after each
│                  │  • Progress tracking
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  PDF Creation    │  For slides:
│  (Optional)      │  • Combine images into PDF
│                  │  • Maintain order
└────────┬─────────┘
         │
         ▼
   Output Directory
```

### 4.3 Image Generation

**Class**: `ImageGenerator` from `paper2slides/generator/image_generator.py`

```python
class ImageGenerator:
    def generate(
        self,
        plan: ContentPlan,
        gen_input: GenerationInput,
        max_workers: int = 1,
        save_callback = None,
    ) -> List[GeneratedImage]
```

#### Style Processing

For custom styles, LLM processes user description:

```python
def process_custom_style(client, user_style, model) -> ProcessedStyle:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": STYLE_PROCESS_PROMPT}],
        response_format={"type": "json_object"},
    )
    return ProcessedStyle(
        style_name="...",      # e.g., "Cyberpunk with neon aesthetic"
        color_tone="...",      # e.g., "Dark background with neon accents"
        special_elements="...", # e.g., "Holographic UI elements"
        decorations="...",     # e.g., "Grid patterns"
        valid=True
    )
```

**Built-in Styles**:
- **Academic**: Clean, professional, white background
- **Doraemon**: Colorful, friendly, cartoon character elements

#### Prompt Construction

For each section, build a detailed image generation prompt:

```python
def build_section_prompt(section, config, figures, tables):
    prompt_parts = []
    
    # 1. Format directive
    if output_type == "slides":
        prompt_parts.append(FORMAT_SLIDE)  # "Create a presentation slide..."
    else:
        prompt_parts.append(FORMAT_POSTER)  # "Create a research poster..."
    
    # 2. Style directives
    if style == "academic":
        prompt_parts.append(SLIDE_STYLE_HINTS["academic"])
    elif style == "doraemon":
        prompt_parts.append(SLIDE_STYLE_HINTS["doraemon"])
    elif custom_style:
        prompt_parts.append(f"Style: {processed_style.style_name}")
        prompt_parts.append(f"Color tone: {processed_style.color_tone}")
    
    # 3. Layout hints
    if section.section_type == "title":
        layout = SLIDE_LAYOUTS_ACADEMIC["title"]
    else:
        layout = SLIDE_LAYOUTS_ACADEMIC["content"]
    prompt_parts.append(layout)
    
    # 4. Content
    prompt_parts.append(f"Title: {section.title}")
    prompt_parts.append(f"Content:\n{section.content}")
    
    # 5. Figures
    for fig_ref in section.figures:
        fig = figures_index[fig_ref.figure_id]
        prompt_parts.append(f"Figure {fig.figure_id}: {fig.caption}")
        if fig_ref.focus:
            prompt_parts.append(f"Focus: {fig_ref.focus}")
        # Note: Actual image embedding happens in API call
    
    # 6. Tables
    for table_ref in section.tables:
        table = tables_index[table_ref.table_id]
        prompt_parts.append(f"Table {table.table_id}: {table.caption}")
        if table_ref.extract:
            prompt_parts.append(f"Extract: {table_ref.extract}")
        if table_ref.focus:
            prompt_parts.append(f"Focus: {table_ref.focus}")
        # HTML content converted to text representation
    
    # 7. Common rules
    prompt_parts.append(SLIDE_COMMON_STYLE_RULES)
    prompt_parts.append(CONSISTENCY_HINT)
    
    return "\n\n".join(prompt_parts)
```

#### API Call

```python
def generate_one_image(prompt, figures_to_embed):
    # Prepare message content
    content_parts = [{"type": "text", "text": prompt}]
    
    # Embed referenced figures
    for fig in figures_to_embed:
        with open(fig.image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_data}"}
        })
    
    # Call image generation API
    response = client.chat.completions.create(
        model="google/gemini-3-pro-image-preview",
        messages=[{"role": "user", "content": content_parts}],
        max_tokens=16384,  # For image output
    )
    
    # Extract image from response
    # (Implementation depends on API format)
    return image_data
```

#### Parallel Generation

```python
if max_workers > 1:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for section in plan.sections:
            future = executor.submit(generate_one_image, section, ...)
            futures.append((section.id, future))
        
        for section_id, future in futures:
            image = future.result()
            if save_callback:
                save_callback(image, index, total)
            images.append(image)
else:
    # Sequential generation
    for section in plan.sections:
        image = generate_one_image(section, ...)
        if save_callback:
            save_callback(image, index, total)
        images.append(image)
```

### 4.4 Output

**Images**: `output_dir/<timestamp>/`
```
slide_01.png  (or .jpg, .webp depending on API)
slide_02.png
slide_03.png
...
```

**PDF** (for slides only): `output_dir/<timestamp>/slides.pdf`
```python
def save_images_as_pdf(images, pdf_path):
    from reportlab.pdfgen import canvas
    from PIL import Image as PILImage
    
    # Create PDF with proper page sizes
    # Add each image as a page
    # Save combined PDF
```

### 4.5 Key Implementation Details

**Incremental Saving**:
```python
def save_image_callback(img, index, total):
    ext = ext_map.get(img.mime_type, ".png")
    filepath = output_subdir / f"{img.section_id}{ext}"
    with open(filepath, "wb") as f:
        f.write(img.image_data)
    logger.info(f"  [{index+1}/{total}] Saved: {filepath.name}")

# Pass callback to generator
images = generator.generate(plan, gen_input, save_callback=save_image_callback)
```

**Figure Embedding**:
Original figures are embedded in prompts to maintain visual consistency:
```python
figures_to_embed = plan.get_section_figures(section)
for fig_info, focus_hint in figures_to_embed:
    # Read and encode figure
    # Add to prompt content
```

**Table Rendering**:
HTML tables are converted to text representation for the prompt:
```python
def html_table_to_text(html):
    # Parse HTML table
    # Convert to plain text with proper alignment
    # Return formatted string
```

### 4.6 Performance

**Sequential** (max_workers=1):
- Time: ~10-15 seconds per image
- Total: ~2-3 minutes for 8-slide deck
- Memory: Low
- Reliability: High (no race conditions)

**Parallel** (max_workers=2):
- Time: ~6-8 seconds per image (amortized)
- Total: ~1-2 minutes for 8-slide deck
- Memory: Moderate
- Speedup: ~40-50%

**Parallel** (max_workers=4+):
- Marginal returns (API rate limits)
- Higher memory usage
- Recommended: max_workers=2 for optimal balance

---

## 🔄 Stage Interactions and Dependencies

### Forward Dependencies

```
RAG ──────────────┐
  │               │
  │ (rag_results) │
  └──────────────▶│
                  │
              SUMMARY ───────────┐
                  │              │
                  │ (content +   │
                  │  origin)     │
                  └─────────────▶│
                                 │
                             PLAN ──────────┐
                                 │          │
                                 │ (plan +  │
                                 │  origin) │
                                 └─────────▶│
                                            │
                                        GENERATE
                                            │
                                            ▼
                                        Output
```

### Checkpoint Reuse

```
Scenario: Change Style
  - Reuse: checkpoint_rag.json, checkpoint_summary.json
  - Regenerate: Plan Stage, Generate Stage
  
Scenario: Change Length/Density
  - Reuse: checkpoint_rag.json, checkpoint_summary.json
  - Regenerate: Plan Stage, Generate Stage

Scenario: Change to Fast Mode
  - Regenerate: All stages (different mode path)

Scenario: Add More Slides
  - Reuse: checkpoint_rag.json, checkpoint_summary.json
  - Regenerate: Plan Stage (with new length), Generate Stage
```

### Error Recovery

Each stage can fail independently:

```python
try:
    result = await run_stage()
    state["stages"][stage] = "completed"
except Exception as e:
    state["stages"][stage] = "failed"
    state["error"] = str(e)
    # Save state and stop
```

Resume from failed stage:
```bash
# Automatically detects last completed stage
python -m paper2slides --input paper.pdf --output slides

# Or force specific stage
python -m paper2slides --input paper.pdf --output slides --from-stage summary
```

---

## 💡 Best Practices

### 1. When to Use Fast Mode
✅ **Use Fast Mode When**:
- Document is short (< 20 pages)
- Quick iteration needed
- Single file with few images
- Testing/development

❌ **Avoid Fast Mode When**:
- Document is long (> 50 pages)
- Multiple files to process together
- Many high-resolution images
- Production quality needed

### 2. Optimizing Quality

**For Better Content Extraction**:
- Use normal mode for complex papers
- Ensure good-quality input PDFs
- Provide complete documents (not excerpts)

**For Better Image Generation**:
- Be specific with custom styles
- Use appropriate length/density settings
- Provide high-quality original figures

### 3. Performance Optimization

**Faster Processing**:
```bash
# Fast mode + parallel generation
python -m paper2slides --input paper.pdf --fast --parallel 2
```

**Quality Focus**:
```bash
# Normal mode + sequential generation
python -m paper2slides --input paper.pdf
```

### 4. Debugging

**Check Intermediate Results**:
1. Review `checkpoint_rag.json` for query quality
2. Read `summary.md` for content accuracy
3. Inspect `checkpoint_plan.json` for layout
4. Test individual stages with `--from-stage`

**Common Issues**:
- RAG queries returning empty: Check document parsing quality
- Missing figures: Verify image paths in markdown
- Poor layout: Adjust length/density settings
- Style not applied: Check custom style processing

---

## 📚 Next Steps

- **[API Reference](./04-api-reference.md)**: Learn about HTTP endpoints
- **[CLI Usage](./05-cli-usage.md)**: Master command-line options
- **[Code Structure](./06-code-structure.md)**: Understand codebase organization
