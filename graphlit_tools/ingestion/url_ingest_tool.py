import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class URLIngestInput(BaseModel):
    url: str = Field(description="URL of cloud-hosted file to be ingested into knowledge base")

class URLIngestTool(BaseTool):
    name: str = "Graphlit URL ingest tool"
    description: str = """Ingests content from URL.
    Returns extracted Markdown text and metadata from content.
    Can ingest individual Word documents, PDFs, audio recordings, videos, images, or any other unstructured data."""
    args_schema: Type[BaseModel] = URLIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the IngestTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting files. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, url: str) -> Optional[str]:
        content_id = None

        try:
            response = await self.graphlit.client.ingest_uri(
                uri=url,
                workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                is_synchronous=True,
                correlation_id=self.correlation_id
            )

            content_id = response.ingest_uri.id if response.ingest_uri is not None else None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        if content_id is None:
            raise ToolException('Invalid content identifier.')

        try:
            response = await self.graphlit.client.get_content(
                id=content_id
            )

            if response.content is None:
                raise ToolException(f'Failed to get content [{content_id}].')

            logger.debug(f'URLIngestTool: Retrieved content by ID [{content_id}].')

            results = helpers.format_content(response.content)

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str) -> Optional[str]:
        return helpers.run_async(self._arun, url)
