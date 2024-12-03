import asyncio
import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class OrganizationRetrievalInput(BaseModel):
    search: str = Field(description="Text to search for within the knowledge base")
    limit: Optional[int] = Field(default=None, description="Number of organizations to return from search query, optional")

class OrganizationRetrievalTool(BaseTool):
    name: str = "Graphlit organization retrieval tool"
    description: str = """Accepts search text as string.
    Retrieves organizations based on similarity search from knowledge base.
    Returns metadata from organizations relevant to the search text."""
    args_schema: Type[BaseModel] = OrganizationRetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)
    search_type: Optional[enums.SearchTypes] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, search_type: Optional[enums.SearchTypes] = None, **kwargs):
        """
        Initializes the OrganizationRetrievalTool.

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

    async def _arun(self, search: str = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.query_organizations(
                filter=input_types.OrganizationFilter(
                    search=search,
                    searchType=self.search_type if self.search_type is not None else enums.SearchTypes.HYBRID,
                    limit=limit if limit is not None else 10 # NOTE: default to 10 relevant organizations
                )
            )

            if response.organizations is None or response.organizations.results is None:
                return None

            print(f'OrganizationRetrievalTool: Retrieved [{len(response.organizations.results)}] organization(s) given search text [{search}].')

            results = []

            for organization in response.organizations.results:
                results.extend(helpers.format_organization(organization))

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
