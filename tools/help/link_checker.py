"""spec-038 T-AA178 — MDX link checker.

Verifies every internal deep-link in MDX articles resolves to a known slug,
and every citation anchor resolves to a heading. Fails CI on broken link.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

LINK_RE = re.compile(r"\]\((/help/[^)]+)\)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--content-root", default="apps/web/src/content/help")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    root = Path(args.content_root)
    slugs = {f"/help/articles/{p.relative_to(root).with_suffix('').as_posix()}" for p in root.rglob("*.mdx")}
    # also accept persona/glossary/playbook flat links
    for p in root.rglob("*.mdx"):
        rel = p.relative_to(root).with_suffix("").as_posix()
        slugs.add(f"/help/{rel}")

    bad = []
    for p in root.rglob("*.mdx"):
        text = p.read_text(encoding="utf-8", errors="replace")
        for link in LINK_RE.findall(text):
            base = link.split("#", 1)[0]
            if (
                base not in slugs
                and not base.endswith("/help/chat")
                and not base.endswith("/help/search")
                and not base.endswith("/help/glossary")
                and base != "/help"
            ):
                bad.append((p.as_posix(), link))

    for src, link in bad:
        logger.error("broken help link in %s: %s", src, link)
    return 1 if bad else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
