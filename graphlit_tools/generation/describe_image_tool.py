import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class DescribeImageInput(BaseModel):
    url: str = Field(description="URL for image to be described with vision LLM")
    prompt: str = Field(description="Text prompt which is provided to vision LLM for completion")

class DescribeImageTool(BaseTool):
    name: str = "Graphlit image description tool"
    description: str = """Accepts image URL as string.
    Prompts vision LLM and returns completion. Returns Markdown text from LLM completion."""
    args_schema: Type[BaseModel] = DescribeImageInput

    graphlit: Graphlit = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    specification_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, specification_id: Optional[str] = None,
                 correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the DescribeImageTool.

        Args:
            graphlit (Optional[Graphlit]): Instance for interacting with the Graphlit API.
                Defaults to a new Graphlit instance if not provided.
            specification_id (Optional[str]): ID for the LLM specification. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.specification_id = specification_id
        self.correlation_id = correlation_id

    async def _arun(self, prompt: str, url: str) -> str:
        try:
            response = await self.graphlit.client.describe_image(
                specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                prompt=prompt,
                uri=url,
                correlation_id=self.correlation_id
            )

            if response.describe_image is None or response.describe_image.message is None:
                raise ToolException('Failed to describe image.')

            message = response.describe_image.message

            return message.message
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e
        except Exception as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e

    def _run(self, prompt: str, url: str) -> str:
        return helpers.run_async(self._arun, prompt, url)
