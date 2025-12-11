# Overview

## 🎯 What is Paper2Slides?

Paper2Slides is an intelligent document-to-presentation conversion system that transforms research papers, reports, and documents into professional slides and posters automatically. It uses advanced AI techniques including Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and AI image generation to create presentation-ready materials.

## ✨ Key Features

### 1. Universal Document Support
- **File Types**: PDF, Word, Excel, PowerPoint, Markdown
- **Multiple Files**: Process single files or entire directories
- **Batch Processing**: Handle multiple documents simultaneously with unified content extraction

### 2. Intelligent Content Extraction (RAG-Powered)
- **Deep Analysis**: Extracts key insights, figures, tables, and data points with precision
- **Context-Aware**: Understands document structure and relationships between sections
- **Source Traceability**: Maintains links between generated content and original sources
- **Vision Support**: Processes both text and images from documents

### 3. Two Processing Modes

#### Normal Mode (RAG-Based)
- Full document indexing with vector database
- Intelligent retrieval for accurate content selection
- Best for: Long documents, complex papers, multiple files
- Uses: LightRAG for graph-enhanced retrieval

#### Fast Mode (Direct LLM)
- Skips RAG indexing, queries LLM directly
- Embeds images at original positions in markdown
- Best for: Short documents, quick previews, rapid iterations
- Uses: GPT-4o with vision capabilities

### 4. Flexible Output Options

**Slides**
- Short (5-7 slides)
- Medium (8-12 slides)
- Long (13-20 slides)

**Posters**
- Sparse (minimal content)
- Medium (balanced)
- Dense (comprehensive)

### 5. Custom Styling
- **Built-in Styles**: Academic (professional), Doraemon (friendly/colorful)
- **Custom Styles**: Natural language descriptions (e.g., "minimalist with blue theme")
- **AI-Powered**: Uses Gemini 3 Pro Image Preview for generation
- **Style Processing**: LLM interprets and applies custom style requests

### 6. Smart Recovery & Checkpointing
- **Automatic Checkpoints**: Saves progress at each stage
- **Resume Support**: Continue from any interruption point
- **Stage Override**: Jump to specific stages (e.g., change style without re-parsing)
- **No Data Loss**: All intermediate results preserved

### 7. Parallel Processing
- **Concurrent Generation**: Generate multiple slides simultaneously
- **Configurable Workers**: Set worker count (default: 2)
- **Performance Boost**: Significantly faster for multi-slide outputs

## 🏗️ High-Level Architecture

```
Input Documents → RAG Stage → Summary Stage → Plan Stage → Generate Stage → Output
                     ↓            ↓              ↓              ↓
              checkpoint_rag  checkpoint_sum  checkpoint_plan  images/PDF
```

### Pipeline Stages

1. **RAG Stage**: Parse and index documents, run intelligent queries
2. **Summary Stage**: Extract structured content (title, authors, sections, figures, tables)
3. **Plan Stage**: Generate content layout and organization strategy
4. **Generate Stage**: Create high-quality images using AI

Each stage produces checkpoints that enable resumption and stage-specific regeneration.

## 🎨 How It Works (Simple Example)

Let's trace a simple workflow:

```bash
# User runs this command
python -m paper2slides --input paper.pdf --output slides --style doraemon --length medium
```

**What happens internally:**

1. **RAG Stage** (30-60 seconds)
   - Parses PDF to markdown using MinerU
   - If normal mode: Indexes content in vector database
   - Runs queries to extract key information
   - Saves: `checkpoint_rag.json`

2. **Summary Stage** (10-20 seconds)
   - Extracts paper title, authors, affiliations
   - Identifies sections (abstract, intro, methods, etc.)
   - Catalogs all figures and tables
   - Saves: `checkpoint_summary.json`, `summary.md`

3. **Plan Stage** (15-30 seconds)
   - Plans 8-12 slides (medium length)
   - Decides which content goes on each slide
   - Assigns figures/tables to appropriate slides
   - Saves: `checkpoint_plan.json`

4. **Generate Stage** (30-90 seconds)
   - Generates each slide as an image
   - Applies Doraemon style (colorful, friendly)
   - Creates final PDF from slides
   - Saves: `slide_01.png`, `slide_02.png`, ..., `slides.pdf`

**Total Time**: ~2-4 minutes for a typical paper

## 💡 Key Concepts

### RAG (Retrieval-Augmented Generation)
Paper2Slides uses RAG to intelligently extract content from documents:
- **Parsing**: Converts documents to structured markdown
- **Indexing**: Creates searchable knowledge base (normal mode)
- **Querying**: Retrieves relevant information using predefined queries
- **Augmentation**: LLM generates responses based on retrieved context

### Checkpointing System
Every stage saves its results, enabling:
- **Resume**: If interrupted, continue where you left off
- **Regenerate**: Change parameters without redoing work
- **Experiment**: Try different styles/lengths quickly

Example:
```bash
# First run - does all 4 stages
python -m paper2slides --input paper.pdf --output slides --style academic

# Change to doraemon style - only redoes Plan + Generate stages
python -m paper2slides --input paper.pdf --output slides --style doraemon

# Force restart from scratch
python -m paper2slides --input paper.pdf --output slides --from-stage rag
```

### Content Types
- **Paper**: Academic papers with formal structure (default queries focus on research aspects)
- **General**: Any other documents (generates custom queries based on overview)

### Output Types
- **Slides**: Multi-page presentation with sequential flow
- **Poster**: Single-page comprehensive view

## 🔧 Technology Stack

### Core Libraries
- **LightRAG**: Graph-enhanced RAG for intelligent retrieval
- **MinerU**: High-quality PDF/document parsing
- **OpenAI API**: GPT-4o for analysis and planning
- **Gemini 3 Pro Image**: AI-powered image generation

### Backend
- **FastAPI**: RESTful API server
- **Uvicorn**: ASGI web server
- **Python 3.12+**: Core runtime

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **TailwindCSS**: Styling
- **Axios**: API communication

## 🎯 Use Cases

### Academic Research
- Convert papers to conference presentation slides
- Create poster presentations for symposiums
- Generate teaching materials from research papers

### Business Reports
- Transform reports into executive presentations
- Create visual summaries of long documents
- Generate presentation decks from proposals

### Documentation
- Convert technical documentation to training slides
- Create overview posters from detailed docs
- Build presentation materials from markdown files

## 🚀 Next Steps

Now that you understand what Paper2Slides does, continue to:

- **[Architecture](./02-architecture.md)**: Learn about the system design
- **[Pipeline Stages](./03-pipeline-stages.md)**: Deep dive into each processing stage
- **[CLI Usage](./05-cli-usage.md)**: Start using Paper2Slides from command line

## 📊 Performance Characteristics

### Speed
- **Fast Mode**: 1-2 minutes for typical papers
- **Normal Mode**: 2-4 minutes for typical papers
- **Parallel Generation**: 30-50% faster with 2 workers

### Quality
- **Content Accuracy**: High - RAG ensures source traceability
- **Visual Quality**: Professional - AI-generated images at presentation quality
- **Layout**: Adaptive - Content automatically adjusted to fit

### Resource Usage
- **Memory**: 2-4 GB for normal operation
- **Disk**: ~50-200 MB per processed document (includes checkpoints and images)
- **API Calls**: ~20-50 LLM calls per document (depends on mode and complexity)
