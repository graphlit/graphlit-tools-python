import logging
import json
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class ExtractTextInput(BaseModel):
    text: str = Field(description="Text to be extracted with LLM.")
    model: BaseModel = Field(description="Pydantic model which describes the data which will be extracted")
    prompt: Optional[str] = Field(description="Text prompt which is provided to LLM to guide data extraction, optional.", default=None)

class ExtractTextTool(BaseTool):
    name: str = "Graphlit JSON text data extraction tool"
    description: str = """Extracts JSON data from text using LLM.
    Returns extracted JSON from text."""
    args_schema: Type[BaseModel] = ExtractTextInput

    graphlit: Graphlit = Field(None, exclude=True)

    specification_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, specification_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the ExtractTextTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            specification_id (Optional[str]): ID for the LLM specification to use. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.specification_id = specification_id
        self.correlation_id = correlation_id

    async def _arun(self, text: str, model: BaseModel, prompt: Optional[str] = None) -> Optional[str]:
        default_prompt = """
        Extract data using the tools provided.
        """

        try:
            response = await self.graphlit.client.extract_text(
                specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                tools=[input_types.ToolDefinitionInput(name=model.__name__, schema=model.model_dump_json())],
                prompt=default_prompt if prompt is None else prompt,
                text=text,
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

    def _run(self, text: str, model: BaseModel, prompt: Optional[str] = None) -> Optional[str]:
        return helpers.run_async(self._arun, text, model, prompt)
