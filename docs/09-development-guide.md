# Development Guide

Guide for developers who want to contribute to or extend Paper2Slides.

## 🚀 Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/HKUDS/Paper2Slides.git
cd Paper2Slides

# Create development environment
conda create -n paper2slides-dev python=3.12 -y
conda activate paper2slides-dev

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest black flake8 mypy

# Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Project Structure for Developers

```
Paper2Slides/
├── paper2slides/           # Main package
│   ├── core/               # Pipeline logic
│   ├── raganything/        # Document parsing
│   ├── rag/                # RAG system
│   ├── summary/            # Content extraction
│   ├── generator/          # Image generation
│   ├── prompts/            # LLM prompts
│   └── utils/              # Utilities
├── api/                    # Web API
├── frontend/               # React frontend
├── tests/                  # Test suite (to be added)
├── docs/                   # Documentation
└── scripts/                # Shell scripts
```

## 🧰 Development Workflow

### 1. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Test changes
python -m paper2slides --input test.pdf --output slides --debug

# Run tests (when available)
pytest tests/

# Format code
black paper2slides/
flake8 paper2slides/

# Commit changes
git add .
git commit -m "Add feature: description"

# Push to GitHub
git push origin feature/your-feature-name
```

### 2. Code Style

**Follow PEP 8**:
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to functions and classes

**Example**:
```python
async def run_rag_stage(base_dir: Path, config: Dict) -> Dict:
    """
    Stage 1: Index document and run RAG queries.
    
    Args:
        base_dir: Base directory for this document/project
        config: Pipeline configuration with input_path (file or directory)
    
    Returns:
        Dictionary with rag_results and markdown_paths
        
    Note:
        RAGClient handles both single files and directories automatically.
    """
    # Implementation
    pass
```

### 3. Type Hints

Use type hints for all function signatures:

```python
from typing import Dict, List, Optional
from pathlib import Path

def process_files(
    file_paths: List[str],
    output_dir: Path,
    recursive: bool = False
) -> Optional[Dict[str, Any]]:
    """Process multiple files."""
    pass
```

### 4. Error Handling

Use specific exceptions and informative messages:

```python
try:
    result = await run_stage()
except FileNotFoundError as e:
    logger.error(f"Input file not found: {e}")
    raise
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

## 🔧 Common Development Tasks

### Adding a New Style

**1. Update Style Enum** (`paper2slides/generator/config.py`):
```python
class StyleType(Enum):
    ACADEMIC = "academic"
    DORAEMON = "doraemon"
    TOTORO = "totoro"      # New style
    CUSTOM = "custom"
```

**2. Add Style Hints** (`paper2slides/prompts/image_generation.py`):
```python
SLIDE_STYLE_HINTS = {
    "academic": "Clean professional white background...",
    "doraemon": "Colorful friendly with character...",
    "totoro": "Nature-inspired with forest green tones...",  # New
}
```

**3. Add Layout Templates** (if needed):
```python
SLIDE_LAYOUTS_TOTORO = {
    "title": "Title centered with nature elements...",
    "content": "Content with leaf decorations...",
}
```

**4. Update Image Generator** (`paper2slides/generator/image_generator.py`):
```python
if style == "totoro":
    style_hint = SLIDE_STYLE_HINTS["totoro"]
    layouts = SLIDE_LAYOUTS_TOTORO
```

### Adding a New Content Type

**1. Define Content Model** (`paper2slides/summary/models.py`):
```python
@dataclass
class ReportContent:
    """Business report content structure."""
    title: str
    executive_summary: str
    sections: List[Dict[str, str]]
    recommendations: List[str]
```

**2. Add Extraction Logic** (`paper2slides/summary/report.py`):
```python
async def extract_report(
    rag_results: Dict[str, List[Dict]],
    llm_client: OpenAI,
    model: str = "gpt-4o-mini"
) -> ReportContent:
    """Extract structured report content."""
    # Implementation
    pass
```

**3. Add Query Set** (`paper2slides/rag/query.py`):
```python
RAG_REPORT_QUERIES = {
    "summary": ["What is the executive summary?"],
    "findings": ["What are the key findings?"],
    "recommendations": ["What recommendations are provided?"],
}
```

**4. Update Pipeline** (`paper2slides/core/stages/summary_stage.py`):
```python
if content_type == "report":
    content = await extract_report(rag_results, llm_client)
```

### Adding a New Output Format

