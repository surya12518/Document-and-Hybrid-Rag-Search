from langchain_community.tools.tavily_search import TavilySearchResults
from models import DocumentChunk, SourceType

class WebSearcher:
    def __init__(self):
        self.tool = TavilySearchResults(max_results=3)

    def search(self, query: str) -> list[DocumentChunk]:
        try:
            results = self.tool.invoke({"query": query})
            chunks = []
            for res in results:
                chunks.append(DocumentChunk(
                    chunk_id="web",
                    source_id="tavily",
                    source_type=SourceType.WEB,
                    title="Web Result",
                    content=res['content'],
                    url=res['url']
                ))
            return chunks
        except Exception as e:
            print(f"Tavily Error: {e}")
            return []