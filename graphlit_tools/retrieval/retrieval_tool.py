import asyncio
import logging
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class RetrievalInput(BaseModel):
    search: Optional[str] = Field(description="Text to search for in contents")
    limit: Optional[int] = Field(description="Number of contents to return from search query")

class RetrievalTool(BaseTool):
    name = "Retrieval"
    description = """Retrieves contents based on similarity search from knowledge base. Returns Markdown extracted from contents.
    Can search through web pages, PDFs, audio transcripts, and other unstructured data."""
    args_schema: Type[BaseModel] = RetrievalInput

    graphlit: Graphlit = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, **kwargs):
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()

    async def _arun(self, search: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.query_contents(
                filter=input_types.ContentFilter(
                    search=search,
                    searchType=enums.SearchTypes.HYBRID,
                    limit=limit if limit is not None else 10 # NOTE: default to 10 relevant contents
                )
            )

            if response.contents is None or response.contents.results is None:
                return None

            results = []

            for content in response.contents.results:
                if content.type == enums.ContentTypes.FILE:
                    results.append(f'## {content.file_type}: {content.file_name}')
                else:
                    results.append(f'## {content.type}: {content.name}')

                if content.uri is not None:
                    results.append(f'### URI {content.uri}')

                if content.document is not None:
                    if content.document.title is not None:
                        results.append(f'### Title {content.document.title}')

                    if content.document.author is not None:
                        results.append(f'### Author {content.document.author}')

                if content.audio is not None:
                    if content.audio.title is not None:
                        results.append(f'### Title {content.audio.title}')

                    if content.audio.author is not None:
                        results.append(f'### Host {content.audio.author}')

                    if content.audio.episode is not None:
                        results.append(f'### Episode {content.audio.episode}')

                    if content.audio.series is not None:
                        results.append(f'### Series {content.audio.series}')

                if content.pages is not None:
                    for page in content.pages:
                        if page.chunks is not None and len(page.chunks) > 0:
                            results.append(f'### Page #{page.index + 1}')

                            for chunk in page.chunks:
                                results.append(chunk.text)

                            results.append('\n')

                if content.segments is not None:
                    for segment in content.segments:
                        if segment.chunks is not None and len(segment.chunks) > 0:
                            results.append(f'### Transcript Segment [{segment.start_time}-{segment.end_time}]')

                            for chunk in segment.chunks:
                                results.append(chunk.text)

                            results.append('\n')

                results.append('\n')

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: Optional[str] = None, limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, limit))
        except RuntimeError:
            return asyncio.run(self._arun(search, limit))
