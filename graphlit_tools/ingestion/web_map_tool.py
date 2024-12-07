import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class WebMapInput(BaseModel):
    url: str = Field(description="URL of the web page to be mapped")

class WebMapTool(BaseTool):
    name: str = "Graphlit web map tool"
    description: str = """Accepts web page URL as string.
    Enumerates the web pages at or beneath the provided URL using web sitemap.
    Returns list of mapped URIs from web site."""
    args_schema: Type[BaseModel] = WebMapInput

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

    async def _arun(self, url: str) -> Optional[str]:
        try:
            response = await self.graphlit.client.map_web(
                uri=url,
                correlation_id=self.correlation_id
            )

            results = response.map_web.results if response.map_web is not None else None

            if results is not None:
                logger.debug(f'Completed web map, found [{len(results)}] results.')

                return '\n'.join(result for result in results) if results is not None else None
            else:
                return None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str) -> Optional[str]:
        return helpers.run_async(self._arun, url)
