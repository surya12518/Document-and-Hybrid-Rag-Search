from langchain.tools import tool
from collections import Counter
import pandas as pd
from typing import List, Dict

# --- MCP / LangChain Tools ---

@tool
def lookup_paper_metadata(paper_title: str):
    """Useful for finding year, citations, and venue for a specific paper title."""
    # Simulation of an external API call (e.g., Semantic Scholar)
    return {
        "title": paper_title,
        "citations": 145,
        "year": 2023,
        "venue": "NeurIPS"
    }

@tool
def identify_emerging_trends(topic: str):
    """Analyzes the paper database to find rising keywords over time."""
    # In a real app, this would query the internal database
    return f"Trends for {topic}: 'Prompt Engineering' (+40% YoY), 'LoRA' (+25% YoY)."

# --- Analytics Functions ---

def generate_trend_data(papers: List):
    """Aggregates keywords/topics by year for visualization."""
    data = []
    for p in papers:
        # Heuristic: Use first word of title as a 'topic' for demo purposes
        topic = p.title.split()[0] if p.title else "General"
        data.append({"Year": p.year, "Topic": topic, "Count": 1})
    
    df = pd.DataFrame(data)
    if not df.empty:
        df_grouped = df.groupby(['Year', 'Topic']).sum().reset_index()
        return df_grouped
    return pd.DataFrame(columns=["Year", "Topic", "Count"])

