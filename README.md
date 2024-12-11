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

## Support

Please refer to the [Graphlit API Documentation](https://docs.graphlit.dev/).

For support with the Graphlit Agent Tools, please submit a [GitHub Issue](https://github.com/graphlit/graphlit-tools-python/issues).  

For further support with the Graphlit Platform, please join our [Discord](https://discord.gg/ygFmfjy3Qx) community.

