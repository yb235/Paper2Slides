"""
Generate Stage - Image generation
"""
import logging
import os
from pathlib import Path
from typing import Dict

from ...utils import load_json
from ..paths import get_summary_checkpoint, get_plan_checkpoint, get_output_dir

logger = logging.getLogger(__name__)


async def run_generate_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict:
    """Stage 4: Generate images."""
    from paper2slides.summary import PaperContent, GeneralContent, TableInfo, FigureInfo, OriginalElements
    from paper2slides.generator import GenerationConfig, GenerationInput
    from paper2slides.generator.config import OutputType, PosterDensity, SlidesLength, StyleType
    from paper2slides.generator.content_planner import ContentPlan, Section, TableRef, FigureRef
    from paper2slides.generator.image_generator import ImageGenerator, save_images_as_pdf
    
    plan_data = load_json(get_plan_checkpoint(config_dir))
    summary_data = load_json(get_summary_checkpoint(base_dir, config))
    if not plan_data or not summary_data:
        raise ValueError("Missing checkpoints.")
    
    content_type = plan_data.get("content_type", "paper")
    
    origin_data = plan_data["origin"]
    origin = OriginalElements(
        tables=[TableInfo(
            table_id=t["id"],
            caption=t.get("caption", ""),
            html_content=t.get("html", ""),
        ) for t in origin_data.get("tables", [])],
        figures=[FigureInfo(
            figure_id=f["id"],
            caption=f.get("caption"),
            image_path=f.get("path", ""),
        ) for f in origin_data.get("figures", [])],
        base_path=origin_data.get("base_path", ""),
    )
    
    plan_dict = plan_data["plan"]
    tables_index = {t.table_id: t for t in origin.tables}
    figures_index = {f.figure_id: f for f in origin.figures}
    
    sections = []
    for s in plan_dict.get("sections", []):
        sections.append(Section(
            id=s.get("id", ""),
            title=s.get("title", ""),
            section_type=s.get("type", "content"),
            content=s.get("content", ""),
            tables=[TableRef(**t) for t in s.get("tables", [])],
            figures=[FigureRef(**f) for f in s.get("figures", [])],
        ))
    
    plan = ContentPlan(
        output_type=plan_dict.get("output_type", "slides"),
        sections=sections,
        tables_index=tables_index,
        figures_index=figures_index,
        metadata=plan_dict.get("metadata", {}),
    )
    
    if content_type == "paper":
        content = PaperContent(**summary_data["content"])
    else:
        content = GeneralContent(**summary_data["content"])
    
    gen_config = GenerationConfig(
        output_type=OutputType(config.get("output_type", "slides")),
        poster_density=PosterDensity(config.get("poster_density", "medium")),
        slides_length=SlidesLength(config.get("slides_length", "medium")),
        style=StyleType(config.get("style", "academic")),
        custom_style=config.get("custom_style"),
    )
    gen_input = GenerationInput(config=gen_config, content=content, origin=origin)
    
    logger.info("Generating images...")
    
    # Prepare output directory
    output_subdir = get_output_dir(config_dir)
    output_subdir.mkdir(parents=True, exist_ok=True)
    ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    
    # Save callback: save each image immediately after generation
    def save_image_callback(img, index, total):
        ext = ext_map.get(img.mime_type, ".png")
        filepath = output_subdir / f"{img.section_id}{ext}"
        with open(filepath, "wb") as f:
            f.write(img.image_data)
        logger.info(f"  [{index+1}/{total}] Saved: {filepath.name}")
    
    image_api_key = os.getenv("IMAGE_GEN_API_KEY", "")
    
    if not image_api_key:
        logger.warning("IMAGE_GEN_API_KEY not set. Generating placeholder slides locally.")
        images = _generate_placeholder_images(plan, gen_input, output_subdir)
    else:
        generator = ImageGenerator()
        max_workers = config.get("max_workers", 1)
        images = generator.generate(plan, gen_input, max_workers=max_workers, save_callback=save_image_callback)
    
    logger.info(f"  Generated {len(images)} images")
    
    # Generate PDF for slides
    output_type = config.get("output_type", "slides")
    if output_type == "slides" and len(images) > 1:
        pdf_path = output_subdir / "slides.pdf"
        save_images_as_pdf(images, str(pdf_path))
        logger.info(f"  Saved: slides.pdf")
    
    logger.info("")
    logger.info(f"Output: {output_subdir}")
    
    return {"output_dir": str(output_subdir), "num_images": len(images)}


def _generate_placeholder_images(plan, gen_input, output_subdir):
    """Generate simple text-based placeholder images when image API is unavailable."""
    from paper2slides.generator.image_generator import GeneratedImage
    from PIL import Image, ImageDraw, ImageFont
    import io
    import textwrap
    
    output_subdir.mkdir(parents=True, exist_ok=True)
    images = []
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    LINE_SPACING = 6
    MAX_TEXT_HEIGHT = 680
    
    for idx, section in enumerate(plan.sections):
        img = Image.new("RGB", (1280, 720), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        title = section.title or f"Slide {idx+1}"
        draw.text((40, 30), title, fill=(0, 0, 0), font=title_font)
        
        content = section.content or gen_input.get_summary_text()
        y = 90
        for paragraph in content.splitlines():
            wrapped = textwrap.wrap(paragraph, width=90) or [""]
            for line in wrapped:
                draw.text((40, y), line, fill=(30, 30, 30), font=body_font)
                y += body_font.getbbox("Ag")[3] + LINE_SPACING
                if y > MAX_TEXT_HEIGHT:
                    break
            if y > MAX_TEXT_HEIGHT:
                break
            y += 10
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()
        
        section_id = section.id or f"section_{idx+1:02d}"
        filepath = output_subdir / f"{section_id}.png"
        with open(filepath, "wb") as f:
            f.write(data)
        
        images.append(GeneratedImage(section_id=section_id, image_data=data, mime_type="image/png"))
        logger.info(f"  [{idx+1}/{len(plan.sections)}] Saved: {filepath.name} (placeholder)")
    
    return images
