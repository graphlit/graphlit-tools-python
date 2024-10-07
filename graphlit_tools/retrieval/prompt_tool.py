import asyncio
import logging
import json
from typing import Type, Optional, List, Callable
from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

"""
Example of tool callback function:
def callback(tool_name, **kwargs):
    if tool_name == 'add_numbers':
        return add_numbers(**kwargs)
    elif tool_name == 'concat_strings':
        return concat_strings(**kwargs)
    else:
        return None
"""

class PromptInput(BaseModel):
    prompt: str = Field(description="Text prompt which is provided to LLM for completion, via RAG pipeline.")

class PromptToolInput(BaseModel):
    name: str = Field(description="Tool name.")
    description: Optional[str] = Field(description="Tool description.")
    parameters: dict = Field(description="JSON schema for tool parameters.")
    callback: Callable[..., Optional[str]] = Field(description="Function which gets called back upon tool call")

class PromptTool(BaseTool):
    name = "Graphlit RAG prompt tool"
    description = """Accepts user prompt as string.
    Prompts LLM with relevant content and returns completion from RAG pipeline. Returns Markdown text from LLM completion.
    Uses vector embeddings and similarity search to retrieve relevant content from knowledge base.
    Can search through web pages, PDFs, audio transcripts, and other unstructured data."""
    args_schema: Type[BaseModel] = PromptInput

    graphlit: Graphlit = Field(None, exclude=True)

    conversation_id: Optional[str] = Field(None, exclude=True)
    specification_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    tools: Optional[List[PromptToolInput]] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, conversation_id: Optional[str] = None, specification_id: Optional[str] = None,
                 tools: Optional[List[PromptToolInput]] = None,
                 correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the PromptTool.

        Args:
            graphlit (Optional[Graphlit]): Instance for interacting with the Graphlit API.
                Defaults to a new Graphlit instance if not provided.
            conversation_id (Optional[str]): ID for the ongoing conversation. Defaults to None.
            specification_id (Optional[str]): ID for the LLM specification. Will update an existing conversation. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            tools (Optional[List[ToolInput]]): List of tools provided to LLM. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.conversation_id = conversation_id
        self.specification_id = specification_id
        self.tools = tools
        self.correlation_id = correlation_id

    async def _arun(self, prompt: str) -> str:
        try:
            response = await self.graphlit.client.prompt_conversation(
                id=self.conversation_id,
                specification=input_types.EntityReferenceInput(id=self.specification_id) if self.specification_id is not None else None,
                prompt=prompt,
                tools=[input_types.ToolDefinitionInput(name=tool.name, description=tool.description, schema=json.dumps(tool.parameters)) for tool in self.tools if tool.name is not None and tool.parameters is not None] if self.tools is not None else None,
                correlation_id=self.correlation_id
            )

            if response.prompt_conversation is None or response.prompt_conversation.conversation is None or response.prompt_conversation.message is None:
                print('Failed to prompt conversation.')
                return None

            message = response.prompt_conversation.message

            if self.tools is not None and message.tool_calls is not None:
                responses = []

                for tool_call in message.tool_calls:
                    tool = next((x for x in self.tools if x.name == tool_call.name), None)

                    if tool is not None:
                        arguments = json.loads(tool_call.arguments)

                        if asyncio.iscoroutinefunction(tool.callback):
                            content = await tool.callback(**arguments)
                        else:
                            content = tool.callback(**arguments)

                        if content is not None:
                            responses.append(input_types.ConversationToolResponseInput(id=tool_call.id, content=content))

                if len(responses) > 0:
                    response = await self.graphlit.client.continue_conversation(
                        id=response.prompt_conversation.conversation.id,
                        responses=responses,
                        correlation_id=self.correlation_id
                    )

                    if response.continue_conversation is None or response.continue_conversation.message is None:
                        return None

                    return response.continue_conversation.message.message if response.continue_conversation.message is not None else None
                else:
                    return message.message
            else:
                return message.message
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e
        except Exception as e:
            logger.error(str(e))
            print(str(e))
            raise ToolException(str(e)) from e

    def _run(self, prompt: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(prompt))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(prompt))
        except RuntimeError:
            return asyncio.run(self._arun(prompt))
