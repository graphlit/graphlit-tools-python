import asyncio
import logging
import time
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class WebCrawlInput(BaseModel):
    url: str = Field(description="URL of web site to be crawled and ingested into knowledge base")
    read_limit: Optional[int] = Field(default=None, description="Maximum number of web pages from web site to be crawled")

class WebCrawlTool(BaseTool):
    name: str = "Graphlit web crawl tool"
    description: str = """Crawls web pages from web site. Returns Markdown extracted from web pages."""
    args_schema: Type[BaseModel] = WebCrawlInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the WebCrawlTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting web pages. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, url: str, read_limit: Optional[int] = None) -> Optional[str]:
        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name=f'Web Feed [{url}]',
                    type=enums.FeedTypes.WEB,
                    web=input_types.WebFeedPropertiesInput(
                        uri=url,
                        readLimit=read_limit
                    ),
                    workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                ),
                correlation_id=self.correlation_id
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

                results = []

                for content in contents:
                    if content.type == enums.ContentTypes.FILE:
                        results.append(f'## {content.file_type}: {content.file_name}')
                    elif content.type == enums.ContentTypes.PAGE:
                        results.append(f'## {content.type}:')
                    else:
                        results.append(f'## {content.type}: {content.name}')

                    if content.original_date is not None:
                        results.append(f'### Date: {content.original_date}')

                    if content.uri is not None:
                        results.append(f'### URI: {content.uri}')

                    if content.document is not None:
                        if content.document.title is not None:
                            results.append(f'### Title: {content.document.title}')

                        if content.document.author is not None:
                            results.append(f'### Author: {content.document.author}')

                    if content.links is not None:
                        for link in content.links[:10]: # NOTE: just return top 10 links
                            results.append(f'### {link.link_type} Link: {link.uri}')

                    results.append('\n')
                    results.append(content.markdown)
                    results.append('\n')

                text = "\n".join(results)

                return text
            else:
                return None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str, read_limit: Optional[int] = None) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(url, read_limit))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(url, read_limit))
        except RuntimeError:
            return asyncio.run(self._arun(url))

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
