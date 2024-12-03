from typing import Any, cast

try:
    from crewai_tools.tools.base_tool import BaseTool as CrewAIBaseTool
except ImportError as e:
    raise ImportError(
        "CrewAIConverter requires the `crewai_tools` package. "
        "Install it using `pip install graphlit-tools[crewai]`."
    ) from e

from .base_tool import BaseTool

class CrewAIConverter(CrewAIBaseTool):
    """Tool to convert Graphlit tools into CrewAI tools."""

    graphlit_tool: Any

    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        tool = cast(BaseTool, self.graphlit_tool)

        return tool.run(*args, **kwargs)

    async def _arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        tool = cast(BaseTool, self.graphlit_tool)

        return await tool.arun(*args, **kwargs)

    @classmethod
    def from_tool(cls, tool: Any, **kwargs: Any) -> "BaseTool":
        if not isinstance(tool, BaseTool):
            raise ValueError(f"Expected a Graphlit tool, got {type(tool)}")

        tool = cast(BaseTool, tool)

        if tool.args_schema is None:
            raise ValueError("Invalid arguments JSON schema.")

        return cls(
            name=tool.name,
            description=tool.description,
            args_schema=tool.args_schema,
            graphlit_tool=tool,
            **kwargs,
        )
