from typing import Any, cast
from schema import Schema
from .base_tool import BaseTool

GriptapeBaseTool: Any = None

try:
    from griptape.tools import BaseTool as GriptapeBaseTool
    from griptape.utils.decorators import activity
    from griptape.artifacts import TextArtifact
except ImportError:
    GriptapeBaseTool = None

if GriptapeBaseTool:
    class GriptapeConverter(GriptapeBaseTool):
        """Tool to convert Graphlit tools into Griptape tools."""

        @classmethod
        def from_tool(cls, tool: Any, **kwargs: Any) -> "GriptapeConverter":
            if not isinstance(tool, BaseTool):
                raise ValueError(f"Expected a Graphlit tool, got {type(tool)}")

            tool = cast(BaseTool, tool)

            if tool.args_schema is None:
                raise ValueError("Invalid arguments JSON schema.")

            def generate(self, params: dict[str, Any]) -> TextArtifact:
                return TextArtifact(str(tool.run(**params)))

            tool_schema = Schema(tool.json_schema)

            decorated_generate = activity(
                config={
                    "description": tool.description,
                    "schema": tool_schema,
                }
            )(generate)

            new_cls = type(
                "GriptapeConverter",
                (cls,),
                {"generate": decorated_generate},
            )

            return new_cls(
                name=tool.name,
                **kwargs,
            )
else:
    class GriptapeConverter:
        """Fallback GriptapeConverter if griptape is not installed."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "GriptapeConverter requires the griptape package. "
                "Install it using pip install graphlit-tools[griptape]."
            )
