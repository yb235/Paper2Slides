# CLI Usage

Complete guide to using Paper2Slides from the command line.

## 🚀 Quick Start

```bash
# Basic usage - generate slides from a paper
python -m paper2slides --input paper.pdf --output slides

# Generate poster with custom style
python -m paper2slides --input paper.pdf --output poster --style "minimalist blue theme"

# Fast mode with parallel generation
python -m paper2slides --input paper.pdf --output slides --fast --parallel 2
```

## 📖 Command Syntax

```bash
python -m paper2slides [OPTIONS]
```

## 🎛️ Command-Line Options

### Required Options

#### `--input, -i PATH`
Input file or directory path.

**Accepts**:
- Single file: `paper.pdf`, `document.docx`, `report.md`
- Directory: `papers/` (processes all supported files)
- Relative or absolute paths

**Examples**:
```bash
# Single file (relative path)
python -m paper2slides --input paper.pdf --output slides

# Single file (absolute path)
python -m paper2slides --input /home/user/documents/paper.pdf --output slides

# Directory (processes all files)
python -m paper2slides --input ./papers/ --output slides

# Multiple files (via directory)
python -m paper2slides --input ./research_papers/ --output slides
```

**Supported File Types**:
- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Microsoft Excel (`.xlsx`)
- Microsoft PowerPoint (`.pptx`)
- Markdown (`.md`)

---

### Output Type Options

#### `--output TYPE`
Output type: `slides` or `poster`.

**Default**: `poster`

**Options**:
- `slides`: Multi-page presentation deck
- `poster`: Single-page research poster

**Examples**:
```bash
# Generate slides
python -m paper2slides --input paper.pdf --output slides

# Generate poster
python -m paper2slides --input paper.pdf --output poster
```

---

### Content Type Options

#### `--content TYPE`
Content type: `paper` or `general`.

**Default**: `paper`

**Options**:
- `paper`: Academic/research paper (uses paper-specific queries and templates)
- `general`: General document (uses flexible content extraction)

**Examples**:
```bash
# Academic paper
python -m paper2slides --input research.pdf --content paper --output slides

# Business report
python -m paper2slides --input report.pdf --content general --output slides
```

**Differences**:

| Aspect | Paper | General |
|--------|-------|---------|
| Queries | Paper-specific (methodology, results, etc.) | Dynamic based on content |
| Structure | Formal sections expected | Flexible |
| Figures/Tables | Research-focused | General-purpose |
| Templates | Academic style | Adaptable |

---

### Style Options

#### `--style STYLE`
Presentation style.

**Default**: `doraemon`

**Built-in Styles**:
- `academic`: Clean, professional, white background
- `doraemon`: Colorful, friendly, character elements

**Custom Styles**: Any text description
- `"minimalist with blue theme"`
- `"corporate professional with charts"`
- `"warm and friendly presentation"`

**Examples**:
```bash
# Built-in academic style
python -m paper2slides --input paper.pdf --style academic

# Built-in doraemon style
python -m paper2slides --input paper.pdf --style doraemon

# Custom style
python -m paper2slides --input paper.pdf --style "modern tech with dark mode"

# Custom style with specific elements
python -m paper2slides --input paper.pdf --style "elegant minimalist, soft pink and white colors, gentle gradients"
```

**Style Processing**:
Custom styles are processed by LLM to extract:
- Style name/theme
- Color tones
- Special elements
- Decorative patterns

---

### Length & Density Options

#### `--length LENGTH` (for slides)
Number of slides to generate.

**Default**: `short`

**Options**:
- `short`: 5-7 slides
- `medium`: 8-12 slides
- `long`: 13-20 slides

**Examples**:
```bash
# Short presentation
python -m paper2slides --input paper.pdf --output slides --length short

# Medium presentation
python -m paper2slides --input paper.pdf --output slides --length medium

# Long presentation
python -m paper2slides --input paper.pdf --output slides --length long
```

#### `--density DENSITY` (for poster)
Content density on poster.

**Default**: `medium`

**Options**:
- `sparse`: Minimal content, focus on visuals (~3-5 sections)
- `medium`: Balanced text and visuals (~5-8 sections)
- `dense`: Comprehensive content (~8-12 sections)

**Examples**:
```bash
# Sparse poster
python -m paper2slides --input paper.pdf --output poster --density sparse

# Medium poster
python -m paper2slides --input paper.pdf --output poster --density medium

# Dense poster
python -m paper2slides --input paper.pdf --output poster --density dense
```

---

### Performance Options

#### `--fast`
Enable fast mode (skip RAG indexing).

