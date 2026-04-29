# go2web - HTTP Client over TCP Sockets

A command-line HTTP client built entirely on raw TCP sockets.
No third-party HTTP libraries (requests, urllib3, http.client) are used.

## Architecture

```
go2web/
├── go2web.py        # CLI entry point
├── http_client.py   # Core HTTP client (raw TCP sockets)
├── renderer.py      # Content rendering (HTML/JSON)
├── search.py        # Bing RSS search functionality
├── cache.py          # File-based HTTP cache
├── go2web.cmd       # Windows launcher
└── README.md
```

## Modules

### http_client.py
Core HTTP client using raw TCP sockets:
- `parse_url()` - Breaks URL into host, port, path, scheme
- `raw_request()` - Opens TCP socket, wraps in TLS if HTTPS, sends request, reads response
- `parse_response()` - Splits raw HTTP response into status, headers, body
- `decode_chunked()` - Handles Transfer-Encoding: chunked
- `fetch()` - Orchestrates with redirect following and cache integration

### renderer.py
Content rendering based on Content-Type:
- `render_json()` - Pretty prints JSON
- `render_html()` - Strips HTML tags, extracts plain text
- `render()` - Dispatches to appropriate renderer
- `is_html()` - Auto-detects HTML content

### cache.py
File-based JSON cache:
- 5-minute TTL per entry
- Respects Cache-Control: no-store / no-cache
- Max 50 entries with oldest-first eviction

### search.py
Web search using Bing RSS:
- `search()` - Returns formatted top 10 results
- `parse_rss()` - Extracts title/link from RSS items

### go2web.py
CLI entry point:
- Parses arguments with argparse
- Routes to `fetch()` for URLs or `search()` for search terms

## Features

| Feature | Description |
|---------|-------------|
| `-h` | Help flag displays usage |
| `-u <URL>` | Fetches HTTP/HTTPS URLs, prints human-readable content |
| `-s <term>` | Searches Bing RSS, displays top 10 results |
| HTTP redirects | Follows 301/302/303/307/308 (up to 5 hops) |
| Content negotiation | Accepts JSON and HTML, renders accordingly |
| Chunked transfer | Decodes chunked responses |
| HTTP cache | File-based cache with 5-min TTL |

## Setup

```bash
# No dependencies required - pure Python standard library
python go2web.py -h
```

## Usage

```bash
python go2web.py -u <URL>     # Fetch URL
python go2web.py -s <term>    # Search Bing
python go2web.py -h          # Show help
```

## Examples

```
$ python go2web.py -u http://example.com
Example Domain
=== Example Domain ===
This domain is for use in illustrative examples in documents.

$ python go2web.py -s python tutorial
Top 10 results for 'python tutorial':

1. Best online resource to learn Python? - Stack Overflow
   https://stackoverflow.com/questions/70577/best-online-resource-to-learn-python

2. Socket Programming in Python (Guide) - Real Python
   https://realpython.com/python-sockets/
...
```

## Extra Points Earned

- +1 Clickable search result links (via Bing)
- +1 HTTP redirect handling (301/302/303/307/308)
- +2 HTTP cache mechanism (file-based with TTL)
- +2 Content negotiation (JSON and HTML rendering)
