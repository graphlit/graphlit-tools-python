import logging
import time
import os
from typing import Optional, Type

from graphlit import Graphlit
from graphlit_api import exceptions, input_types, enums
from pydantic import BaseModel, Field

from ..base_tool import BaseTool
from ..exceptions import ToolException
from .. import helpers

logger = logging.getLogger(__name__)

class NotionIngestInput(BaseModel):
    search: Optional[str] = Field(description="Text to search for within ingested pages", default=None)
    read_limit: Optional[int] = Field(description="Maximum number of pages from Notion database to be read", default=10)

class NotionIngestTool(BaseTool):
    name: str = "Graphlit Notion ingest tool"
    description: str = """Ingests pages from Notion database into knowledge base.
    Optionally accepts search text for searching within the ingested pages. If search text was not provided, all ingested pages will be returned.
    Returns extracted Markdown text and metadata from Notion pages."""
    args_schema: Type[BaseModel] = NotionIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the NotionIngestTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting pages. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, search: Optional[str] = None, read_limit: Optional[int] = None) -> Optional[str]:
        feed_id = None

        token = os.environ['NOTION_API_KEY']

        if token is None:
            raise ToolException('Invalid Notion API key. Need to assign NOTION_API_KEY environment variable.')

        database_id = os.environ['NOTION_DATABASE_ID']

        if database_id is None:
            raise ToolException('Invalid Notion database identifier. Need to assign NOTION_DATABASE_ID environment variable.')

        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name='Notion Feed',
                    type=enums.FeedTypes.NOTION,
                    notion=input_types.NotionFeedPropertiesInput(
                        type=enums.NotionTypes.DATABASE,
                        identifiers=[database_id],
                        token=token,
                        readLimit=read_limit if read_limit is not None else 10
                    ),
                    workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                ),
                correlation_id=self.correlation_id
            )

            feed_id = response.create_feed.id if response.create_feed is not None else None

            if feed_id is None:
                raise ToolException('Invalid feed identifier.')

            logger.debug(f'Created feed [{feed_id}].')

            # Wait for feed to complete, since ingestion happens asychronously
            done = False
            time.sleep(5)

            while not done:
                done = await helpers.is_feed_done(self.graphlit.client, feed_id)

                if done is None:
                    break

                if not done:
                    time.sleep(5)

            logger.debug(f'Completed feed [{feed_id}].')
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        return await helpers.format_feed_contents(self.graphlit.client, feed_id, search)

    def _run(self, search: Optional[str] = None, read_limit: Optional[int] = None) -> Optional[str]:
        return helpers.run_async(self._arun, search, read_limit)
