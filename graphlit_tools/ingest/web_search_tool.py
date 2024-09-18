import asyncio
import logging
import time
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class WebSearchInput(BaseModel):
    search: str = Field(description="Search query for web pages to be ingested into knowledge base")
    read_limit: Optional[int] = Field(description="Maximum number of web pages from web search to be ingested")

class WebSearchTool(BaseTool):
    name = "Web Search"
    description = """Performs web search based on search query, and ingests the related web pages into knowledge base. Returns Markdown extracted from web pages."""
    args_schema: Type[BaseModel] = WebSearchInput

    graphlit: Graphlit = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, **kwargs):
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()

    async def _arun(self, search: str, read_limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    type=enums.FeedTypes.SEARCH,
                    search=input_types.SearchFeedPropertiesInput(
                        type=enums.SearchServiceTypes.TAVILY,
                        text=search,
                        readLimit=read_limit
                    )
                )
            )

            feed_id = response.create_feed.id if response.create_feed is not None else None

            if feed_id is not None:
                logger.debug(f'Created feed [{feed_id}].')

                # Wait for feed to complete, since ingestion happens asychronously
                done = False
                time.sleep(5)

                while not done:
                    done = await self.is_feed_done(feed_id)

                    if done is None:
                        break

                    if not done:
                        time.sleep(2)

                logger.debug(f'Completed feed [{feed_id}].')

                contents = await self.query_contents(feed_id)

                return '\n\n'.join(content.markdown for content in contents) if contents is not None else None
            else:
                return None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, search: str, read_limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(search, read_limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(search, read_limit))
        except RuntimeError:
            return asyncio.run(self._arun(search))

    async def is_feed_done(self, feed_id: str):
        if self.graphlit.client is None:
            return None

        response = await self.graphlit.client.is_feed_done(feed_id)

        return response.is_feed_done.result if response.is_feed_done is not None else None

    async def query_contents(self, feed_id: str):
        if self.graphlit.client is None:
            return None

        try:
            response = await self.graphlit.client.query_contents(
                filter=input_types.ContentFilter(
                    feeds=[
                        input_types.EntityReferenceFilter(
                            id=feed_id
                        )
                    ]
                )
            )

            return response.contents.results if response.contents is not None else None
        except exceptions.GraphQLClientError as e:
            print(str(e))
            return None