**Default**: `false` (normal mode)

**Fast Mode**:
- Parses documents to markdown
- Queries LLM directly with full content
- No RAG indexing overhead
- ~30-60 seconds faster

**When to Use**:
- Short documents (< 20 pages)
- Quick previews
- Development/testing
- Single files with few images

**Examples**:
```bash
# Fast mode
python -m paper2slides --input short_paper.pdf --fast

# Normal mode (default)
python -m paper2slides --input long_paper.pdf
```

#### `--parallel N`
Enable parallel slide generation with N workers.

**Default**: `1` (sequential)

**Options**:
- Without argument: Uses 2 workers (`--parallel`)
- With number: Uses N workers (`--parallel 4`)

**Performance**:
- 2 workers: ~40-50% faster
- 4 workers: ~60-70% faster (diminishing returns)
- Higher workers: API rate limits may apply

**Examples**:
```bash
# Parallel with 2 workers (default)
python -m paper2slides --input paper.pdf --parallel

# Parallel with 4 workers
python -m paper2slides --input paper.pdf --parallel 4

# Sequential (default without --parallel)
python -m paper2slides --input paper.pdf
```

---

### Checkpoint Control

#### `--from-stage STAGE`
Force restart from a specific stage.

**Default**: Auto-detect (reuse existing checkpoints)

**Options**:
- `rag`: Start from RAG stage (full restart)
- `summary`: Start from Summary stage
- `plan`: Start from Plan stage
- `generate`: Start from Generate stage

**Use Cases**:

| Scenario | Command |
|----------|---------|
| **Change style only** | `--from-stage plan` |
| **Change length/density** | `--from-stage plan` |
| **Regenerate images** | `--from-stage generate` |
| **Full restart** | `--from-stage rag` |
| **Fix extraction errors** | `--from-stage summary` |

**Examples**:
```bash
# Change style (skip RAG and Summary)
python -m paper2slides --input paper.pdf --style academic --from-stage plan

# Regenerate images only
python -m paper2slides --input paper.pdf --from-stage generate

# Full restart
python -m paper2slides --input paper.pdf --from-stage rag
```

**Auto-Detection**:
Without `--from-stage`, Paper2Slides intelligently detects what needs to be rerun:

```bash
# First run - executes all stages
python -m paper2slides --input paper.pdf --output slides --style doraemon

# Change to academic style - only reruns Plan + Generate
python -m paper2slides --input paper.pdf --output slides --style academic

# Change to poster - only reruns Plan + Generate
python -m paper2slides --input paper.pdf --output poster --style academic
```

---

### Directory & Logging Options

#### `--output-dir PATH`
Output directory for generated files.

**Default**: `outputs/` (in project root)

**Examples**:
```bash
# Custom output directory
python -m paper2slides --input paper.pdf --output-dir /home/user/results

# Relative path
python -m paper2slides --input paper.pdf --output-dir ./my_outputs
```

#### `--debug`
Enable debug logging.

**Default**: `false` (INFO level)

**Debug Output**:
- Detailed stage information
- API call details
- Checkpoint operations
- Intermediate results

**Examples**:
```bash
# Debug mode
python -m paper2slides --input paper.pdf --debug

# Normal mode (default)
python -m paper2slides --input paper.pdf
```

---

### Information Options

#### `--list`
List all processed outputs.

**Usage**:
```bash
python -m paper2slides --list
```

**Output Example**:
```
paper/paper/
  [normal] rag[✓] summary[✓]
    slides_doraemon_medium/ plan[✓] generate[✓]
    slides_academic_long/ plan[✓] generate[✓]
  [fast] rag[✓] summary[✓]
    poster_academic_medium/ plan[✓] generate[✓]

report/general/
  [normal] rag[✓] summary[✓]
    slides_doraemon_short/ plan[✓] generate[○]
```

**Symbols**:
- `✓`: Completed
- `○`: Pending
- `✗`: Failed

---

## 💡 Common Usage Patterns

### Basic Workflows

#### Quick Preview
```bash
# Fastest possible generation
python -m paper2slides --input paper.pdf --output slides --length short --fast --parallel 2
```

#### Production Quality
```bash
# Best quality, normal mode
python -m paper2slides --input paper.pdf --output slides --length long --style academic --parallel 2
```

#### Custom Style Exploration
```bash
# Try different styles quickly
python -m paper2slides --input paper.pdf --output slides --style "modern tech" --from-stage plan
python -m paper2slides --input paper.pdf --output slides --style "warm friendly" --from-stage plan
python -m paper2slides --input paper.pdf --output slides --style "elegant minimal" --from-stage plan
```

