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

class JiraIssueIngestInput(BaseModel):
    uri: str = Field(default=None, description="Atlassian Jira server URI")
    project: str = Field(default=None, description="Atlassian Jira project name")
    read_limit: Optional[int] = Field(default=None, description="Maximum number of issues from Jira to be read")

class JiraIssueIngestTool(BaseTool):
    name: str = "Graphlit Jira ingest tool"
    description: str = """Ingests issues from Atlassian Jira into knowledge base.
    Accepts Atlassian Jira server URI and project name.
    Returns extracted Markdown text and metadata from issues."""
    args_schema: Type[BaseModel] = JiraIssueIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the JiraIssueIngestTool.

        Args:
            graphlit (Optional[Graphlit]): An optional Graphlit instance to interact with the Graphlit API.
                If not provided, a new Graphlit instance will be created.
            workflow_id (Optional[str]): ID for the workflow to use when ingesting issues. Defaults to None.
            correlation_id (Optional[str]): Correlation ID for tracking requests. Defaults to None.
            **kwargs: Additional keyword arguments for the BaseTool superclass.
        """
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, uri: str, project: str, read_limit: Optional[int] = None) -> Optional[str]:
        feed_id = None

        email = os.environ['JIRA_EMAIL']

        if email is None:
            raise ToolException('Invalid Atlassian Jira email address. Need to assign JIRA_EMAIL environment variable.')

        token = os.environ['JIRA_TOKEN']

        if token is None:
            raise ToolException('Invalid Atlassian Jira token. Need to assign JIRA_TOKEN environment variable.')

        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name='Jira',
                    type=enums.FeedTypes.ISSUE,
                    issue=input_types.IssueFeedPropertiesInput(
                        type=enums.FeedServiceTypes.ATLASSIAN_JIRA,
                        jira=input_types.AtlassianJiraFeedPropertiesInput(
                            uri=uri,
                            project=project,
                            email=email,
                            token=token,
                        ),
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
                    time.sleep(5)

            logger.debug(f'Completed feed [{feed_id}].')
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

        try:
            contents = await self.query_contents(feed_id)

            results = []

            for content in contents:
                results.extend(helpers.format_content(content))

            text = "\n".join(results)

            return text
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, uri: str, project: str, read_limit: Optional[int] = None) -> Optional[str]:
        return helpers.run_async(self._arun, uri, project, read_limit)

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
            logger.error(str(e))
            return None
