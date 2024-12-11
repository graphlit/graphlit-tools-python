import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class GenerateSummaryInput(BaseModel):
    text: str = Field(description="Text to be summarized")
    prompt: Optional[str] = Field(description="Text prompt which is provided to LLM for text summarization, optional.", default=None)

class GenerateSummaryTool(BaseTool):
    name: str = "Graphlit summary generation tool"
    description: str = """Accepts text as string.
    Optionally accepts text prompt to be provided to LLM for text summarization.
    Returns summary as text."""
    args_schema: Type[BaseModel] = GenerateSummaryInput

    graphlit: Graphlit = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    specification_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, specification_id: Optional[str] = None,
                 correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the GenerateSummaryTool.

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

    async def _arun(self, text: str, prompt: Optional[str] = None) -> str:
        try:
            response = await self.graphlit.client.summarize_text(
                text=text,
                summarization=input_types.SummarizationStrategyInput(
                    type=enums.SummarizationTypes.SUMMARY if prompt is None else enums.SummarizationTypes.CUSTOM,
                    prompt=prompt,
                    specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                ),
                correlation_id=self.correlation_id
            )

            if response.summarize_text is None or response.summarize_text.items is None:
                raise ToolException('Failed to generate summary.')

            items = response.summarize_text.items

            item = items[0] if response.summarize_text.items is not None and len(response.summarize_text.items) > 0 else None

            return item.text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e
        except Exception as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e

    def _run(self, text: str, prompt: Optional[str] = None) -> str:
        return helpers.run_async(self._arun, text, prompt)
