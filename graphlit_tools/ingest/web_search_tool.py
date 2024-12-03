import asyncio
import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException

logger = logging.getLogger(__name__)

class WebSearchInput(BaseModel):
    search: str = Field(description="Search query for web pages to be ingested into knowledge base")
    read_limit: Optional[int] = Field(default=None, description="Maximum number of web pages from web search to be ingested")

class WebSearchTool(BaseTool):
    name: str = "Graphlit web search tool"
    description: str = """Accepts search query text as string.
    Performs web search based on search query, and ingests the related web pages into knowledge base. Returns Markdown extracted from web pages."""
    args_schema: Type[BaseModel] = WebSearchInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, correlation_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.correlation_id = correlation_id

    async def _arun(self, search: str, search_limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.search_web(
                type=enums.SearchServiceTypes.TAVILY,
                text=search,
                limit=search_limit,
                correlation_id=self.correlation_id
            )

            results = response.search_web.results if response.search_web is not None else None

            if results is not None:
                logger.debug(f'Completed web search, found [{len(results)}] results.')

                return '\n\n'.join(result.text for result in results) if results is not None else None
            else:
                return None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: str, search_limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, search_limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, search_limit))
        except RuntimeError:
            return asyncio.run(self._arun(search))