**1. Update Output Type Enum** (`paper2slides/generator/config.py`):
```python
class OutputType(Enum):
    SLIDES = "slides"
    POSTER = "poster"
    INFOGRAPHIC = "infographic"  # New
```

**2. Add Planning Prompt** (`paper2slides/prompts/content_planning.py`):
```python
PAPER_INFOGRAPHIC_PLANNING_PROMPT = """
You are an expert at creating infographics from research papers.
Create a visually engaging infographic layout...
"""
```

**3. Update Content Planner** (`paper2slides/generator/content_planner.py`):
```python
if output_type == "infographic":
    prompt = PAPER_INFOGRAPHIC_PLANNING_PROMPT
```

**4. Update CLI** (`paper2slides/main.py`):
```python
parser.add_argument(
    "--output",
    choices=["poster", "slides", "infographic"],
    default="poster"
)
```

### Customizing LLM Prompts

**Location**: `paper2slides/prompts/`

**Example - Modify Planning Prompt**:

```python
# In paper2slides/prompts/content_planning.py

PAPER_SLIDES_PLANNING_PROMPT = """
You are an expert at creating academic presentation slides.

[Your custom instructions here]

Output JSON format:
{
  "sections": [
    {
      "id": "slide_01",
      "title": "...",
      "type": "title|content|methods|results|conclusion",
      "content": "...",
      "figures": [...],
      "tables": [...]
    }
  ]
}

[Your custom guidelines here]
"""
```

**Testing Prompt Changes**:
```bash
# Test with a specific paper
python -m paper2slides \
  --input test_paper.pdf \
  --output slides \
  --from-stage plan \  # Only rerun planning
  --debug
```

### Adding Custom Parsers

**1. Create Parser Class** (`paper2slides/raganything/custom_parser.py`):
```python
from .base import BaseParser

class CustomParser(BaseParser):
    """Custom document parser."""
    
    def parse(self, file_path: str, output_dir: str) -> ParseResult:
        """Parse document to markdown."""
        # Implementation
        pass
```

**2. Register Parser** (`paper2slides/raganything/batch_parser.py`):
```python
PARSERS = {
    "mineru": MinerUParser,
    "custom": CustomParser,  # New
}
```

**3. Use Custom Parser**:
```bash
# In code
parser = BatchParser(parser_type="custom")
```

## 🧪 Testing

### Unit Tests (To Be Implemented)

```python
# tests/unit/test_content_planner.py
import pytest
from paper2slides.generator import ContentPlanner

def test_content_planner_slides():
    """Test content planner for slides."""
    planner = ContentPlanner(api_key="test", base_url="test")
    # Test implementation
    pass

def test_content_planner_poster():
    """Test content planner for poster."""
    # Test implementation
    pass
```

### Integration Tests (To Be Implemented)

```python
# tests/integration/test_pipeline.py
import pytest
from pathlib import Path
from paper2slides.core import run_pipeline

@pytest.mark.asyncio
async def test_full_pipeline(tmp_path):
    """Test complete pipeline execution."""
    config = {
        "input_path": "tests/fixtures/sample.pdf",
        "output_type": "slides",
        "style": "academic"
    }
    # Test implementation
    pass
```

### Manual Testing

```bash
# Test with sample paper
python -m paper2slides \
  --input tests/fixtures/sample_paper.pdf \
  --output slides \
  --style academic \
  --length short \
  --debug

# Verify outputs
ls outputs/sample_paper/paper/normal/slides_academic_short/
```

## 🐛 Debugging Tips

### Enable Debug Logging

```python
# In your code
import logging
logging.basicConfig(level=logging.DEBUG)
```

```bash
# In CLI
python -m paper2slides --input paper.pdf --debug
```

### Inspect Checkpoints

```python
from paper2slides.utils import load_json

# Load checkpoint
rag_data = load_json(Path("outputs/.../checkpoint_rag.json"))
print(rag_data.keys())
print(rag_data["rag_results"]["paper_info"])
```

### Test Individual Stages

```python
# Test RAG stage
from paper2slides.core.stages import run_rag_stage
import asyncio

config = {"input_path": "paper.pdf", "fast_mode": False}
result = asyncio.run(run_rag_stage(Path("outputs/test"), config))
```

