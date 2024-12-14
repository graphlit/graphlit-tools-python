from abc import abstractmethod
from typing import Any, Type, Dict
from pydantic import BaseModel

class BaseTool(BaseModel):
    """
    Abstract base class for tools.
    
    Attributes:
        name (str): The name of the tool.
        description (str): A short description of the tool's functionality.
        args_schema (Type[BaseModel]): The schema for arguments expected by the tool.
    """
    name: str
    description: str
    args_schema: Type[BaseModel]

    def run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Public method to execute the tool. Delegates to the abstract _run method.

        Args:
            *args (Any): Positional arguments passed to the tool.
            **kwargs (Any): Keyword arguments passed to the tool.

        Returns:
            Any: The result of executing the tool.
        """
        return self._run(*args, **kwargs)

    @abstractmethod
    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Abstract method to define the tool's behavior.

        Subclasses must implement this method to provide the actual logic.

        Args:
            *args (Any): Positional arguments passed to the tool.
            **kwargs (Any): Keyword arguments passed to the tool.

        Returns:
            Any: The result of executing the tool.
        """

    async def arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Public async method to execute the tool. Delegates to the abstract _arun method.

        Args:
            *args (Any): Positional arguments passed to the tool.
            **kwargs (Any): Keyword arguments passed to the tool.

        Returns:
            Any: The result of executing the tool asynchronously.
        """
        return await self._arun(*args, **kwargs)

    @abstractmethod
    async def _arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Abstract async method to define the tool's asynchronous behavior.

        Subclasses must implement this method to provide the actual async logic.

        Args:
            *args (Any): Positional arguments passed to the tool.
            **kwargs (Any): Keyword arguments passed to the tool.

        Returns:
            Any: The result of executing the tool asynchronously.
        """

    @property
    def json_schema(self) -> Dict[str, Any]:
        """Get the tool's JSON schema."""
        return self.args_schema.model_json_schema()

    def to_openai_tool(self) -> Dict[str, Any]:
        """
        Creates a tool definition compatible with OpenAI tool calling.

        Returns:
            dict: The tool definition for OpenAI.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.json_schema
        }
