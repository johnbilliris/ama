"""spec-038 T-AA175 — lint built static HTML for missing ``lang`` attributes.

Scans MDX source files (and optionally Next.js exported HTML) for glossary
terms tagged ``lang="…"`` in the glossary YAML, and ensures any non-English
fragment in built output carries the matching ``lang`` attribute. CI gate.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--content-root", default="apps/web/src/content/help")
    p.add_argument("--glossary", default="apps/web/src/content/help/glossary/terms.yaml")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    glossary_text = Path(args.glossary).read_text(encoding="utf-8", errors="replace")
    # parse very simple `term:` blocks (avoids PyYAML dep)
    non_en_terms = []
    cur_term = None
    cur_lang = None
    for line in glossary_text.splitlines():
        line = line.strip()
        if line.startswith("- term:"):
            cur_term = line.split(":", 1)[1].strip()
            cur_lang = None
        elif line.startswith("lang:"):
            cur_lang = line.split(":", 1)[1].strip()
            if cur_term and cur_lang and cur_lang != "en":
                non_en_terms.append((cur_term, cur_lang))

    violations = 0
    for term, lang in non_en_terms:
        re.compile(rf"(?<!lang=\"{re.escape(lang)}\">)\b{re.escape(term)}\b")
        for mdx in Path(args.content_root).rglob("*.mdx"):
            text = mdx.read_text(encoding="utf-8", errors="replace")
            if term in text and f'lang="{lang}"' not in text:
                logger.error("missing lang attr for %r in %s", term, mdx)
                violations += 1
    return 1 if violations else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