---

### Academic Use Cases

#### Conference Presentation
```bash
# Medium length, academic style
python -m paper2slides --input research_paper.pdf \
  --output slides \
  --style academic \
  --length medium \
  --parallel 2
```

#### Poster Session
```bash
# Dense poster with all details
python -m paper2slides --input research_paper.pdf \
  --output poster \
  --style academic \
  --density dense
```

#### Quick Talk (5 minutes)
```bash
# Short slides, key points only
python -m paper2slides --input paper.pdf \
  --output slides \
  --style doraemon \
  --length short \
  --fast
```

---

### Business Use Cases

#### Executive Summary
```bash
# Poster with key highlights
python -m paper2slides --input report.pdf \
  --content general \
  --output poster \
  --style "corporate professional" \
  --density sparse
```

#### Full Presentation
```bash
# Long slides with details
python -m paper2slides --input report.pdf \
  --content general \
  --output slides \
  --style "modern business" \
  --length long
```

---

### Batch Processing

#### Process Multiple Papers
```bash
# Place all PDFs in a directory
mkdir papers
cp paper1.pdf paper2.pdf paper3.pdf papers/

# Process all at once
python -m paper2slides --input papers/ --output slides --style academic
```

#### Generate Both Slides and Poster
```bash
# Generate slides
python -m paper2slides --input paper.pdf --output slides --style academic

# Generate poster (reuses RAG and Summary checkpoints)
python -m paper2slides --input paper.pdf --output poster --style academic
```

---

## 🔄 Checkpoint and Resume

### Understanding Checkpoints

Paper2Slides saves progress at each stage:

```
outputs/
  └── paper/
      └── paper/
          └── normal/                    # or fast/
              ├── checkpoint_rag.json    # ✓ After RAG stage
              ├── checkpoint_summary.json # ✓ After Summary stage
              └── slides_doraemon_medium/
                  ├── checkpoint_plan.json # ✓ After Plan stage
                  └── 20241210_123456/     # ✓ After Generate stage
```

### Resume After Interruption

```bash
# Start processing
python -m paper2slides --input paper.pdf --output slides

# Interrupted! (Ctrl+C or crash)

# Resume - automatically continues from last checkpoint
python -m paper2slides --input paper.pdf --output slides
```

**Output**:
```
Project: paper
Base: outputs/paper/paper/normal
Config: slides_doraemon_short

Reusing existing checkpoints, starting from: plan
```

### Regenerate with Different Settings

```bash
# Original run
python -m paper2slides --input paper.pdf --output slides --style doraemon --length medium

# Try different style (keeps RAG and Summary)
python -m paper2slides --input paper.pdf --output slides --style academic --length medium

# Try different length (keeps RAG and Summary)
python -m paper2slides --input paper.pdf --output slides --style academic --length long

# Try poster instead (keeps RAG and Summary)
python -m paper2slides --input paper.pdf --output poster --style academic --density medium
```

### Force Full Restart

```bash
# Delete all checkpoints and start fresh
python -m paper2slides --input paper.pdf --output slides --from-stage rag

# Or manually delete checkpoint directory
rm -rf outputs/paper/paper/normal/
python -m paper2slides --input paper.pdf --output slides
```

---

## 📊 Output Structure

### Generated Files

After successful generation:

```
outputs/
  └── paper/                              # Project name (from input filename)
      └── paper/                          # Content type
          └── normal/                     # Mode (fast or normal)
              ├── checkpoint_rag.json     # RAG results
              ├── checkpoint_summary.json # Extracted content
              ├── summary.md              # Human-readable summary
              └── slides_doraemon_medium/ # Config name
                  ├── state.json          # Pipeline state
                  ├── checkpoint_plan.json # Content plan
                  └── 20241210_123456/    # Timestamp
                      ├── slide_01.png    # Generated slides
                      ├── slide_02.png
                      ├── ...
                      └── slides.pdf      # Combined PDF
```

### Accessing Results

```bash
# View summary
cat outputs/paper/paper/normal/summary.md

# Open PDF
open outputs/paper/paper/normal/slides_doraemon_medium/20241210_123456/slides.pdf

# List images
ls outputs/paper/paper/normal/slides_doraemon_medium/20241210_123456/
```

---

## 🐛 Debugging and Troubleshooting

### Enable Debug Mode

```bash
python -m paper2slides --input paper.pdf --output slides --debug
```

**Debug Output Includes**:
- Stage execution details
- LLM prompts and responses
- File operations
- Checkpoint saves/loads
- Error stack traces

