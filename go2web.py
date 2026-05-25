import re
import sys
import json
import socket
from urllib.parse import urlparse

from cache import cache_get, cache_set
from http_client import http_request
from renderer import html_to_text
from search import cmd_search


def cmd_url(url: str):
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host or ("." not in host and host != "localhost"):
        print(f"Error: '{url}' does not look like a valid URL.", file=sys.stderr)
        print("  Example usage:  go2web -u https://example.com", file=sys.stderr)
        sys.exit(1)

    cached = cache_get(url)
    if cached:
        print("[cache hit]\n")
        print(cached)
        return

    try:
        status, headers, body = http_request(
            url, accept="text/html,application/json;q=0.9"
        )
    except socket.gaierror:
        print(f"Error: Could not resolve host '{host}'.", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print(f"Error: Connection to '{host}' timed out.", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"Error: Connection refused by '{host}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    content_type = headers.get("content-type", "")
    encoding = "utf-8"
    enc_match = re.search(r"charset=([^\s;]+)", content_type)
    if enc_match:
        encoding = enc_match.group(1).strip().strip('"')
    text_body = body.decode(encoding, errors="replace")

    if "application/json" in content_type or "json" in content_type:
        try:
            output = json.dumps(json.loads(text_body), indent=2, ensure_ascii=False)
        except Exception:
            output = text_body
    else:
        output = html_to_text(text_body)

    cache_set(url, output)
    print(f"HTTP {status}\n")
    print(output)


HELP_TEXT = """
go2web — HTTP client over raw TCP sockets

Usage:
  go2web -u <URL>           Make an HTTP request to the URL and print the response
  go2web -s <search-term>   Search DuckDuckGo and print the top 10 results
  go2web -h                 Show this help message

Features
  * HTTP redirects (up to 10 hops) - specialI stup it.
  * File-based HTTP cache (TTL 5 min, stored in ./cache/ as JSON files)
  * Content negotiation (HTML rendered as plain text, JSON pretty-printed)
  * Interactive: open search results by number

Examples:
  go2web -u https://example.com
  go2web -u http://info.cern.ch
  go2web -s "Python TCP sockets"
  go2web -s open source networking
"""


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(HELP_TEXT)
        sys.exit(0)

    flag = sys.argv[1]

    if flag == "-u":
        if len(sys.argv) < 3:
            print("Error: -u requires a URL argument", file=sys.stderr)
            sys.exit(1)
        cmd_url(sys.argv[2])

    elif flag == "-s":
        if len(sys.argv) < 3:
            print("Error: -s requires a search term", file=sys.stderr)
            sys.exit(1)
        cmd_search(" ".join(sys.argv[2:]))

    else:
        print(f"Unknown option: {flag}\nRun 'go2web -h' for help.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
