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

class GoogleEmailIngestInput(BaseModel):
    search: Optional[str] = Field(description="Text to search for within ingested emails.", default=None)
    read_limit: Optional[int] = Field(description="Maximum number of emails from Google Email account to be read.", default=10)

class GoogleEmailIngestTool(BaseTool):
    name: str = "Graphlit Google Email ingest tool"
    description: str = """Ingests emails from Google Email account into knowledge base.
    Optionally accepts search text for searching within the ingested emails. If search text was not provided, all ingested emails will be returned.
    Returns extracted Markdown text and metadata from emails."""
    args_schema: Type[BaseModel] = GoogleEmailIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the GmailIngestTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting emails. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, search: Optional[str] = None, read_limit: Optional[int] = None) -> Optional[str]:
        feed_id = None

        refresh_token = os.environ['GOOGLE_EMAIL_REFRESH_TOKEN']

        if refresh_token is None:
            raise ToolException('Invalid Google Email refresh token. Need to assign GOOGLE_EMAIL_REFRESH_TOKEN environment variable.')

        client_id = os.environ['GOOGLE_EMAIL_CLIENT_ID']

        if client_id is None:
            raise ToolException('Invalid Google Email client identifier. Need to assign GOOGLE_EMAIL_CLIENT_ID environment variable.')

        client_secret = os.environ['GOOGLE_EMAIL_CLIENT_SECRET']

        if client_secret is None:
            raise ToolException('Invalid Google Email client secret. Need to assign GOOGLE_EMAIL_CLIENT_SECRET environment variable.')

        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name='Google Email',
                    type=enums.FeedTypes.EMAIL,
                    email=input_types.EmailFeedPropertiesInput(
                        type=enums.FeedServiceTypes.GOOGLE_EMAIL,
                        google=input_types.GoogleEmailFeedPropertiesInput(
                            type=enums.EmailListingTypes.PAST,
                            refreshToken=refresh_token,
                            clientId=client_id,
                            clientSecret=client_secret,
                        ),
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

    def _run(self, search: Optional[str] = None, read_limit: Optional[int] = None) -> str:
        return helpers.run_async(self._arun, search, read_limit)
