"""Markdown -> HTML rendering (used by GET ?render=true and the web UI)."""

from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False, "linkify": True})


def render_markdown(text: str) -> str:
    return _md.render(text)
