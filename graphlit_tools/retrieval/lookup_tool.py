import asyncio
import logging
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel
from . import helpers

logger = logging.getLogger(__name__)

class LookupInput(BaseModel):
    content_id: str = Field(description="ID of content which has been ingested into knowledge base")

class LookupTool(BaseTool):
    name: str = "Graphlit content lookup tool"
    description: str = """Retrieves content by ID from knowledge base.
    Returns extracted Markdown text and metadata from content."""
    args_schema: Type[BaseModel] = LookupInput

    graphlit: Graphlit = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, **kwargs):
        """
        Initializes the LookupTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()

    async def _arun(self, content_id: str) -> Optional[str]:
        try:
            response = await self.graphlit.client.get_content(
                id=content_id
            )

            if response.content is None:
                return None

            print(f'LookupTool: Retrieved content by ID [{content_id}].')

            results = helpers.format_content(response.content)

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, content_id: str) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(content_id))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(content_id))
        except RuntimeError:
            return asyncio.run(self._arun(content_id))
