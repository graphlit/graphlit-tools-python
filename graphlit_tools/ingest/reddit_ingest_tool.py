import logging
import time
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class RedditIngestInput(BaseModel):
    subreddit_name: str = Field(description="Reddit subreddit name to be read and ingested into knowledge base")
    read_limit: Optional[int] = Field(default=None, description="Maximum number of posts from Reddit subreddit to be read")

class RedditIngestTool(BaseTool):
    name: str = "Graphlit Reddit ingest tool"
    description: str = """Ingests posts from Reddit subreddit into knowledge base.
    Returns extracted Markdown text and metadata from Reddit posts."""
    args_schema: Type[BaseModel] = RedditIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the RedditIngestTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting posts. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, subreddit_name: str, read_limit: Optional[int] = None) -> Optional[str]:
        feed_id = None

        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name=f'Reddit Feed [{subreddit_name}]',
                    type=enums.FeedTypes.REDDIT,
                    reddit=input_types.RedditFeedPropertiesInput(
                        subredditName=subreddit_name,
                        readLimit=read_limit if read_limit is not None else 10
                    ),
                    workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                ),
                correlation_id=self.correlation_id
            )

            feed_id = response.create_feed.id if response.create_feed is not None else None

            if feed_id is None:
                return None

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
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        try:
            contents = await self.query_contents(feed_id)

            results = []

            for content in contents:
                results.append(helpers.format_content(content))

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, subreddit_name: str, read_limit: Optional[int] = None) -> Optional[str]:
        return helpers.run_async(self._arun, subreddit_name, read_limit)

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
