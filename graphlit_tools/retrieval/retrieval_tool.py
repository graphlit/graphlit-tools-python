import asyncio
import logging
from typing import Type, List, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types, QueryContentsContentsResults
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class RetrievalInput(BaseModel):
    search: Optional[str] = Field(description="Text to search for in contents")
    limit: Optional[int] = Field(description="Number of contents to return from search query")

class RetrievalTool(BaseTool):
    name = "retrieval"
    description = """Retrieves content based on similarity search from knowledge base.
    Can search through web pages, PDFs, audio transcripts, and other unstructured data."""
    args_schema: Type[BaseModel] = RetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, **kwargs):
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()

    async def _arun(self, search: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.query_contents(
                filter=input_types.ContentFilter(
                    search=search,
                    searchType=enums.SearchTypes.HYBRID,
                    limit=limit
                )
            )

            if response.contents is None or response.contents.results is None:
                return None
            
            return "\n\n".join([result.markdown for result in response.contents.results])
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, limit))
        except RuntimeError:
            return asyncio.run(self._arun(search, limit))
