from typing import Any, Dict, cast
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

        graphlit_tool: BaseTool

        @classmethod
        def from_tool(cls, tool: Any, **kwargs: Any) -> "GriptapeConverter":
            if not isinstance(tool, BaseTool):
                raise ValueError(f"Expected a Graphlit tool, got {type(tool)}")

            graphlit_tool = cast(BaseTool, tool)

            if graphlit_tool.args_schema is None:
                raise ValueError("Invalid arguments JSON schema.")

            # Create an instance of GriptapeConverter
            instance = cls(name=graphlit_tool.name, **kwargs)
            instance.graphlit_tool = graphlit_tool

            # Define the generate method dynamically
            def generate(self, params: Dict[str, Any]) -> TextArtifact:
                return TextArtifact(str(self.graphlit_tool.run(**params)))

            # Convert the tool's schema
            tool_schema = Schema(graphlit_tool.json_schema)

            # Decorate the generate method
            decorated_generate = activity(
                config={
                    "description": graphlit_tool.description,
                    "schema": tool_schema,
                }
            )(generate)

            # Attach the dynamically created method to the instance
            setattr(instance, "generate", decorated_generate)

            return instance
else:
    class GriptapeConverter:
        """Fallback GriptapeConverter if griptape is not installed."""

        @classmethod
        def from_tool(cls, tool: Any, **kwargs: Any) -> "GriptapeConverter":
            raise ImportError(
                "GriptapeConverter requires the griptape package. "
                "Install it using pip install graphlit-tools[griptape]."
            )