### Check Intermediate Results

```bash
# View RAG results
cat outputs/paper/paper/normal/checkpoint_rag.json | jq .

# View extracted content
cat outputs/paper/paper/normal/checkpoint_summary.json | jq .

# View content plan
cat outputs/paper/paper/normal/slides_doraemon_medium/checkpoint_plan.json | jq .

# View pipeline state
cat outputs/paper/paper/normal/slides_doraemon_medium/state.json | jq .
```

### Common Issues

#### No Output Generated

```bash
# Check if stages completed
python -m paper2slides --list

# Check specific stage
cat outputs/paper/paper/normal/slides_doraemon_medium/state.json
```

#### Poor Quality Results

```bash
# Try normal mode instead of fast
python -m paper2slides --input paper.pdf --output slides

# Use longer length
python -m paper2slides --input paper.pdf --output slides --length long

# Check extracted content quality
cat outputs/paper/paper/normal/summary.md
```

#### API Errors

```bash
# Check environment variables
env | grep -E '(RAG_LLM|IMAGE_GEN)'

# Verify API keys in .env file
cat paper2slides/.env
```

---

## ⚡ Performance Tips

### Optimize Speed

```bash
# Fastest: fast mode + parallel + short
python -m paper2slides --input paper.pdf --fast --parallel 4 --length short

# Balance: normal mode + parallel
python -m paper2slides --input paper.pdf --parallel 2 --length medium
```

### Optimize Quality

```bash
# Best quality: normal mode + long + sequential
python -m paper2slides --input paper.pdf --output slides --length long

# Good balance: normal mode + medium + parallel
python -m paper2slides --input paper.pdf --output slides --length medium --parallel 2
```

### Optimize Cost (API calls)

```bash
# Fewest calls: fast mode + short
python -m paper2slides --input paper.pdf --fast --length short

# Moderate: normal mode + reuse checkpoints
python -m paper2slides --input paper.pdf --output slides
python -m paper2slides --input paper.pdf --output poster  # Reuses RAG/Summary
```

---

## 🔧 Environment Variables

While most configuration is via command-line options, some settings require environment variables:

```bash
# Set API keys
export RAG_LLM_API_KEY="your_openai_key"
export RAG_LLM_BASE_URL="https://api.openai.com/v1"
export IMAGE_GEN_API_KEY="your_openrouter_key"
export IMAGE_GEN_BASE_URL="https://openrouter.ai/api/v1"

# Run Paper2Slides
python -m paper2slides --input paper.pdf --output slides
```

**Better**: Use `.env` file in `paper2slides/` directory:

```bash
# paper2slides/.env
RAG_LLM_API_KEY=your_openai_key
RAG_LLM_BASE_URL=https://api.openai.com/v1
IMAGE_GEN_API_KEY=your_openrouter_key
IMAGE_GEN_BASE_URL=https://openrouter.ai/api/v1
```

---

## 📖 Examples by Complexity

### Beginner Examples

```bash
# Simplest possible usage
python -m paper2slides --input paper.pdf --output slides

# With style choice
python -m paper2slides --input paper.pdf --output slides --style academic

# Generate poster
python -m paper2slides --input paper.pdf --output poster
```

### Intermediate Examples

```bash
# Custom style with specific length
python -m paper2slides --input paper.pdf --output slides \
  --style "modern minimalist" --length medium

# Fast mode for quick results
python -m paper2slides --input paper.pdf --output slides --fast --parallel 2

# Generate both slides and poster
python -m paper2slides --input paper.pdf --output slides --style academic
python -m paper2slides --input paper.pdf --output poster --style academic
```

### Advanced Examples

```bash
# Full control with debugging
python -m paper2slides \
  --input paper.pdf \
  --output slides \
  --content paper \
  --style "elegant corporate with blue accents" \
  --length long \
  --parallel 4 \
  --output-dir ./results \
  --debug

# Checkpoint-based iteration
python -m paper2slides --input paper.pdf --output slides --style "option1" --from-stage plan
python -m paper2slides --input paper.pdf --output slides --style "option2" --from-stage plan
python -m paper2slides --input paper.pdf --output slides --style "option3" --from-stage plan

# Batch process directory
python -m paper2slides --input ./papers/ --output slides --style academic --parallel 2
```

---

## 📚 Next Steps

- **[Configuration](./08-configuration.md)**: Detailed environment setup
- **[Code Structure](./06-code-structure.md)**: Understanding the codebase
- **[Troubleshooting](./10-troubleshooting.md)**: Solving common problems
