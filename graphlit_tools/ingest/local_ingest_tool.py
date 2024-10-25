import asyncio
import logging
import os
import base64
import mimetypes
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class LocalIngestInput(BaseModel):
    file_path: str = Field(description="Path of local file to be ingested into knowledge base")

class LocalIngestTool(BaseTool):
    name: str = "Ingest Local File"
    description: str = """Ingests content from local file. Returns the ID of the ingested content in knowledge base.
    Can use LookupTool to return Metadata and extracted Markdown text from content. Or, can use RetrievalTool to search within content by ID and return Metadata and relevant extracted Markdown text chunks.
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

    async def _arun(self, file_path: str) -> Optional[str]:
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

                return response.ingest_encoded_file.id if response.ingest_encoded_file is not None else None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, file_path: str) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(file_path))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(file_path))
        except RuntimeError:
            return asyncio.run(self._arun(file_path))
