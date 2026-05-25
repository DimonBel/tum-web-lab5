import re


def html_to_text(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<(br|p|div|li|tr|h[1-6])[^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</?(ul|ol|table|thead|tbody)[^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(
        r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        lambda m: f"{strip_tags(m.group(2))} [{m.group(1)}]",
        html, flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(r"<[^>]+>", "", html)
    entities = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
        "&#39;": "'", "&nbsp;": " ", "&mdash;": "—", "&ndash;": "–",
        "&hellip;": "…", "&laquo;": "«", "&raquo;": "»",
    }
    for ent, char in entities.items():
        html = html.replace(ent, char)
    html = re.sub(r"\n{3,}", "\n\n", html)
    html = re.sub(r"[ \t]+", " ", html)
    lines = [l.strip() for l in html.splitlines()]
    return "\n".join(l for l in lines if l)


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()
