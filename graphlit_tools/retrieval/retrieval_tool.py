import asyncio
import logging
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel
from . import helpers

logger = logging.getLogger(__name__)

class RetrievalInput(BaseModel):
    search: str = Field(description="Text to search for within the knowledge base")
    limit: Optional[int] = Field(description="Number of contents to return from search query")

class RetrievalTool(BaseTool):
    name = "Graphlit content retrieval tool"
    description = """Retrieves contents based on similarity search from knowledge base. Uses search text to locate relevant contents.
    Returns ID and metadata from relevant contents.
    Can search through web pages, PDFs, audio transcripts, and other unstructured data."""
    args_schema: Type[BaseModel] = RetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, **kwargs):
        """
        Initializes the RetrievalTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()

    async def _arun(self, search: str = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.query_contents(
                filter=input_types.ContentFilter(
                    search=search,
                    searchType=enums.SearchTypes.HYBRID,
                    limit=limit if limit is not None else 10 # NOTE: default to 10 relevant contents
                )
            )

            if response.contents is None or response.contents.results is None:
                return None

            print(f'RetrievalTool: Retrieved [{len(response.contents.results)}] content(s) given search text [{search}].')

            results = []

            for content in response.contents.results:
                results.extend(helpers.format_content(content))

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: str = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, limit))
        except RuntimeError:
            return asyncio.run(self._arun(search, limit))
