import asyncio
import logging
from typing import Type, Optional, List
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class IngestInput(BaseModel):
    url: str = Field(description="URL of cloud-hosted file to be ingested into knowledge base")

class IngestOutput(BaseModel):
    id: str = Field(description="ID of ingested content in knowledge base")
    markdown: Optional[str] = Field(description="Markdown text or audio transcript extracted from ingested file")
    links: List[(str, enums.LinkTypes)] = Field(description="List of hyperlinks extracted from ingested file")

class IngestTool(BaseTool):
    name = "Ingest File from URL"
    description = """Ingests content from URL. Returns extracted Markdown text or audio transcript from content.
    Can ingest individual Word documents, PDFs, audio recordings, videos, images, or other unstructured data."""
    args_schema: Type[BaseModel] = IngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

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

    async def _arun(self, url: str) -> IngestOutput:
        try:
            response = await self.graphlit.client.ingest_uri(
                uri=url,
                workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                is_synchronous=True,
                correlation_id=self.correlation_id
            )

            content_id = response.ingest_uri.id if response.ingest_uri is not None else None

            if content_id is None:
                raise ToolException('Invalid content identifier after ingestion.')

            response = await self.graphlit.client.get_content(content_id)

            content = response.content

            if content is None:
                raise ToolException('Failed to get content [{content_id}].')

            links = [(link.uri, link.link_type) for link in content.links if link.uri is not None and link.link_type is not None]

            return IngestOutput(id=content.id, markdown=content.markdown, links=links)
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str) -> IngestOutput:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(url))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(url))
        except RuntimeError:
            return asyncio.run(self._arun(url))
