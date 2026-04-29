import socket
import ssl
import sys
import gzip
import zlib
from urllib.parse import urlparse, urljoin

MAX_REDIRECTS = 10


def http_request(url: str, accept: str = "text/html,application/json", redirects: int = 0):
    if redirects > MAX_REDIRECTS:
        raise RuntimeError("Too many redirects")

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Accept: {accept}\r\n"
        f"Accept-Language: en-US,en;q=0.9\r\n"
        f"Accept-Encoding: gzip, deflate\r\n"
        f"Connection: close\r\n"
        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
        f"\r\n"
    )

    def _make_raw():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        return s

    def _connect_https(verify=True):
        s = _make_raw()
        ctx = ssl.create_default_context()
        if not verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        wrapped = ctx.wrap_socket(s, server_hostname=host)
        wrapped.connect((host, port))
        return wrapped

    if scheme == "https":
        try:
            sock = _connect_https(verify=True)
        except ssl.SSLCertVerificationError:
            print("  SSL cert verification failed, retrying without verification...", file=sys.stderr)
            sock = _connect_https(verify=False)
    else:
        sock = _make_raw()
        sock.connect((host, port))

    try:
        sock.sendall(request.encode("utf-8"))
        chunks = []
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            except socket.timeout:
                break
    finally:
        sock.close()

    raw = b"".join(chunks)

    if not raw:
        raise RuntimeError(
            f"Server at '{host}' closed the connection without sending any data.\n"
            "  The site is likely protected by bot-detection (e.g. Cloudflare) that\n"
            "  blocks raw TCP clients based on their TLS fingerprint."
        )

    header_end = raw.find(b"\r\n\r\n")
    if header_end == -1:
        header_end = raw.find(b"\n\n")
        sep_len = 2
    else:
        sep_len = 4

    header_bytes = raw[:header_end]
    body_bytes = raw[header_end + sep_len:]

    header_text = header_bytes.decode("utf-8", errors="replace")
    lines = header_text.split("\r\n") if "\r\n" in header_text else header_text.split("\n")
    status_line = lines[0]
    status_code = int(status_line.split()[1]) if len(status_line.split()) >= 2 else 0

    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()

    if headers.get("transfer-encoding", "").lower() == "chunked":
        body_bytes = _decode_chunked(body_bytes)

    content_encoding = headers.get("content-encoding", "").lower()
    if content_encoding == "gzip":
        body_bytes = gzip.decompress(body_bytes)
    elif content_encoding == "deflate":
        try:
            body_bytes = zlib.decompress(body_bytes)
        except zlib.error:
            body_bytes = zlib.decompress(body_bytes, -zlib.MAX_WBITS)

    if 300 <= status_code < 400:
        location = headers.get("location", "")
        if location:
            if location.startswith("/"):
                location = f"{scheme}://{host}{location}"
            elif not location.startswith("http"):
                location = urljoin(url, location)
            print(f"  Redirecting to {location}", file=sys.stderr)
            return http_request(location, accept=accept, redirects=redirects + 1)

    return status_code, headers, body_bytes


def _decode_chunked(data: bytes) -> bytes:
    result = b""
    while data:
        crlf = data.find(b"\r\n")
        if crlf == -1:
            break
        try:
            size = int(data[:crlf].split(b";")[0].strip(), 16)
        except ValueError:
            break
        if size == 0:
            break
        chunk_start = crlf + 2
        result += data[chunk_start: chunk_start + size]
        data = data[chunk_start + size + 2:]
    return result
