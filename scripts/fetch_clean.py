"""fetch_clean.py — token-efficient web content fetcher for research subagents.

Usage:
    python scripts/fetch_clean.py <url> [--max-chars N] [--jina-fallback]

Behavior:
  - GitHub repo roots and blob URLs → raw.githubusercontent.com (verbatim, no trafilatura)
  - raw.githubusercontent.com, arxiv.org/abs, *.md, *.txt → fetch & return as-is
  - HTML pages → trafilatura → BeautifulSoup/lxml fallback → (optional) Jina Reader fallback
  - Output: clean markdown to stdout, truncated to --max-chars (default 40000)
  - Failure: non-zero exit + one-line stderr; never dumps raw HTML

Importable API:
    from scripts.fetch_clean import fetch_clean, rewrite_github_url
"""
from __future__ import annotations

import re
import sys
from typing import Optional
from urllib.parse import urlparse

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_UA = "Mozilla/5.0 (compatible; research-fetch/1.0)"
_TIMEOUT = 20
_THIN_THRESHOLD = 200  # chars; below this, trafilatura output is considered empty/thin
_DEFAULT_MAX_CHARS = 40_000
_TRUNCATION_MARKER = "\n[truncated]"


# ---------------------------------------------------------------------------
# GitHub URL rewriting
# ---------------------------------------------------------------------------

