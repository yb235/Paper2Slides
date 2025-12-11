# Troubleshooting Guide

Solutions to common problems and frequently asked questions.

## 🚨 Common Issues

### Installation Issues

#### Problem: Import Error for `paper2slides`

```
ModuleNotFoundError: No module named 'paper2slides'
```

**Solutions**:

1. **Verify installation**:
```bash
pip list | grep lightrag
pip list | grep mineru
```

2. **Reinstall dependencies**:
```bash
pip install -r requirements.txt
```

3. **Check Python version**:
```bash
python --version  # Should be 3.12+
```

4. **Ensure correct environment**:
```bash
conda activate paper2slides
which python  # Should point to conda environment
```

#### Problem: MinerU Installation Fails

```
ERROR: Could not build wheels for mineru
```

**Solutions**:

1. **Install build tools** (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

2. **Install build tools** (macOS):
```bash
xcode-select --install
```

3. **Try minimal installation**:
```bash
pip install mineru[core]==2.6.4
```

### API Key Issues

#### Problem: API Key Not Found

```
Error: Missing RAG_LLM_API_KEY
```

**Solutions**:

1. **Check .env file exists**:
```bash
ls paper2slides/.env
```

2. **Verify .env content**:
```bash
cat paper2slides/.env
# Should contain:
# RAG_LLM_API_KEY=sk-...
# IMAGE_GEN_API_KEY=sk-or-...
```

3. **Create .env from example**:
```bash
cp paper2slides/.env.example paper2slides/.env
# Edit with your keys
nano paper2slides/.env
```

4. **Use environment variables**:
```bash
export RAG_LLM_API_KEY="your-key"
export IMAGE_GEN_API_KEY="your-key"
```

#### Problem: API Key Invalid

```
Error: Invalid API key
```

**Solutions**:

1. **Test OpenAI key**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

2. **Test OpenRouter key**:
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

3. **Regenerate keys**:
   - OpenAI: https://platform.openai.com/api-keys
   - OpenRouter: https://openrouter.ai/keys

4. **Check for spaces/newlines**:
```bash
# Keys should be on single line without quotes
# WRONG: RAG_LLM_API_KEY="sk-..."
# RIGHT: RAG_LLM_API_KEY=sk-...
```

### File Processing Issues

#### Problem: Input File Not Found

```
Error: Input file not found: paper.pdf
```

**Solutions**:

1. **Use absolute path**:
```bash
python -m paper2slides --input /absolute/path/to/paper.pdf
```

2. **Check current directory**:
```bash
pwd
ls -la  # Verify file exists
```

3. **Use relative path from project root**:
```bash
cd /path/to/Paper2Slides
python -m paper2slides --input ./papers/paper.pdf
```

#### Problem: Parsing Fails

```
Error: Failed to parse document
```

**Solutions**:

1. **Check file integrity**:
```bash
file paper.pdf  # Should show "PDF document"
```

2. **Try different PDF**:
   - Some PDFs are scanned images (not text)
   - Some are encrypted/protected

3. **Check MinerU installation**:
```bash
python -c "from magic_pdf.pipe.UNIPipe import UNIPipe; print('OK')"
```

4. **Enable debug mode**:
```bash
python -m paper2slides --input paper.pdf --debug
```

#### Problem: Image Extraction Fails

```
Warning: Image not found: /path/to/image.png
```

**Solutions**:

1. **Check markdown output**:
```bash
# Find parsed markdown
find outputs/ -name "*.md"
cat outputs/paper/paper/normal/rag_output/paper.md
```

2. **Verify image paths**:
   - Images should be in same directory as markdown
   - Paths should be relative or absolute

3. **Check image files**:
```bash
find outputs/ -name "*.png"
ls -la outputs/paper/paper/normal/rag_output/
```

### RAG Issues

#### Problem: Empty RAG Results

```
Error: No RAG results generated
```

**Solutions**:

1. **Try fast mode**:
```bash
python -m paper2slides --input paper.pdf --fast
```

2. **Check document length**:
   - Very short documents may not generate good results
   - Try with a longer document

3. **Increase query specificity**:
   - Edit `paper2slides/rag/query.py`
   - Add more specific queries

#### Problem: RAG Indexing Fails

```
Error: Failed to index documents
```

**Solutions**:

1. **Check LightRAG installation**:
```bash
pip install lightrag-hku --upgrade
```

2. **Clear RAG storage**:
```bash
rm -rf outputs/paper/paper/normal/rag_storage/
```

3. **Use fast mode instead**:
```bash
python -m paper2slides --input paper.pdf --fast
```

### Generation Issues

#### Problem: No Images Generated

```
Error: Image generation failed
```

**Solutions**:

1. **Check OpenRouter API key**:
```bash
# Test key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $IMAGE_GEN_API_KEY"
```

2. **Check rate limits**:
   - Wait a few minutes
   - Try sequential generation (remove `--parallel`)

3. **Check plan checkpoint**:
```bash
cat outputs/.../checkpoint_plan.json | jq .
# Verify sections exist
```

4. **Try simpler style**:
```bash
python -m paper2slides --input paper.pdf --style academic
```

#### Problem: Images Low Quality

**Solutions**:

1. **Use more detailed prompts** (code modification):
   - Edit `paper2slides/prompts/image_generation.py`
   - Add more style details

2. **Provide better input**:
   - Use higher quality input documents
   - Ensure figures are clear

3. **Adjust length/density**:
```bash
# More slides = less content per slide = better quality
python -m paper2slides --input paper.pdf --length long
```

#### Problem: PDF Generation Fails

```
Error: Failed to create PDF
```

**Solutions**:

1. **Check reportlab installation**:
```bash
pip install reportlab --upgrade
```

2. **Verify images exist**:
```bash
ls outputs/.../20241210_123456/
```

3. **Check image format**:
   - Should be PNG or JPEG
   - Not corrupted

### Performance Issues

#### Problem: Very Slow Processing

**Solutions**:

1. **Use fast mode**:
```bash
python -m paper2slides --input paper.pdf --fast --parallel 2
```

2. **Reduce length/density**:
```bash
python -m paper2slides --input paper.pdf --length short
```

3. **Check network connection**:
```bash
ping api.openai.com
ping openrouter.ai
```

4. **Monitor API calls**:
```bash
# Enable debug to see API calls
python -m paper2slides --input paper.pdf --debug
```

#### Problem: Out of Memory

```
Error: MemoryError
```

**Solutions**:

1. **Reduce parallel workers**:
```bash
python -m paper2slides --input paper.pdf --parallel 1
```

2. **Use fast mode**:
```bash
python -m paper2slides --input paper.pdf --fast
```

3. **Process smaller batches**:
```bash
# Instead of directory, process files individually
python -m paper2slides --input paper1.pdf
python -m paper2slides --input paper2.pdf
```

4. **Increase system memory**:
   - Close other applications
   - Use machine with more RAM

### API Server Issues

#### Problem: Port Already in Use

```
Error: Address already in use
```

**Solutions**:

1. **Use different port**:
```bash
./scripts/start_backend.sh 8002
```

2. **Kill existing process**:
```bash
lsof -ti :8001 | xargs kill -9
```

3. **Find and kill process**:
```bash
ps aux | grep "python api/server.py"
kill <PID>
```

#### Problem: CORS Errors

```
Error: CORS policy blocked
```

**Solutions**:

1. **Update CORS origins** in `api/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://your-frontend-url.com",  # Add this
    ],
)
```

2. **Restart backend**:
```bash
./scripts/stop.sh
./scripts/start_backend.sh
```

#### Problem: File Upload Fails

```
Error: No files uploaded
```

**Solutions**:

1. **Check file size**:
   - Default limit: 100 MB
   - Larger files: Configure in API

2. **Check file type**:
   - Must be: PDF, DOCX, XLSX, PPTX, MD

3. **Check network**:
```bash
curl -F "files=@test.pdf" http://localhost:8001/api/chat
```

### Checkpoint Issues

#### Problem: Checkpoint Not Found

```
Error: Missing checkpoint_rag.json
```

**Solutions**:

1. **Verify checkpoint exists**:
```bash
ls outputs/paper/paper/normal/
```

2. **Check mode**:
```bash
# Fast mode checkpoints in fast/
ls outputs/paper/paper/fast/

# Normal mode checkpoints in normal/
ls outputs/paper/paper/normal/
```

3. **Regenerate from scratch**:
```bash
python -m paper2slides --input paper.pdf --from-stage rag
```

#### Problem: Corrupt Checkpoint

```
Error: Failed to load checkpoint
```

**Solutions**:

1. **Validate JSON**:
```bash
cat outputs/.../checkpoint_rag.json | jq .
```

2. **Delete and regenerate**:
```bash
rm outputs/.../checkpoint_rag.json
python -m paper2slides --input paper.pdf --from-stage rag
```

3. **Check disk space**:
```bash
df -h
```

## ❓ Frequently Asked Questions

### General Questions

#### Q: How long does processing take?

**A**: Typical times for a 10-page paper:
- Fast mode: 1-2 minutes
- Normal mode: 2-4 minutes
- With parallel generation (2 workers): 30-50% faster

#### Q: How much does it cost (API calls)?

**A**: Approximate costs per paper (varies by length):
- RAG queries: ~$0.10-0.30 (GPT-4o)
- Content extraction: ~$0.05-0.10 (GPT-4o-mini)
- Planning: ~$0.05-0.10 (GPT-4o)
- Image generation: ~$0.50-2.00 (Gemini 3 Pro, 8-12 images)

**Total**: ~$0.70-2.50 per paper

#### Q: Can I use local models?

**A**: Not directly. Paper2Slides uses cloud APIs. To use local models:
1. Set up local API server (e.g., vLLM, Ollama with OpenAI-compatible API)
2. Set `RAG_LLM_BASE_URL` to local server
3. Results may vary depending on model quality

#### Q: Can I process multiple papers at once?

**A**: Yes, two ways:
1. **Directory input**: `--input ./papers/` (processes all files)
2. **Separate runs**: Run CLI multiple times in parallel
3. **API**: Only one session at a time via web interface

#### Q: How do I change the style of existing output?

**A**:
```bash
# Original run
python -m paper2slides --input paper.pdf --style doraemon

# Change style (reuses RAG and Summary)
python -m paper2slides --input paper.pdf --style academic

# Or force from plan stage
python -m paper2slides --input paper.pdf --style academic --from-stage plan
```

### Technical Questions

#### Q: What's the difference between fast and normal mode?

**A**:

| Aspect | Fast Mode | Normal Mode |
|--------|-----------|-------------|
| Parsing | ✓ MinerU | ✓ MinerU |
| Indexing | ✗ Skipped | ✓ LightRAG |
| Queries | Direct GPT-4o | RAG retrieval |
| Time | ~1-2 min | ~2-4 min |
| Cost | Lower | Slightly higher |
| Quality | Good for short docs | Better for long docs |
| Best for | Quick previews | Production quality |

#### Q: Can I customize the prompts?

**A**: Yes, edit files in `paper2slides/prompts/`:
- `content_planning.py`: Planning prompts
- `image_generation.py`: Image generation prompts
- `paper_extraction.py`: Content extraction prompts

Then run with `--from-stage` to test:
```bash
python -m paper2slides --input paper.pdf --from-stage plan --debug
```

#### Q: How do checkpoints work?

**A**: Checkpoints save after each stage:
1. RAG: `checkpoint_rag.json`
2. Summary: `checkpoint_summary.json`
3. Plan: `checkpoint_plan.json`
4. Generate: Images in timestamped directory

Benefits:
- Resume after interruption
- Regenerate from any stage
- Experiment with different settings

#### Q: Can I use different LLM models?

**A**: Currently hardcoded in code:
- RAG: GPT-4o
- Extraction: GPT-4o-mini
- Planning: GPT-4o
- Images: Gemini 3 Pro

To change:
1. Modify model names in code
2. Ensure API endpoint supports models
3. Test thoroughly

### Workflow Questions

#### Q: How do I generate both slides and poster?

**A**:
```bash
# Generate slides
python -m paper2slides --input paper.pdf --output slides --style academic

# Generate poster (reuses RAG and Summary)
python -m paper2slides --input paper.pdf --output poster --style academic
```

#### Q: How do I try different styles quickly?

**A**:
```bash
# First run (all stages)
python -m paper2slides --input paper.pdf --output slides --style academic

# Try other styles (only Plan + Generate)
python -m paper2slides --input paper.pdf --output slides --style doraemon
python -m paper2slides --input paper.pdf --output slides --style "minimalist blue"
```

#### Q: Can I edit the generated plan?

**A**: Yes:
1. Generate initial plan:
```bash
python -m paper2slides --input paper.pdf --from-stage plan
```

2. Edit `checkpoint_plan.json`:
```bash
nano outputs/.../checkpoint_plan.json
# Modify sections, titles, figure assignments
```

3. Regenerate images:
```bash
python -m paper2slides --input paper.pdf --from-stage generate
```

## 🔍 Debugging Techniques

### Enable Debug Mode

```bash
python -m paper2slides --input paper.pdf --debug
```

Shows:
- API calls and responses
- Checkpoint operations
- File operations
- Detailed errors

### Check Intermediate Results

```bash
# View summary
cat outputs/paper/paper/normal/summary.md

# Inspect RAG results
cat outputs/paper/paper/normal/checkpoint_rag.json | jq .rag_results.paper_info

# View plan
cat outputs/.../checkpoint_plan.json | jq .plan.sections

# Check state
cat outputs/.../state.json | jq .stages
```

### Test Individual Components

```python
# Test parsing
from paper2slides.raganything.batch_parser import BatchParser
parser = BatchParser()
result = parser.process_batch(["paper.pdf"], "test_output")

# Test RAG
from paper2slides.rag import RAGClient
# ... test RAG operations

# Test content planner
from paper2slides.generator import ContentPlanner
# ... test planning
```

### Monitor API Calls

```bash
# Debug mode shows all API calls
python -m paper2slides --input paper.pdf --debug 2>&1 | grep "API"
```

## 📞 Getting Help

### Before Asking for Help

1. **Search existing issues**: https://github.com/HKUDS/Paper2Slides/issues
2. **Check documentation**: Review relevant docs sections
3. **Try debug mode**: `--debug` often reveals the problem
4. **Test with sample**: Does it work with a different PDF?

### How to Report Issues

Include:

1. **Paper2Slides version**:
```bash
python -c "import paper2slides; print(paper2slides.__version__)"
```

2. **Python version**:
```bash
python --version
```

3. **Operating system**:
```bash
uname -a  # Linux/macOS
```

4. **Full command**:
```bash
python -m paper2slides --input paper.pdf --output slides --debug
```

5. **Error message**:
```
Complete error output from terminal
```

6. **Relevant checkpoint**:
```bash
# If error in specific stage
cat outputs/.../checkpoint_xxx.json
```

### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **WeChat/Feishu**: Community groups (see main README)

## 🛠️ Advanced Troubleshooting

### Clean Slate

If all else fails:

```bash
# Remove all outputs
rm -rf outputs/

# Remove virtual environment
conda remove -n paper2slides --all

# Reinstall
conda create -n paper2slides python=3.12 -y
conda activate paper2slides
pip install -r requirements.txt

# Reconfigure
cp paper2slides/.env.example paper2slides/.env
# Add your API keys

# Test
python -m paper2slides --input paper.pdf --output slides --debug
```

### Network Issues

```bash
# Test API connectivity
curl https://api.openai.com/v1/models
curl https://openrouter.ai/api/v1/models

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Bypass proxy (if needed)
unset HTTP_PROXY HTTPS_PROXY
```

### Permission Issues

```bash
# Fix directory permissions
chmod -R 755 outputs sources

# Fix env file permissions
chmod 600 paper2slides/.env

# Run as user (not root)
whoami  # Should not be root
```

## 📚 Additional Resources

- **[Architecture](./02-architecture.md)**: Understanding the system
- **[Pipeline Stages](./03-pipeline-stages.md)**: How stages work
- **[Configuration](./08-configuration.md)**: Setup and config
- **[Development Guide](./09-development-guide.md)**: Contributing

---

**Still having issues?** Open an issue on GitHub with details!
