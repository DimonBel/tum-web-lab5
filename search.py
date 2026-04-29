import re
import sys
from urllib.parse import quote_plus, unquote

from cache import cache_get, cache_set
from http_client import http_request
from renderer import strip_tags

DDG_URL = "https://html.duckduckgo.com/html/"


def _is_bot_challenge(html: str) -> bool:
    return "anomaly-modal" in html or "bots use DuckDuckGo" in html


def cmd_search(term: str):
    query = quote_plus(term)
    url = f"{DDG_URL}?q={query}"

    cached = cache_get(url)
    if cached:
        if _is_bot_challenge(cached):
            from cache import cache_delete
            cache_delete(url)
        else:
            print("[cache hit]\n")
            _print_search_results(cached, term)
            return

    try:
        _, _, body = http_request(url, accept="text/html")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    html = body.decode("utf-8", errors="replace")
    if _is_bot_challenge(html):
        print("Error: DuckDuckGo returned a bot-challenge page. Try again in a moment.", file=sys.stderr)
        sys.exit(1)
    cache_set(url, html)
    _print_search_results(html, term)


def _print_search_results(html: str, term: str):
    pattern = re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    results = pattern.findall(html)
    snippets = [strip_tags(s) for s in snippet_pattern.findall(html)]

    if not results:
        results = re.findall(r'href="(/l/\?[^"]+)"[^>]*class="[^"]*result__url[^"]*"', html)
        if not results:
            print("No results found. Try a different search term.")
            return

    print(f'Top results for: "{term}"\n{"-"*50}')
    shown = 0
    for i, (href, title) in enumerate(results):
        if shown >= 10:
            break
        real_url = _extract_ddg_url(href)
        clean_title = strip_tags(title).strip()
        snippet = snippets[i] if i < len(snippets) else ""
        print(f"\n{shown+1}. {clean_title}")
        print(f"   {real_url}")
        if snippet:
            print(f"   {snippet[:160]}{'...' if len(snippet) > 160 else ''}")
        shown += 1

    if shown == 0:
        print("No results parsed. Try a different search term.")
        return

    print(f'\n{"-"*50}')
    print("Enter a result number to open it, or press Enter to quit: ", end="", flush=True)
    try:
        choice = input().strip()
        if choice.isdigit():
            idx = int(choice) - 1
            valid_results = [_extract_ddg_url(href) for href, _ in results[:10]]
            if 0 <= idx < len(valid_results):
                print(f"\nFetching {valid_results[idx]} ...\n")
                from go2web import cmd_url
                cmd_url(valid_results[idx])
    except (EOFError, KeyboardInterrupt):
        pass


def _extract_ddg_url(href: str) -> str:
    m = re.search(r"[?&]uddg=([^&]+)", href)
    if m:
        return unquote(m.group(1))
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return "https://duckduckgo.com" + href
    return href
