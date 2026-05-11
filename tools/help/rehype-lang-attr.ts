/**
 * spec-038 T-AA007 / T-AA179 — rehype plug-in.
 *
 * Walks the MDX HAST tree and enforces that any glossary-tagged non-English
 * fragment carries a BCP-47 ``lang`` attribute (FR-009a / FR-009a-AMEND).
 */
import type { Root, Element, Text } from "hast";
import type { Plugin } from "unified";

export interface RehypeLangAttrOptions {
  /** When true, throw on missing lang attributes (CI gate). */
  strict?: boolean;
  /** Glossary terms that REQUIRE a lang attribute when used. */
  termsRequiringLang?: { term: string; lang: string }[];
}

const visit = (node: Element | Root, fn: (el: Element) => void): void => {
  if ((node as Element).type === "element") fn(node as Element);
  const children = (node as Root | Element).children ?? [];
  for (const c of children) {
    if ((c as Element).type === "element") visit(c as Element, fn);
  }
};

const rehypeLangAttr: Plugin<[RehypeLangAttrOptions?], Root> = (options = {}) => {
  const { strict = true, termsRequiringLang = [] } = options;
  return (tree: Root) => {
    const violations: string[] = [];
    visit(tree, (el) => {
      const props = (el.properties ?? {}) as Record<string, unknown>;
      const lang = props.lang as string | undefined;
      for (const { term, lang: requiredLang } of termsRequiringLang) {
        for (const c of el.children ?? []) {
          if ((c as Text).type === "text" && (c as Text).value.includes(term)) {
            if (lang !== requiredLang) {
              violations.push(`<${el.tagName}> contains "${term}" but lang="${requiredLang}" required (found ${lang ?? "none"})`);
            }
          }
        }
      }
    });
    if (violations.length && strict) {
      throw new Error(`rehype-lang-attr: ${violations.length} violations:\n  ${violations.join("\n  ")}`);
    }
  };
};

export default rehypeLangAttr;
