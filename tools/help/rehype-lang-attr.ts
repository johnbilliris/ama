/**
 * spec-038 T-AA007 / T-AA179 — rehype plug-in stub.
 *
 * Walks the MDX HAST tree and (at full implementation) enforces that any
 * declared glossary-tagged non-English fragment carries a BCP-47 ``lang``
 * attribute (FR-009a / FR-009a-AMEND). The stub is registered in
 * ``apps/web/next.config.mjs`` so the build pipeline is wired before the
 * authoring-time linter (T-AA179) lands.
 */
import type { Plugin } from 'unified';
import type { Root } from 'hast';

export interface RehypeLangAttrOptions {
  /** When true, throw on missing lang attributes (CI gate). */
  strict?: boolean;
}

const rehypeLangAttr: Plugin<[RehypeLangAttrOptions?], Root> = (_options = {}) => {
  return (_tree: Root) => {
    // Stub — full visitor lands in T-AA179.
    return;
  };
};

export default rehypeLangAttr;
