from typing import List
from crawler_engine.models import CrawledPage

def clean_markdown(text: str) -> str:
    # Basic cleanup to avoid excessive whitespace
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if line.strip():
            cleaned.append(line.strip())
    return '\n\n'.join(cleaned)

def build_kb(pages: List[CrawledPage]) -> str:
    kb_parts = []
    kb_parts.append("# Website Knowledge Base")
    kb_parts.append("This document contains extracted information from the crawled website.\n")
    
    # Sort pages: home first, then others by depth
    sorted_pages = sorted(pages, key=lambda x: (x.page_type != "home", x.depth, x.url))
    
    for page in sorted_pages:
        if not page.markdown.strip():
            continue
            
        kb_parts.append(f"## Page: {page.title or page.page_type.title()}")
        kb_parts.append(f"**Source:** {page.url}\n")
        
        cleaned_md = clean_markdown(page.markdown)
        
        # Limit page size so we don't blow up context too much
        if len(cleaned_md) > 15000:
            cleaned_md = cleaned_md[:15000] + "\n...[truncated]"
            
        kb_parts.append(cleaned_md)
        kb_parts.append("\n---\n")
        
    return "\n".join(kb_parts)
