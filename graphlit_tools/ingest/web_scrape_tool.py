import asyncio
import logging
from typing import Type, Optional
from graphlit import Graphlit
from graphlit_api import exceptions, enums, input_types
from langchain_core.tools import BaseTool, ToolException
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)

class WebScrapeInput(BaseModel):
    url: str = Field(description="URL of web page to be scraped and ingested into knowledge base")

class WebScrapeTool(BaseTool):
    name: str = "Graphlit web scrape tool"
    description: str = """Scrapes web page. Returns Markdown extracted from web page."""
    args_schema: Type[BaseModel] = WebScrapeInput

    graphlit: Graphlit = Field(None, exclude=True)

    workflow_id: Optional[str] = Field(None, exclude=True)
    correlation_id: Optional[str] = Field(None, exclude=True)

    def __init__(self, graphlit: Optional[Graphlit] = None, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None, **kwargs):
        """
        Initializes the WebScrapeTool.

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

                content = response.content

                results = []

                if content is not None:
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

                    if content.pages is not None:
                        for page in content.pages:
                            if page.chunks is not None and len(page.chunks) > 0:
                                results.append(f'### Page #{page.index + 1}')

                                for chunk in page.chunks:
                                    results.append(chunk.text)

                                results.append('\n')

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
