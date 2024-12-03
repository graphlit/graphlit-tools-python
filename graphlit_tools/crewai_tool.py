from typing import Any, cast

from crewai_tools.tools.base_tool import BaseTool as CrewAIBaseTool

from .base_tool import BaseTool

class CrewAITool(CrewAIBaseTool):
    """Tool to wrap Graphlit tools into CrewAI tools."""

    graphlit_tool: Any

    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        tool = cast(BaseTool, self.graphlit_tool)

        return tool.run(self, args, kwargs)

    async def _arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        tool = cast(BaseTool, self.graphlit_tool)

        return await tool.arun(self, args, kwargs)

    @classmethod
    def from_tool(cls, tool: Any, **kwargs: Any) -> "BaseTool":
        if not isinstance(tool, BaseTool):
            raise ValueError(f"Expected a Graphlit tool, got {type(tool)}")

        tool = cast(BaseTool, tool)

        if tool.args_schema is None:
            raise ValueError(
                "The Graphlit tool does not have an args_schema specified."
            )

        return cls(
            name=tool.name,
            description=tool.description,
            args_schema=tool.args_schema,
            graphlit_tool=tool,
            **kwargs,
        )
