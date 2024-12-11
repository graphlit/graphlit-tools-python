# Python Agent Tools for Graphlit Platform

## Overview

The Graphlit Agent Tools for Python enables easy interaction with agent frameworks such as [CrewAI](https://crewai.com), allowing developers to easily integrate the Graphlit service with agentic workflows. This document outlines the setup process and provides a basic example of using the tools.

## Prerequisites

Before you begin, ensure you have the following:

- Python 3.x installed on your system.
- An active account on the [Graphlit Platform](https://portal.graphlit.dev) with access to the API settings dashboard.

## Installation

To install the Graphlit Agent Tools with CrewAI, use pip:

```bash
pip install graphlit-tools[crewai]
```

### Using the Graphlit agent tools

We have example Google Colab notebooks using CrewAI, which provide an example for [analyzing the web marketing strategy of a company](https://colab.research.google.com/github/graphlit/graphlit-samples/blob/main/python/Notebook%20Examples/Graphlit_2024_12_07_CrewAI_Web_Marketing_Analyzer.ipynb), and for [structured data extraction of products from scraped web pages](https://colab.research.google.com/github/graphlit/graphlit-samples/blob/main/python/Notebook%20Examples/Graphlit_2024_12_08_CrewAI_Product_Data_Extraction.ipynb).

Once you have configured the Graphlit client, as shown below, you will pass the client to the tool constructor.

For use in CrewAI, you will need to convert the tool to the CrewAI tool schema with the `CrewAIConverter.from_tool()` function.  We will provide support for additional agent frameworks, such as LangGraph and AutoGen in future.

```python
from graphlit_tools import WebSearchTool, CrewAIConverter

web_search_tool = CrewAIConverter.from_tool(WebSearchTool(graphlit))
```

## Configuration

The Graphlit Client supports environment variables to be set for authentication and configuration:

- `GRAPHLIT_ENVIRONMENT_ID`: Your environment ID.
- `GRAPHLIT_ORGANIZATION_ID`: Your organization ID.
- `GRAPHLIT_JWT_SECRET`: Your JWT secret for signing the JWT token.

Alternately, you can pass these values with the constructor of the Graphlit client.

You can find these values in the API settings dashboard on the [Graphlit Platform](https://portal.graphlit.dev).

For example, to use Graphlit in a Google Colab notebook, you need to assign these properties as Colab secrets: GRAPHLIT_ORGANIZATION_ID, GRAPHLIT_ENVIRONMENT_ID and GRAPHLIT_JWT_SECRET.

```python
import os
from google.colab import userdata
from graphlit import Graphlit

os.environ['GRAPHLIT_ORGANIZATION_ID'] = userdata.get('GRAPHLIT_ORGANIZATION_ID')
os.environ['GRAPHLIT_ENVIRONMENT_ID'] = userdata.get('GRAPHLIT_ENVIRONMENT_ID')
os.environ['GRAPHLIT_JWT_SECRET'] = userdata.get('GRAPHLIT_JWT_SECRET')

graphlit = Graphlit()
```

### Setting Environment Variables

To set these environment variables on your system, use the following commands, replacing `your_value` with the actual values from your account.

For Unix/Linux/macOS:

```bash
export GRAPHLIT_ENVIRONMENT_ID=your_environment_id_value
export GRAPHLIT_ORGANIZATION_ID=your_organization_id_value
export GRAPHLIT_JWT_SECRET=your_secret_key_value
```

For Windows Command Prompt (CMD):

```cmd
set GRAPHLIT_ENVIRONMENT_ID=your_environment_id_value
set GRAPHLIT_ORGANIZATION_ID=your_organization_id_value
set GRAPHLIT_JWT_SECRET=your_secret_key_value
```

For Windows PowerShell:

```powershell
$env:GRAPHLIT_ENVIRONMENT_ID="your_environment_id_value"
$env:GRAPHLIT_ORGANIZATION_ID="your_organization_id_value"
$env:GRAPHLIT_JWT_SECRET="your_secret_key_value"
```

## Tools

### Content Ingestion

#### URLIngestTool: Graphlit URL ingest tool
##### Description
Ingests content from URL.
Returns extracted Markdown text and metadata from content.
Can ingest individual Word documents, PDFs, audio recordings, videos, images, or any other unstructured data.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| url | str | URL of cloud-hosted file to be ingested into knowledge base |

#### LocalIngestTool: Graphlit local file ingest tool
##### Description
Ingests content from local file.
Returns extracted Markdown text and metadata from content.
Can ingest individual Word documents, PDFs, audio recordings, videos, images, or any other unstructured data.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| file_path | str | Path of local file to be ingested into knowledge base |

#### WebScrapeTool: Graphlit web scrape tool
##### Description
Scrapes web page into knowledge base.
Returns Markdown text and metadata extracted from web page.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| url | str | URL of web page to be scraped and ingested into knowledge base |

#### WebCrawlTool: Graphlit web crawl tool
##### Description
Crawls web pages from web site into knowledge base.
Returns Markdown text and metadata extracted from web pages.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| url | str | URL of web site to be crawled and ingested into knowledge base |
| search | Optional[str] | Text to search for within ingested web pages |
| read_limit | Optional[int] | Maximum number of web pages from web site to be crawled |

#### WebSearchTool: Graphlit web search tool
##### Description
Accepts search query text as string.
Performs web search based on search query.
Returns Markdown text and metadata extracted from web pages.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| search | str | Text to search for within web pages across the Internet |
| search_limit | Optional[int] | Maximum number of web pages to be returned from web search |

#### WebMapTool: Graphlit web map tool
##### Description
Accepts web page URL as string.
Enumerates the web pages at or beneath the provided URL using web sitemap.
Returns list of mapped URIs from web site.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| url | str | URL of the web page to be mapped |

#### RedditIngestTool: Graphlit Reddit ingest tool
##### Description
Ingests posts from Reddit subreddit into knowledge base.
Returns extracted Markdown text and metadata from Reddit posts.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| subreddit_name | str | Reddit subreddit name to be read and ingested into knowledge base |
| search | Optional[str] | Text to search for within ingested posts |
| read_limit | Optional[int] | Maximum number of posts from Reddit subreddit to be read, defaults to 10 |

#### NotionIngestTool: Graphlit Notion ingest tool
##### Description
Ingests pages from Notion database into knowledge base.
Returns extracted Markdown text and metadata from Notion pages.

Requires NOTION_API_KEY to be assigned as environment variable.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| search | Optional[str] | Text to search for within ingested pages |
| read_limit | Optional[int] | Maximum number of pages from Notion database to be read, defaults to 10 |

#### RSSIngestTool: Graphlit RSS ingest tool
##### Description
Ingests posts from RSS feed into knowledge base.
For podcast RSS feeds, audio will be transcribed and ingested into knowledge base.
Returns extracted or transcribed Markdown text and metadata from RSS posts.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| url | str | RSS URL to be read and ingested into knowledge base |
| search | Optional[str] | Text to search for within ingested posts and/or transcripts |
| read_limit | Optional[int] | Maximum number of posts from RSS feed to be read, defaults to 10 |

#### MicrosoftEmailIngestTool: Graphlit Microsoft Email ingest tool
##### Description
Ingests emails from Microsoft Email account into knowledge base.
Returns extracted Markdown text and metadata from emails.

Requires MICROSOFT_EMAIL_CLIENT_ID, MICROSOFT_EMAIL_CLIENT_SECRET and MICROSOFT_EMAIL_REFRESH_TOKEN to be assigned as environment variables.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| search | Optional[str] | Text to search for within ingested email |
| read_limit | Optional[int] | Maximum number of emails from Microsoft Email account to be read, defaults to 10 |

#### GoogleEmailIngestTool: Graphlit Google Email ingest tool
##### Description
Ingests emails from Google Email account into knowledge base.
Returns extracted Markdown text and metadata from emails.

Requires GOOGLE_EMAIL_CLIENT_ID, GOOGLE_EMAIL_CLIENT_SECRET and GOOGLE_EMAIL_REFRESH_TOKEN to be assigned as environment variables.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| search | Optional[str] | Text to search for within ingested email |
| read_limit | Optional[int] | Maximum number of emails from Google Email account to be read, defaults to 10 |

#### GitHubIssueIngestTool: Graphlit GitHub Issue ingest tool
##### Description
Ingests issues from GitHub repository into knowledge base.
Accepts GitHub repository owner and repository name.
For example, for GitHub repository (https://github.com/openai/tiktoken), 'openai' is the repository owner, and 'tiktoken' is the repository name.
Returns extracted Markdown text and metadata from issues.

Requires GITHUB_PERSONAL_ACCESS_TOKEN to be assigned as environment variable.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| repository_name | str | GitHub repository name |
| repository_owner | str | GitHub repository owner |
| search | Optional[str] | Text to search for within ingested issues |
| read_limit | Optional[int] | Maximum number of issues from GitHub repository to be read, defaults to 10 |

#### JiraIssueIngestTool: Graphlit Jira ingest tool
##### Description
Ingests issues from Atlassian Jira into knowledge base.
Accepts Atlassian Jira server URL and project name.
Returns extracted Markdown text and metadata from issues.

Requires JIRA_TOKEN and JIRA_EMAIL to be assigned as environment variables.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| url | str | Atlassian Jira server URL |
| project | str | Atlassian Jira project name |
| search | Optional[str] | Text to search for within ingested issues |
| read_limit | Optional[int] | Maximum number of issues from Jira project to be read, defaults to 10 |

#### LinearIssueIngestTool: Graphlit Linear ingest tool
##### Description
Ingests issues from Linear project into knowledge base.
Accepts Linear project name.
Returns extracted Markdown text and metadata from issues.

Requires LINEAR_API_KEY to be assigned as environment variable.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| project | str | Linear project name |
| search | Optional[str] | Text to search for within ingested issues |
| read_limit | Optional[int] | Maximum number of issues from Linear project to be read, defaults to 10 |

#### MicrosoftTeamsIngestTool: Graphlit Microsoft Teams ingest tool
##### Description
Ingests messages from Microsoft Teams channel into knowledge base.
Returns extracted Markdown text and metadata from messages.

Requires MICROSOFT_TEAMS_CLIENT_ID, MICROSOFT_TEAMS_CLIENT_SECRET and MICROSOFT_TEAMS_REFRESH_TOKEN to be assigned as environment variables.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| team_name | str | Microsoft Teams team name |
| channel_name | str | Microsoft Teams channel name |
| search | Optional[str] | Text to search for within ingested messages |
| read_limit | Optional[int] | Maximum number of messages from Microsoft Teams channel to be read, defaults to 10 |

#### DiscordIngestTool: Graphlit Discord ingest tool
##### Description
Ingests messages from Discord channel into knowledge base.
Accepts Discord channel name.
Returns extracted Markdown text and metadata from messages.

Requires DISCORD_BOT_TOKEN to be assigned as environment variable.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| channel_name | str | Discord channel name |
| search | Optional[str] | Text to search for within ingested messages |
| read_limit | Optional[int] | Maximum number of messages from Discord channel to be read, defaults to 10 |

#### SlackIngestTool: Graphlit Slack ingest tool
##### Description
Ingests messages from Slack channel into knowledge base.
Accepts Slack channel name.
Returns extracted Markdown text and metadata from messages.

Requires SLACK_BOT_TOKEN to be assigned as environment variable.

##### Parameters
| Name | Type | Description |
| ---- | ---- | ---- |
| channel_name | str | Slack channel name |
| search | Optional[str] | Text to search for within ingested messages |
| read_limit | Optional[int] | Maximum number of messages from Slack channel to be read, defaults to 10 |

### Content Generation

PromptTool
DescribeImageTool
DescribeWebPageTool
GenerateSummaryTool
GenerateBulletsTool
GenerateHeadlinesTool
GenerateSocialMediaPostsTool
GenerateQuestionsTool
GenerateKeywordsTool
GenerateChaptersTool

### Data Retrieval

PersonRetrievalTool
OrganizationRetrievalTool
ContentRetrievalTool

### Data Extraction

ExtractURLTool
ExtractWebPageTool
ExtractTextTool

## Support

Please refer to the [Graphlit API Documentation](https://docs.graphlit.dev/).

For support with the Graphlit Agent Tools, please submit a [GitHub Issue](https://github.com/graphlit/graphlit-tools-python/issues).  

For further support with the Graphlit Platform, please join our [Discord](https://discord.gg/ygFmfjy3Qx) community.

