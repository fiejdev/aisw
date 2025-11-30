# DT - Autonomous AI Software Engineer for a Specific Use-Case: Advanced Web Scraping Based on Natural Language Input

LangGraph-based system

## Overview

- **Programmer node**: Uses Azure OpenAI to generate/fix Python code based on user queries.
- **Runner node**: Executes code in an isolated Docker container with execution tracing.
- **Auto-retry loop**: Control-flow in `graph.py` that calls the nodes repeatedly until success or `max_iters` is reached.

## Technology Details

- **LangGraph orchestration**: `graph.py` wires the `programmer` and `runner` nodes together, persists state via a `MemorySaver`, and keeps retrying failed runs until the configured `max_iters`.
- **Coding agent**: `programmer.py` builds JSON-constrained prompts for an Azure OpenAI deployment, ensuring each response includes structured diagnostics plus a complete Python program that only depends on the stdlib, `numpy`, `pandas`, `requests`, and `bs4`.
- **Sandboxed container**: `runner.py` feeds the model-produced code into the `dt-sandbox:py313` image built from the provided `Dockerfile` (Python 3.13 slim, preloaded with the allowed libraries, non-root user).
- **Execution harness**: Inside the container, `harness.py` runs the code, records stdout/stderr, traces up to 200 line events with compact locals, and emits a JSON payload describing success or the captured exception plus instrumented frames.
- **Self-healing loop**: The JSON payload is passed back to the programmer node so the model can reason about the failing stack trace and produce a revised patch on the next iteration.

## Codebase Structure

- **`graph.py`**: Defines the LangGraph with two nodes: `programmer` and `runner`, and runs the loop.
- **`programmer.py`**: Logic behind the `programmer` node (prompt building + Azure OpenAI call).
- **`runner.py`**: Logic behind the `runner` node (executes code in the Docker sandbox).
- **`harness.py`**: Script that runs inside the container to execute and trace the code.
- **`config.py`**: Minimal helpers for loading Azure OpenAI configuration.


## Setup

Prerequisite: Python 3.13 on the host (matches the `python:3.13-slim` runtime baked into `dt-sandbox:py313`).

1. **Build Docker image:**
   ```bash
   docker build -t dt-sandbox:py313 .
   ```

2. **Create `.env` file:**
   ```
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_API_VERSION=2025-04-01-preview
   AZURE_OPENAI_DEPLOYMENT=your_deployment_name
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python graph.py "your query here" [max_iters]
```

**Example:**
```bash
python graph.py "Fetch https://example.com, extract all anchor texts" 4
```

The system will generate code, execute it, and automatically fix errors up to `max_iters` times (default: 3).

## Real Example

```
> python graph.py "Scrape https://books.toscrape.com/catalogue/category/books/travel_2/index.html; follow every pagination link; emit CSV with title, star_rating, price as float, availability text sorted by price" 5
INFO: thread_id=dbba0ef251e8
INFO: [programmer] generating code…
INFO: HTTP Request: POST https://aisw-fr.cognitiveservices.azure.com/openai/deployments/gpt-5-mini/chat/completions?api-version=2025-04-01-preview "HTTP/1.1 200 OK"
INFO: [programmer] produced code (preview):
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"  
url = start_url
books = []

while url:
    resp …
INFO: [runner] executing code in container…
INFO: [runner] failure
INFO: [runner] stderr (preview):

INFO: [runner] exception (preview):
{'type': 'ValueError', 'message': "could not convert string to float: 'Â45.17'", 'frames': [{'file': '/opt/harness.py', 'line': 77, 'func': 'main', 'locals': {'code': 'import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"  
url = start_url
books = []

while url:
    resp …
INFO: [programmer] repairing code…
INFO: HTTP Request: POST https://aisw-fr.cognitiveservices.azure.com/openai/deployments/gpt-5-mini/chat/completions?api-version=2025-04-01-preview "HTTP/1.1 200 OK"
INFO: [programmer] produced code (preview):
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"  
url = start_url
books = []

while url:…
INFO: [runner] executing code in container…
INFO: [runner] failure
INFO: [runner] stderr (preview):
Traceback (most recent call last):
  File "/opt/harness.py", line 16, in to_jsonable
    json.dumps(value)
    ~~~~~~~~~~^^^^^^^
  File "/usr/local/lib/python3.13/json/__init__.py", line 231, in dumps
    return _default_encoder.encode(obj)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/usr/local/…
INFO: [runner] exception (preview):
{'type': 'ContainerExecutionError', 'message': 'invalid harness output (exit 1)', 'frames': []}
INFO: [programmer] repairing code…
INFO: HTTP Request: POST https://aisw-fr.cognitiveservices.azure.com/openai/deployments/gpt-5-mini/chat/completions?api-version=2025-04-01-preview "HTTP/1.1 200 OK"
INFO: [programmer] produced code (preview):
import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"  
url = start_url
books = []

while url:
    resp…
INFO: [runner] executing code in container…
INFO: [runner] failure
INFO: [runner] stderr (preview):

INFO: [runner] exception (preview):
{'type': 'PermissionError', 'message': "[Errno 13] Permission denied: 'books.csv'", 'frames': [{'file': '/opt/harness.py', 'line': 77, 'func': 'main', 'locals': {'code': 'import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"  
url = start_url
books = []

while url:
    resp…
INFO: [programmer] repairing code…
INFO: HTTP Request: POST https://aisw-fr.cognitiveservices.azure.com/openai/deployments/gpt-5-mini/chat/completions?api-version=2025-04-01-preview "HTTP/1.1 200 OK"
INFO: [programmer] produced code (preview):
import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import tempfile
import os
import sys

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"  
url = start…
INFO: [runner] executing code in container…
INFO: [runner] success
INFO: [runner] stdout (preview):
Wrote 11 rows to /tmp/books.csv

INFO: [runner] code (preview):
import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import tempfile
import os
import sys

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}       
start_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"
url = start…
```
