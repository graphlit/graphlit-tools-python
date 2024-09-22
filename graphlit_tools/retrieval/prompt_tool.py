import asyncio
import logging
from typing import Type, Optional, List
from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class PromptInput(BaseModel):
    prompt: str = Field(description="User prompt for RAG pipeline")

class PromptOutputCitation(BaseModel):
    index: int = Field(description="Citation index, one-based")
    text: str = Field(description="Relevant text from cited content")
    content_id: str = Field(description="ID of cited content in knowledge base")

class PromptOutput(BaseModel):
    completion: str = Field(description="LLM assistant message return from LLM prompt completion")
    citations: List[PromptOutputCitation] = Field(description="List of citations referenced in LLM assistant message")

class PromptTool(BaseTool):
    name = "Graphlit prompt tool"
    description = """Uses vector embeddings and similarity search to retrieve relevant content from knowledge base.
    Prompts LLM with relevant content and returns completion from RAG pipeline. Returns Markdown text from LLM completion.
    Can search through web pages, PDFs, audio transcripts, and other unstructured data."""
    args_schema: Type[BaseModel] = PromptInput

    graphlit: Graphlit = Field(None, exclude=True)

    conversation_id: Optional[str] = Field(None, exclude=True)
    specification_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, conversation_id: Optional[str] = None, specification_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the PromptTool.

        Args:
            graphlit (Optional[Graphlit]): Instance for interacting with the Graphlit API.
                Defaults to a new Graphlit instance if not provided.
            conversation_id (Optional[str]): ID for the ongoing conversation. Defaults to None.
            specification_id (Optional[str]): ID for the LLM specification. Will update an existing conversation. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.conversation_id = conversation_id
        self.specification_id = specification_id
        self.correlation_id = correlation_id

    async def _arun(self, prompt: str) -> PromptOutput:
        try:
            response = await self.graphlit.client.prompt_conversation(
                id=self.conversation_id,
                # TODO: requires API/SDK update
                #specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                prompt=prompt,
                correlation_id=self.correlation_id
            )

            if response.prompt_conversation is None or response.prompt_conversation.message is None:
                return None

            message = response.prompt_conversation.message

            citations = None

            if message is not None and message.citations:
                citations = [PromptOutputCitation(index=citation.index, text=citation.text, content_id=citation.content.id) for citation in message.citations
                             if citation.content is not None and citation.index is not None and citation.text is not None]

            return PromptOutput(completion=message.message, citations=citations)
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, prompt: str) -> PromptOutput:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(prompt))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(prompt))
        except RuntimeError:
            return asyncio.run(self._arun(prompt))
