import os
from typing import List, Optional
from pydantic import BaseModel, Field
from pypdf import PdfReader
import re

# --- 1. Data Models ---
class PaperSection(BaseModel):
    title: str
    content: str
    page_start: int

class ResearchPaper(BaseModel):
    paper_id: str
    title: str
    authors: List[str] = []
    abstract: str = ""
    sections: List[PaperSection] = []
    year: int = 2024
    venue: str = "Unknown"
    references: List[str] = []
    full_text: str = ""

# --- 2. PDF Parsing Logic ---
def extract_sections_from_pdf(pdf_path: str) -> ResearchPaper:
    reader = PdfReader(pdf_path)
    full_text = ""
    sections = []
    
    # Simple heuristic to find title (usually first line) and text
    first_page_text = reader.pages[0].extract_text()
    lines = first_page_text.split('\n')
    title = lines[0] if lines else "Untitled"
    
    current_section_title = "Introduction"
    current_section_content = []
    
    # Iterate through pages to build full text and sections
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        full_text += text + "\n"
        
        # Simple heuristic: Lines that are all caps or short might be headers
        # In a real production system, use layout analysis models (like LayoutLM)
        page_lines = text.split('\n')
        for line in page_lines:
            # Detect standard academic headers
            if line.strip().upper() in ["ABSTRACT", "INTRODUCTION", "METHODOLOGY", "RESULTS", "CONCLUSION", "REFERENCES"]:
                # Save previous section
                sections.append(PaperSection(
                    title=current_section_title,
                    content="\n".join(current_section_content),
                    page_start=i
                ))
                current_section_title = line.strip().title()
                current_section_content = []
            else:
                current_section_content.append(line)
    
    # Append final section
    sections.append(PaperSection(
        title=current_section_title,
        content="\n".join(current_section_content),
        page_start=len(reader.pages)
    ))

    # Basic metadata extraction (simulated)
    # In production, use an LLM or regex to extract authors/year from the first page text
    filename = os.path.basename(pdf_path)
    
    return ResearchPaper(
        paper_id=filename,
        title=title,
        full_text=full_text,
        sections=sections,
        abstract=sections[0].content if sections else ""
    )