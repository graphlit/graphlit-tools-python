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

class MicrosoftTeamsIngestInput(BaseModel):
    team_name: str = Field(description="Microsoft Teams team name")
    channel_name: str = Field(description="Microsoft Teams channel name")
    search: Optional[str] = Field(description="Text to search for within ingested messages", default=None)
    read_limit: Optional[int] = Field(description="Maximum number of messages from Microsoft Teams channel to be read", default=10)

class MicrosoftTeamsIngestTool(BaseTool):
    name: str = "Graphlit Microsoft Teams ingest tool"
    description: str = """Ingests messages from Microsoft Teams channel into knowledge base.
    Optionally accepts search text for searching within the ingested messages. If search text was not provided, all ingested messages will be returned.
    Returns extracted Markdown text and metadata from messages."""
    args_schema: Type[BaseModel] = MicrosoftTeamsIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the MicrosoftTeamsIngestTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting messages. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, team_name: Optional[str] = None, channel_name: Optional[str] = None, search: Optional[str] = None, read_limit: Optional[int] = None) -> Optional[str]:
        feed_id = None

        team_id = os.environ['MICROSOFT_TEAMS_TEAM_ID']
        channel_id = os.environ['MICROSOFT_TEAMS_CHANNEL_ID']

        refresh_token = os.environ['MICROSOFT_TEAMS_REFRESH_TOKEN']

        if refresh_token is None:
            raise ToolException('Invalid Microsoft Teams refresh token. Need to assign MICROSOFT_TEAMS_REFRESH_TOKEN environment variable.')

        client_id = os.environ['MICROSOFT_TEAMS_CLIENT_ID']

        if client_id is None:
            raise ToolException('Invalid Microsoft Teams client identifier. Need to assign MICROSOFT_TEAMS_CLIENT_ID environment variable.')

        client_secret = os.environ['MICROSOFT_TEAMS_CLIENT_SECRET']

        if client_secret is None:
            raise ToolException('Invalid Microsoft Teams client secret. Need to assign MICROSOFT_TEAMS_CLIENT_SECRET environment variable.')

        teams = None

        try:
            response = await self.graphlit.client.query_microsoft_teams_teams(
                properties=input_types.MicrosoftTeamsTeamsInput(
                    refreshToken=refresh_token,
                )
            )

            teams = response.microsoft_teams_teams.results if response.microsoft_teams_teams is not None else None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        if len(teams) == 0:
            raise ToolException('No Microsoft Teams teams were found.')

        team = next(filter(lambda x: x['team_name'] == team_name, teams), None) if team_name is not None else teams[0]

        team_id = team.team_id if team is not None else team_id

        if team_id is None:
            raise ToolException('Invalid Microsoft Teams team identifier. Need to assign MICROSOFT_TEAMS_TEAM_ID environment variable.')

        channels = None

        try:
            response = await self.graphlit.client.query_microsoft_teams_channels(
                properties=input_types.MicrosoftTeamsChannelsInput(
                    refreshToken=refresh_token,
                ),
                team_id=team_id
            )

            channels = response.microsoft_teams_channels.results if response.microsoft_teams_channels is not None else None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        if len(channels) == 0:
            raise ToolException('No Microsoft Teams channels were found.')

        channel = next(filter(lambda x: x['channel_name'] == channel_name, channels), None) if channel_name is not None else channels[0]

        channel_id = channel.channel_id if channel is not None else channel_id

        if channel_id is None:
            raise ToolException('Invalid Microsoft Teams channel identifier. Need to assign MICROSOFT_TEAMS_CHANNEL_ID environment variable.')

        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name='Microsoft Teams',
                    type=enums.FeedTypes.MICROSOFT_TEAMS,
                    microsoftTeams=input_types.MicrosoftTeamsFeedPropertiesInput(
                        type=enums.FeedListingTypes.PAST,
                        teamId=team_id,
                        channelId=channel_id,
                        clientId=client_id,
                        clientSecret=client_secret,
                        refreshToken=refresh_token,
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

    def _run(self, team_name: Optional[str] = None, channel_name: Optional[str] = None, search: Optional[str] = None, read_limit: Optional[int] = None) -> str:
        return helpers.run_async(self._arun, team_name, channel_name, search, read_limit)
