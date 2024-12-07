import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class PersonRetrievalInput(BaseModel):
    search: str = Field(description="Text to search for within the knowledge base")
    email: Optional[str] = Field(description="Email of person to retrieve.", default=None)
    limit: Optional[int] = Field(description="Number of persons to return from search query, optional.", default=10)

class PersonRetrievalTool(BaseTool):
    name: str = "Graphlit person retrieval tool"
    description: str = """Accepts search text as string. Optionally, accepts person email as string.
    Retrieves persons based on similarity search from knowledge base.
    Returns metadata from persons relevant to the search text."""
    args_schema: Type[BaseModel] = PersonRetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)
    search_type: Optional[enums.SearchTypes] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, search_type: Optional[enums.SearchTypes] = None, **kwargs):
        """
        Initializes the PersonRetrievalTool.

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

    async def _arun(self, search: str = None, email: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.query_persons(
                filter=input_types.PersonFilter(
                    search=search,
                    email=email,
                    searchType=self.search_type if self.search_type is not None else enums.SearchTypes.HYBRID,
                    limit=limit if limit is not None else 10 # NOTE: default to 10 relevant persons
                )
            )

            if response.persons is None or response.persons.results is None:
                return None

            logger.debug(f'PersonRetrievalTool: Retrieved [{len(response.persons.results)}] person(s) given search text [{search}].')

            results = []

            for person in response.persons.results:
                results.extend(helpers.format_person(person))

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: str = None, email: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        return helpers.run_async(self._arun, search, email, limit)