### Use Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use IDE debugger
# Set breakpoint in IDE and run with debugger
```

## 📝 Documentation

### Adding Documentation

**1. Create/Update Markdown Files** in `docs/`

**2. Follow Documentation Structure**:
- Clear headings
- Code examples
- Practical use cases
- Cross-references

**3. Update Main README** if adding major features

### Documentation Standards

- Use clear, concise language
- Provide code examples
- Include both simple and advanced usage
- Add troubleshooting sections
- Keep cross-references updated

## 🤝 Contributing

### Contribution Process

**1. Fork and Clone**:
```bash
# Fork on GitHub
git clone https://github.com/YOUR_USERNAME/Paper2Slides.git
cd Paper2Slides
```

**2. Create Feature Branch**:
```bash
git checkout -b feature/your-feature
```

**3. Make Changes**:
- Write code
- Add tests
- Update documentation
- Follow code style

**4. Test Changes**:
```bash
# Run tests
pytest tests/

# Manual testing
python -m paper2slides --input test.pdf --output slides
```

**5. Commit and Push**:
```bash
git add .
git commit -m "Add feature: description"
git push origin feature/your-feature
```

**6. Create Pull Request**:
- Go to GitHub
- Click "New Pull Request"
- Describe your changes
- Reference any related issues

### Pull Request Guidelines

**Title**: Clear, descriptive (e.g., "Add support for custom parsers")

**Description**:
- What changes were made
- Why these changes are needed
- How to test the changes
- Any breaking changes

**Checklist**:
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or noted in description)
- [ ] Tested manually

## 🔍 Code Review

### What Reviewers Look For

**Code Quality**:
- Clear, readable code
- Proper error handling
- Type hints
- Docstrings

**Functionality**:
- Works as intended
- No bugs
- Edge cases handled

**Performance**:
- Efficient algorithms
- No unnecessary API calls
- Proper async/await usage

**Tests**:
- Adequate test coverage
- Tests pass

**Documentation**:
- Code is documented
- User-facing docs updated

## 🚀 Release Process

### Versioning

Follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating a Release

**1. Update Version**:
```python
# In setup.py or __init__.py
__version__ = "1.2.0"
```

**2. Update CHANGELOG**:
```markdown
## [1.2.0] - 2024-12-10
### Added
- Custom style processing
- Parallel image generation

### Fixed
- Checkpoint detection bug
```

**3. Tag Release**:
```bash
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

**4. Create GitHub Release**:
- Go to GitHub Releases
- Create new release from tag
- Add release notes

## 🏗️ Architecture Decisions

### When Adding Features

**Consider**:
- Is this feature broadly useful?
- Does it fit the project's scope?
- Can it be implemented without breaking existing functionality?
- Is the API intuitive?

**Design Principles**:
- **Modularity**: Keep components independent
- **Extensibility**: Easy to add new features
- **Reliability**: Checkpoint and recover
- **Efficiency**: Minimize API calls and processing time
- **Transparency**: Log progress and decisions

### Code Organization

**Where to Add New Code**:

| Feature Type | Location |
|--------------|----------|
| Pipeline stages | `paper2slides/core/stages/` |
| Content extraction | `paper2slides/summary/` |
| RAG queries | `paper2slides/rag/query.py` |
| Prompts | `paper2slides/prompts/` |
| Utilities | `paper2slides/utils/` |
| API endpoints | `api/server.py` |
| Frontend components | `frontend/src/components/` |

## 📚 Resources

### Internal Resources

- [Architecture Documentation](./02-architecture.md)
- [Pipeline Stages](./03-pipeline-stages.md)
- [Code Structure](./06-code-structure.md)

### External Resources

- [LightRAG](https://github.com/HKUDS/LightRAG)
- [MinerU Documentation](https://github.com/opendatalab/MinerU)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

### Related Projects

- [RAG-Anything](https://github.com/HKUDS/RAG-Anything)
- [VideoRAG](https://github.com/HKUDS/VideoRAG)

## 🎯 Next Steps for Contributors

### Beginner Tasks

- [ ] Add more built-in styles
- [ ] Improve error messages
- [ ] Add input validation
- [ ] Write unit tests
- [ ] Improve documentation

### Intermediate Tasks

- [ ] Add support for new file formats
- [ ] Implement caching layer
- [ ] Add progress indicators
- [ ] Optimize API call efficiency
- [ ] Add configuration file support

### Advanced Tasks

- [ ] Implement custom RAG strategies
- [ ] Add fine-tuning support
- [ ] Implement distributed processing
- [ ] Add plugin system
- [ ] Optimize large document handling

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Community**: WeChat/Feishu groups (see main README)

---

**Thank you for contributing to Paper2Slides! 🎉**
