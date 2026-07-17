"""Markdown -> HTML rendering.

`render_markdown` is the raw render (used by GET /concepts/{id}?render=true). `render_body_html` rewrites
bundle-local `.md` links to `/ui/concepts/<id>` routes so in-body cross-links work inside the web UI.
"""

from markdown_it import MarkdownIt

from app.links import resolve_target

_md = MarkdownIt("commonmark", {"html": False, "linkify": True})


def render_markdown(text: str) -> str:
    return _md.render(text)


def render_body_html(body: str, source_id: str) -> str:
    tokens = _md.parse(body, {})
    for token in tokens:
        if token.type != "inline" or not token.children:
            continue
        for child in token.children:
            if child.type == "link_open":
                href = child.attrGet("href")
                target = resolve_target(source_id, href) if href else None
                if target is not None:
                    child.attrSet("href", f"/ui/concepts/{target}")
    return _md.renderer.render(tokens, _md.options, {})
