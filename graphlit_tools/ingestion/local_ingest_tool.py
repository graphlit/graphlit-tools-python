import logging
import os
import base64
import mimetypes
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class LocalIngestInput(BaseModel):
    file_path: str = Field(description="Path of local file to be ingested into knowledge base")

class LocalIngestTool(BaseTool):
    name: str = "Graphlit local file ingest tool"
    description: str = """Ingests content from local file.
    Returns extracted Markdown text and metadata from content.
    Can ingest individual Word documents, PDFs, audio recordings, videos, images, or any other unstructured data."""
    args_schema: Type[BaseModel] = LocalIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

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
        content_id = None

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

            logger.debug(f'LocalIngestTool: Retrieved content by ID [{content_id}].')

            results = helpers.format_content(response.content)

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, file_path: str) -> Optional[str]:
        return helpers.run_async(self._arun, file_path)
