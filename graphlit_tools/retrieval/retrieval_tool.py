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
    content_id: Optional[str] = Field(default=None, description="Filter by ID of content which has been ingested into knowledge base. Use to search within a specific piece of content.")
    limit: Optional[int] = Field(default=None, description="Number of contents to return from search query, optional")

class RetrievalTool(BaseTool):
    name = "Graphlit content retrieval tool"
    description = """Accepts search text as string.
    Retrieves contents based on similarity search from knowledge base.
    Returns extracted Markdown text and metadata from contents relevant to the search text.
    Can search through web pages, PDFs, audio transcripts, and other unstructured data."""
    args_schema: Type[BaseModel] = RetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)
    search_type: Optional[enums.SearchTypes] = Field(None, exclude=True)

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

    async def _arun(self, search: str = None, content_id: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            # NOTE: force to one content result, if filtering by content_id
            limit = 1 if content_id is not None else limit

            response = await self.graphlit.client.query_contents(
                filter=input_types.ContentFilter(
                    id=content_id,
                    search=search,
                    searchType=self.search_type if self.search_type is not None else enums.SearchTypes.VECTOR,
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

    def _run(self, search: str = None, content_id: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, content_id, limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, content_id, limit))
        except RuntimeError:
            return asyncio.run(self._arun(search, content_id, limit))
