import logging
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class DescribeWebPageInput(BaseModel):
    url: str = Field(description="URL of web page to screenshot and ingest into knowledge base")
    prompt: Optional[str] = Field(description="Text prompt which is provided to vision LLM for screenshot description, optional", default=None)

class DescribeWebPageTool(BaseTool):
    name: str = "Graphlit screenshot web page tool"
    description: str = """Screenshots web page from URL and describes web page with vision LLM.
    Returns Markdown description of screenshot and extracted Markdown text from image."""
    args_schema: Type[BaseModel] = DescribeWebPageInput

    graphlit: Graphlit = Field(None, exclude=True)

    specification_id: Optional[str] = Field(None, exclude=True)
    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, specification_id: Optional[str] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the DescribeWebPageTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting files. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.specification_id = specification_id
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, url: str, prompt: Optional[str] = None) -> Optional[str]:
        content_id = None

        try:
            response = await self.graphlit.client.screenshot_page(
                uri=url,
                workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                is_synchronous=True,
                correlation_id=self.correlation_id
            )

            content_id = response.screenshot_page.id if response.screenshot_page is not None else None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        if content_id is None:
            raise ToolException('Invalid content identifier.')

        content = None

        try:
            response = await self.graphlit.client.get_content(
                id=content_id
            )

            if response.content is None:
                raise ToolException(f'Failed to get content [{content_id}].')

            logger.debug(f'DescribeWebPageTool: Retrieved content by ID [{content_id}].')

            content = response.content
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        if content.image_uri is None:
            raise ToolException(f'Invalid image URI for content [{content_id}].')

        # NOTE: if we've already analyzed the image, via workflow, return the image description
        if content.image.description is not None:
            return content.image.description

        default_prompt = """
        Conduct a thorough analysis of the screenshot, with a particular emphasis on the textual content and any included imagery. 
        Provide a detailed examination of the text, highlighting key points and dissecting technical terms, named entities, and data presentations that contribute to the understanding of the subject matter. 
        Discuss how the technical language and the named entities relate to the overarching topic and objectives of the webpage. 
        Also, describe how the visual elements, such as color schemes, imagery, and branding elements like logos and taglines, support the textual message and enhance the viewer's comprehension of the content. 
        Assess the readability and organization of the content, and evaluate how these aspects facilitate the visitor's navigation and learning experience. Refrain from delving into the specifics of the user interface design but focus on the communication effectiveness and coherence of visual and textual elements. 
        Finally, offer a comprehensive view of the website's ability to convey its message and fulfill its intended commercial, educational, or promotional role, considering the target audience's perspective and potential engagement with the content.

        Carefully examine the image for any text it contains and extract as Markdown text. 
        In cases where the image contains no extractable text or only text that is not useful for understanding, don't extract any text. 
        Focus on including text that contributes significantly to understanding the image, such as titles, headings, key phrases, important data points, or labels. 
        Exclude any text that is not relevant or does not add value to the comprehension of the image. 
        Ensure to transcribe the text completely, without truncating with ellipses.
        """

        # otherwise, describe the screenshot and return image description
        try:
            response = await self.graphlit.client.describe_image(
                specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                prompt=default_prompt if prompt is None else prompt,
                uri=content.image_uri,
                correlation_id=self.correlation_id
            )

            if response.describe_image is None or response.describe_image.message is None:
                raise ToolException('Failed to describe screenshot.')

            return response.describe_image.message
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e
        except Exception as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str, prompt: Optional[str] = None) -> Optional[str]:
        return helpers.run_async(self._arun, url, prompt)
