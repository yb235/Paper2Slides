"""
Plan Stage - Content planning
"""
import os
import logging
from pathlib import Path
from typing import Dict

from ...utils import load_json, save_json
from ..paths import get_summary_checkpoint, get_plan_checkpoint

logger = logging.getLogger(__name__)


async def run_plan_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict:
    """Stage 3: Plan content sections."""
    from paper2slides.summary import PaperContent, GeneralContent, TableInfo, FigureInfo, OriginalElements
    from paper2slides.generator import (
        GenerationConfig, GenerationInput, ContentPlanner,
        OutputType, PosterDensity, SlidesLength, StyleType,
    )
    
    summary_data = load_json(get_summary_checkpoint(base_dir, config))
    if not summary_data:
        raise ValueError("Missing summary checkpoint.")
    
    content_type = summary_data.get("content_type", "paper")
    
    if content_type == "paper":
        content = PaperContent(**summary_data["content"])
    else:
        content = GeneralContent(**summary_data["content"])
    
    origin_data = summary_data["origin"]
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
    tables_index = {t.table_id: t for t in origin.tables}
    figures_index = {f.figure_id: f for f in origin.figures}
    
    gen_config = GenerationConfig(
        output_type=OutputType(config.get("output_type", "slides")),
        poster_density=PosterDensity(config.get("poster_density", "medium")),
        slides_length=SlidesLength(config.get("slides_length", "medium")),
        style=StyleType(config.get("style", "academic")),
        custom_style=config.get("custom_style"),
    )
    
    gen_input = GenerationInput(config=gen_config, content=content, origin=origin)
    
    logger.info("Planning content...")
    api_key = os.getenv("RAG_LLM_API_KEY", "")
    base_url = os.getenv("RAG_LLM_BASE_URL")
    
    if not api_key:
        logger.warning("RAG_LLM_API_KEY not set. Using offline heuristic planner.")
        plan = _offline_plan(gen_input, tables_index, figures_index)
    else:
        planner = ContentPlanner(api_key=api_key, base_url=base_url, model="gpt-4o")
        plan = planner.plan(gen_input)
    
    logger.info(f"  Generated {len(plan.sections)} sections:")
    for i, section in enumerate(plan.sections):
        logger.info(f"    [{i+1}] {section.title} ({section.section_type})")
    
    result = {
        "plan": plan.to_dict(),
        "origin": origin_data,
        "content_type": content_type,
    }
    
    checkpoint_path = get_plan_checkpoint(config_dir)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_json(checkpoint_path, result)
    logger.info(f"  Saved: {checkpoint_path}")
    return result


def _offline_plan(gen_input, tables_index, figures_index):
    """Simple heuristic content plan when LLM is unavailable."""
    from paper2slides.generator.content_planner import Section, ContentPlan
    
    summary = gen_input.get_summary_text()
    min_pages, max_pages = gen_input.config.get_page_range()
    num_sections = max(min_pages, 3)
    
    chunk_size = max(len(summary) // num_sections, 300)
    sections = []
    
    for i in range(num_sections):
        start = i * chunk_size
        chunk = summary[start:start + chunk_size].strip()
        if not chunk and i == 0:
            chunk = "Summary not available."
        section_type = "opening" if i == 0 else "ending" if i == num_sections - 1 else "content"
        title = "Overview" if i == 0 else "Details" if i < num_sections - 1 else "Conclusion"
        sections.append(Section(
            id=f"section_{i+1:02d}",
            title=title,
            section_type=section_type,
            content=chunk,
        ))
    
    return ContentPlan(
        output_type=gen_input.config.output_type.value,
        sections=sections,
        tables_index=tables_index,
        figures_index=figures_index,
        metadata={"offline": True, "page_range": gen_input.config.get_page_range()},
    )
