import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class WebSearchInput(BaseModel):
    search: str = Field(description="Text to search for within web pages across the Internet")
    search_limit: Optional[int] = Field(description="Maximum number of web pages to be returned from web search", default=10)

class WebSearchTool(BaseTool):
    name: str = "Graphlit web search tool"
    description: str = """Accepts search query as string.
    Performs web search based on search query. Format the search query as what would be entered into a Google search.
    Returns URL, title and relevant Markdown text from resulting web pages."""
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
                service=enums.SearchServiceTypes.TAVILY,
                text=search,
                limit=search_limit,
                correlation_id=self.correlation_id
            )

            results = response.search_web.results if response.search_web is not None else None

            if results is not None:
                logger.debug(f'Completed web search, found [{len(results)}] results.')

                return '\n\n'.join(f'URL: {result.uri}\nTitle: {result.title}\n\n{result.text}' for result in results) if results is not None else None
            else:
                return None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: str, search_limit: Optional[int] = None) -> Optional[str]:
        return helpers.run_async(self._arun, search, search_limit)