def rewrite_github_url(url: str) -> Optional[str]:
    """Rewrite a github.com URL to the corresponding raw.githubusercontent.com URL.

    Handles two cases:
      1. Repo root: github.com/<org>/<repo>  →  tries README.md on main then master
      2. Blob file: github.com/<org>/<repo>/blob/<ref>/<path>  →  raw file URL

    Returns the raw URL string if the URL is a rewritable GitHub URL, else None.
    For repo roots, fetches to find the actual default branch (main/master).
    Raises requests.HTTPError / ConnectionError on network failure when needed.
    """
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        return None

    path_parts = [p for p in parsed.path.split("/") if p]

    # Need at least org/repo
    if len(path_parts) < 2:
        return None

    org = path_parts[0]
    repo = path_parts[1]
    if repo.endswith(".git"):
        repo = repo[: -len(".git")]

    # Case 1: repo root (path has exactly org/repo, possibly with trailing slash)
    if len(path_parts) == 2:
        # Try main then master for README.md
        for branch in ("main", "master"):
            raw_url = f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/README.md"
            try:
                resp = requests.head(raw_url, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
                if resp.status_code == 200:
                    return raw_url
            except Exception:
                continue
        # If neither worked, try GET on main (will fail loudly on fetch)
        return f"https://raw.githubusercontent.com/{org}/{repo}/main/README.md"

    # Case 2: blob file URL: github.com/<org>/<repo>/blob/<ref>/<path...>
    if len(path_parts) >= 5 and path_parts[2] == "blob":
        ref = path_parts[3]
        file_path = "/".join(path_parts[4:])
        return f"https://raw.githubusercontent.com/{org}/{repo}/{ref}/{file_path}"

    # Other GitHub paths (issues, pulls, tree, etc.) — not rewritable
    return None


# ---------------------------------------------------------------------------
# URL classification helpers
# ---------------------------------------------------------------------------

def _is_already_clean(url: str) -> bool:
    """Return True if the URL points to already-clean content (raw text/markdown).

    arxiv.org/abs/* pages are HTML abstracts — they go through the HTML extraction
    path (trafilatura). Only truly raw text URLs are classified as already-clean.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.lower()

    if netloc == "raw.githubusercontent.com":
        return True
    if path.endswith(".md") or path.endswith(".txt") or path.endswith(".rst"):
        return True
    return False


# ---------------------------------------------------------------------------
# Fetching helpers
# ---------------------------------------------------------------------------

def _fetch_bytes(url: str) -> bytes:
    """Fetch URL and return raw bytes. Raises on HTTP error or network issue."""
    resp = requests.get(url, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.content


def _decode(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_trafilatura(html: bytes, url: str) -> Optional[str]:
    """Run trafilatura extraction. Returns None if empty/thin."""
    try:
        import trafilatura
        result = trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_links=False,
            include_images=False,
            favor_recall=True,
        )
        if result and len(result.strip()) >= _THIN_THRESHOLD:
            return result
        return None
    except Exception:
        return None


def _extract_lxml_fallback(html: bytes) -> Optional[str]:
    """Strip scripts/style/nav/footer using lxml or bs4, return plain text.

    Uses bs4 if available, else falls back to lxml.etree-based stripping.
    """
    # Try BeautifulSoup first (cleaner API)
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if len(text) >= _THIN_THRESHOLD:
            return text
        return None
    except ImportError:
        pass

    # lxml.html fallback
    try:
        from lxml import etree, html as lxml_html
        tree = lxml_html.fromstring(html)
        # Remove noisy tags
        for bad_tag in ("script", "style", "nav", "footer", "header", "aside"):
            for el in tree.findall(f".//{bad_tag}"):
                el.getparent().remove(el)
        text = "\n".join(tree.itertext())
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if len(text) >= _THIN_THRESHOLD:
            return text
        return None
    except Exception:
        return None


def _extract_jina(url: str) -> Optional[str]:
    """Fetch via Jina Reader (https://r.jina.ai/<url>). Returns None on failure."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        resp = requests.get(
            jina_url,
            headers={"User-Agent": _UA, "Accept": "text/plain"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        text = resp.text.strip()
        if text and len(text) >= _THIN_THRESHOLD:
            return text
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending [truncated] marker if cut."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    return cut + _TRUNCATION_MARKER


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_clean(
    url: str,
    max_chars: int = _DEFAULT_MAX_CHARS,
    jina_fallback: bool = False,
) -> str:
    """Fetch and clean a URL, returning clean text/markdown.

    Raises:
        requests.HTTPError: on HTTP 4xx/5xx
        requests.ConnectionError: on network failure
        ValueError: if all extraction paths return empty/thin content
    """
    # 1. GitHub rewrite (repo root or blob file)
    rewritten = rewrite_github_url(url)
    if rewritten is not None:
        content = _decode(_fetch_bytes(rewritten))
        return _truncate(content, max_chars)

    # 2. Already-clean content (raw URLs, arxiv abs, .md/.txt)
    if _is_already_clean(url):
        content = _decode(_fetch_bytes(url))
        # Light cleanup: strip only blank-line runs (preserve structure)
        content = re.sub(r"\n{3,}", "\n\n", content)
        return _truncate(content, max_chars)

    # 3. HTML page: trafilatura → lxml/bs4 → optional Jina
    raw_html = _fetch_bytes(url)

    # 3a. trafilatura
    result = _extract_trafilatura(raw_html, url)
    if result:
        return _truncate(result, max_chars)

    # 3b. lxml/bs4 strip
    result = _extract_lxml_fallback(raw_html)
    if result:
        return _truncate(result, max_chars)

    # 3c. Jina Reader fallback (only if requested)
    if jina_fallback:
        result = _extract_jina(url)
        if result:
            return _truncate(result, max_chars)

    raise ValueError(
        f"All extraction paths returned empty/thin content for: {url}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str]):
    import argparse
    parser = argparse.ArgumentParser(
        description="Fetch and clean a URL to clean markdown text.",
    )
    parser.add_argument("url", help="URL to fetch and clean")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=_DEFAULT_MAX_CHARS,
        metavar="N",
        help=f"Maximum output characters (default: {_DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--jina-fallback",
        action="store_true",
        default=False,
        help="Fall back to https://r.jina.ai/<url> if local extraction fails",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point. Returns exit code."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        text = fetch_clean(
            args.url,
            max_chars=args.max_chars,
            jina_fallback=args.jina_fallback,
        )
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return 0
    except (requests.HTTPError, requests.ConnectionError) as exc:
        print(f"fetch error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
