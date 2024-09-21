import asyncio
import logging
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class WebScrapeInput(BaseModel):
    url: str = Field(description="URL of web page to be scraped and ingested into knowledge base")

class WebScrapeTool(BaseTool):
    name = "Web Scrape"
    description = """Scrapes web page. Returns Markdown extracted from web page."""
    args_schema: Type[BaseModel] = WebScrapeInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.graphlit = graphlit or Graphlit()
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id

    async def _arun(self, url: str) -> Optional[str]:
        try:
            response = await self.graphlit.client.ingest_uri(
                uri=url,
                workflow=input_types.EntityReferenceInput(id=self.workflow_id) if self.workflow_id is not None else None,
                is_synchronous=True,
                correlation_id=self.correlation_id
            )

            content_id = response.ingest_uri.id if response.ingest_uri is not None else None

            if content_id is not None:
                response = await self.graphlit.client.get_content(content_id)

                return response.content.markdown if response.content is not None else None
            else:
                return None
        except exceptions.GraphQLClientError as e:
            logger.error(str(e))
            raise ToolException(str(e)) from e

    def _run(self, url: str) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self._arun(url))
                return loop.run_until_complete(future)
            else:
                return loop.run_until_complete(self._arun(url))
        except RuntimeError:
            return asyncio.run(self._arun(url))
