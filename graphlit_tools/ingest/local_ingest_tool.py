import asyncio
import logging
import os
import base64
import mimetypes
from typing import Type, Optional, List
from graphlit import Graphlit
from graphlit_api import exceptions, enums
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class LocalIngestInput(BaseModel):
    file_path: str = Field(description="Path of local file to be ingested into knowledge base")

class LocalIngestOutput(BaseModel):
    id: str = Field(description="ID of ingested content in knowledge base")
    markdown: Optional[str] = Field(description="Markdown text or audio transcript extracted from ingested file")
    links: List[(str, enums.LinkTypes)] = Field(description="List of hyperlinks extracted from ingested file")

class LocalIngestTool(BaseTool):
    name = "Ingest Local File"
    description = """Ingests content from local file. Returns extracted Markdown text or audio transcript from content.
    Can ingest individual Word documents, PDFs, audio recordings, videos, images, or other unstructured data."""
    args_schema: Type[BaseModel] = LocalIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the LocalIngestTool.

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

    async def _arun(self, file_path: str) -> LocalIngestOutput:
        try:
            file_name = os.path.basename(file_path)
            content_name, _ = os.path.splitext(file_name)

            mime_type = mimetypes.guess_type(file_name)[0]

            if mime_type is None:
                logger.error(f'Failed to infer MIME type from file [{file_name}].')
                raise ToolException(f'Failed to infer MIME type from file [{file_name}].')

            with open(file_path, "rb") as file:
                file_content = file.read()

                base64_content = base64.b64encode(file_content).decode('utf-8')

                response = await self.graphlit.client.ingest_encoded_file(content_name, base64_content, mime_type, is_synchronous=True)

                content_id = response.ingest_encoded_file.id if response.ingest_encoded_file is not None else None

                if content_id is None:
                    raise ToolException('Invalid content identifier after ingestion.')

                response = await self.graphlit.client.get_content(content_id)

                content = response.content

                if content is None:
                    raise ToolException('Failed to get content [{content_id}].')

                links = [(link.uri, link.link_type) for link in content.links if link.uri is not None and link.link_type is not None]

                return LocalIngestOutput(id=content.id, markdown=content.markdown, links=links)
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, file_path: str) -> LocalIngestOutput:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(file_path))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(file_path))
        except RuntimeError:
            return asyncio.run(self._arun(file_path))
