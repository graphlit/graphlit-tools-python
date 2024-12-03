import asyncio
import logging
from typing import Optional, Type, List

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class ContentRetrievalInput(BaseModel):
    search: str = Field(description="Text to search for within the knowledge base")
    types: Optional[List[enums.ContentTypes]] = Field(description="List of content types to be returned from knowledge base, optional")
    limit: Optional[int] = Field(default=None, description="Number of contents to return from search query, optional")

class ContentRetrievalTool(BaseTool):
    name: str = "Graphlit content retrieval tool"
    description: str = """Accepts search text as string.
    Optionally accepts a list of content types (i.e. FILE, PAGE, EMAIL, ISSUE, MESSAGE) for filtering the result set.
    Retrieves contents based on similarity search from knowledge base.
    Returns extracted Markdown text and metadata from contents relevant to the search text.
    Can search through web pages, PDFs, audio transcripts, Slack messages, emails, or any unstructured data ingested into the knowledge base."""
    args_schema: Type[BaseModel] = ContentRetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)
    search_type: Optional[enums.SearchTypes] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, search_type: Optional[enums.SearchTypes] = None, **kwargs):
        """
        Initializes the RetrievalTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            search_type (Optional[SearchTypes]): An optional enum specifying the type of search to use: VECTOR, HYBRID or KEYWORD.
                If not provided, vector search will be used.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.search_type = search_type

    async def _arun(self, search: str = None, types: Optional[List[enums.ContentTypes]] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.query_contents(
                filter=input_types.ContentFilter(
                    types=types,
                    search=search,
                    searchType=self.search_type if self.search_type is not None else enums.SearchTypes.HYBRID,
                    limit=limit if limit is not None else 10 # NOTE: default to 10 relevant contents
                )
            )

            if response.contents is None or response.contents.results is None:
                return None

            print(f'ContentRetrievalTool: Retrieved [{len(response.contents.results)}] content(s) given search text [{search}].')

            results = []

            for content in response.contents.results:
                results.extend(helpers.format_content(content))

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: str = None, types: Optional[List[enums.ContentTypes]] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, types, limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, types, limit))
        except RuntimeError:
            return asyncio.run(self._arun(search, types, limit))
