import logging
import json
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class ExtractURLInput(BaseModel):
    url: str = Field(description="URL of cloud-hosted file to be ingested into knowledge base")
    model: BaseModel = Field(description="Pydantic model which describes the data which will be extracted")
    prompt: Optional[str] = Field(description="Text prompt which is provided to LLM to guide data extraction, optional.", default=None)

class ExtractURLTool(BaseTool):
    name: str = "Graphlit JSON URL data extraction tool"
    description: str = """Extracts JSON data from ingested file using LLM.
    Returns extracted JSON from file."""
    args_schema: Type[BaseModel] = ExtractURLInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    specification_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, specification_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the ExtractURLTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting files. Defaults to None.
            specification_id (Optional[str]): ID for the LLM specification to use. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.specification_id = specification_id
        self.correlation_id = correlation_id

    async def _arun(self, url: str, model: BaseModel, prompt: Optional[str] = None) -> Optional[str]:
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
            return None

        text = None

        try:
            response = await self.graphlit.client.get_content(
                id=content_id
            )

            if response.content is None:
                return None

            logger.debug(f'ExtractURLTool: Retrieved content by ID [{content_id}].')

            results = helpers.format_content(response.content)

            text = "\n".join(results)
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        default_prompt = """
        Extract data using the tools provided.
        """

        try:
            response = await self.graphlit.client.extract_text(
                specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                tools=[input_types.ToolDefinitionInput(name=model.__name__, schema=model.model_dump_json())],
                prompt=default_prompt if prompt is None else prompt,
                text=text,
                text_type=enums.TextTypes.MARKDOWN,
                correlation_id=self.correlation_id
            )

            if response.extract_text is None:
                logger.debug('Failed to extract text.')
                return None

            extractions = response.extract_text

            json_array = json.loads('[' + ','.join(extraction.value for extraction in extractions) + ']')

            return json.dumps(json_array, indent=4)
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e
        except Exception as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str, model: BaseModel, prompt: Optional[str] = None) -> Optional[str]:
        return helpers.run_async(self._arun, url, model, prompt)
