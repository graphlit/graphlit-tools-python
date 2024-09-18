import asyncio
import logging
from typing import Type, List, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, ContentFilter, QueryContentsContentsResults
from langchain_core.pydantic_v1 import Field
from langchain_core.tools import BaseTool, ToolException

logger = logging.getLogger(__name__)

class RetrievalTool(BaseTool):
    name = "retrieval"
    description = """Retrieves content based on a ContentFilter.
    Can search through web pages, PDFs, and other unstructured data.
    Filters can include query, date ranges, content types, and other criteria."""
    args_schema: Type[ContentFilter] = ContentFilter

    graphlit: Graphlit = Field(exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None):
        super().__init__()
        self.graphlit = graphlit or Graphlit()

    async def _arun(self, content_filter: ContentFilter) -> Optional[List[QueryContentsContentsResults]]:
        try:
            response = await self.graphlit.client.query_contents(
                filter=content_filter
            )

            return response.contents.results if response.contents is not None else None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, content_filter: ContentFilter) -> Optional[List[QueryContentsContentsResults]]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(content_filter))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(content_filter))
        except RuntimeError:
            return asyncio.run(self._arun(content_filter))
