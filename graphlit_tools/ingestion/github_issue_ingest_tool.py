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

class GitHubIssueIngestInput(BaseModel):
    repository_name: str = Field(description="GitHub repository name")
    repository_owner: str = Field(description="GitHub repository owner")
    search: Optional[str] = Field(description="Text to search for within ingested issues", default=None)
    read_limit: Optional[int] = Field(description="Maximum number of issues from GitHub repository to be read", default=10)

class GitHubIssueIngestTool(BaseTool):
    name: str = "Graphlit GitHub Issue ingest tool"
    description: str = """Ingests issues from GitHub repository into knowledge base.
    Accepts GitHub repository owner and repository name.
    For example, for GitHub repository (https://github.com/openai/tiktoken), 'openai' is the repository owner, and 'tiktoken' is the repository name.
    Optionally accepts search text for searching within the ingested issues. If search text was not provided, all ingested issues will be returned.
    Returns extracted Markdown text and metadata from issues."""
    args_schema: Type[BaseModel] = GitHubIssueIngestInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the GitHubIssueIngestTool.

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

    async def _arun(self, repository_name: str, repository_owner: str, search: Optional[str] = None, read_limit: Optional[int] = None) -> Optional[str]:
        feed_id = None

        personal_access_token = os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']

        if personal_access_token is None:
            raise ToolException('Invalid GitHub personal access token. Need to assign GITHUB_PERSONAL_ACCESS_TOKEN environment variable.')

        try:
            response = await self.graphlit.client.create_feed(
                feed=input_types.FeedInput(
                    name='GitHub Issue',
                    type=enums.FeedTypes.ISSUE,
                    issue=input_types.IssueFeedPropertiesInput(
                        type=enums.FeedServiceTypes.GIT_HUB_ISSUES,
                        github=input_types.GitHubIssuesFeedPropertiesInput(
                            repositoryName=repository_name,
                            repositoryOwner=repository_owner,
                            personalAccessToken=personal_access_token,
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

    def _run(self, repository_name: str, repository_owner: str, search: Optional[str] = None, read_limit: Optional[int] = None) -> Optional[str]:
        return helpers.run_async(self._arun, repository_name, repository_owner, search, read_limit)
