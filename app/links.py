"""Extract markdown links from a concept body and resolve them to concept IDs.

Cross-links between concepts form the catalog's graph. Only bundle-local links become edges;
external URLs (http, mailto, //host) and pure anchors are dropped.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from urllib.parse import urlsplit

from markdown_it import MarkdownIt

_md = MarkdownIt()


@dataclass(frozen=True)
class RawLink:
    anchor_text: str
    href: str


def extract_links(body: str) -> list[RawLink]:
    """Return every `[text](href)` link in the body, in document order. Images are excluded."""
    links: list[RawLink] = []
    for token in _md.parse(body):
        if token.type != "inline" or not token.children:
            continue
        children = token.children
        i = 0
        while i < len(children):
            child = children[i]
            if child.type == "link_open":
                href = child.attrGet("href") or ""
                text_parts: list[str] = []
                j = i + 1
                while j < len(children) and children[j].type != "link_close":
                    if children[j].type in ("text", "code_inline"):
                        text_parts.append(children[j].content)
                    j += 1
                links.append(RawLink(anchor_text="".join(text_parts), href=str(href)))
                i = j
            i += 1
    return links


def resolve_target(source_id: str, href: str) -> str | None:
    """Resolve an href (relative to the source concept) to a concept ID, or None if external.

    External (http/https/mailto/protocol-relative) and pure-anchor links return None.
    Fragments and query strings are dropped; a trailing `.md` is stripped.
    """
    href = href.strip()
    if not href or href.startswith("#"):
        return None

    parts = urlsplit(href)
    if parts.scheme or parts.netloc:  # http:, https:, mailto:, //host
        return None

    path = parts.path
    if not path:
        return None

    if path.startswith("/"):
        target = path.lstrip("/")
    else:
        source_dir = posixpath.dirname(source_id)
        target = posixpath.normpath(posixpath.join(source_dir, path))

    if target.lower().endswith(".md"):
        target = target[:-3]

    if target in ("", "."):
        return None
    return target


def resolved_links(source_id: str, body: str) -> list[tuple[str, str]]:
    """Bundle-local links from a body as (target_concept_id, anchor_text), external ones dropped."""
    out: list[tuple[str, str]] = []
    for raw in extract_links(body):
        target = resolve_target(source_id, raw.href)
        if target is not None:
            out.append((target, raw.anchor_text))
    return out
