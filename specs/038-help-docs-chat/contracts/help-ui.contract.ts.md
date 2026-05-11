# Help UI — Module-Boundary Contract (TypeScript)

**Spec**: [`spec.md`](../spec.md) | **Plan**: [`../plan.md`](../plan.md) | **Date**: 2026-05-11

This is the binding contract for components and routes added to `apps/web/src/app/help/` and `apps/web/src/components/help/`. It defines the public props, route segments, accessibility primitives, and telemetry events that downstream tasks must implement. Types follow the existing `packages/domain/src/help/*.ts` twins.

---

## 1. Route segments

All routes mount under `apps/web/src/app/help/`.

| Route | File | Notes |
|---|---|---|
| `/help` | `page.tsx` | Persona-aware landing — derives default persona from IdP claim; honours `?persona=` query for override (validated against entitlements). |
| `/help/search` | `search/page.tsx` | Full-text search; `?q=` required. |
| `/help/chat` | `chat/page.tsx` | Full-page chat surface (the global header `?` button opens a side panel that links here). |
| `/help/articles/[slug]` | `articles/[slug]/page.tsx` | MDX-rendered article. |
| `/help/glossary/[term]` | `glossary/[term]/page.tsx` | Glossary term + cross-links. |
| `/help/playbooks/[id]` | `playbooks/[id]/page.tsx` | Long-form playbook (simulation, agent, observer). |

A persistent `<HelpAffordance />` is mounted in the global app header (existing `apps/web/src/app/layout.tsx`); it is keyboard-reachable via `Ctrl+/` on Windows/Linux and `⌘+/` on macOS.

---

## 2. Component public surface

### `<HelpAffordance />`

```ts
export type HelpAffordanceProps = {
  /** Current route id, used to deep-link "Help on this screen". */
  surfaceId: string;
  /** When true, opens the side panel automatically (e.g., from `?help=open` URL param). */
  initialOpen?: boolean;
};
```

A11y: button has `aria-label="Open help"`, `aria-keyshortcuts="Control+/ Meta+/"`. Side panel uses `role="dialog"` with focus trap and `Esc` to close.

### `<ChatPanel />`

```ts
import type { Citation, ChatTurn } from '@ama/domain/help';

export type ChatPanelProps = {
  sessionId?: string;
  initialMessage?: string;
  personaId: string;             // entitled override or IdP default
  jurisdictionCodes: string[];
  surfaceId?: string;
  /** Render the chat as disabled with the standard banner (FR-026 / FR-026a-AMEND). */
  degraded?: boolean;
  onTurnComplete?: (turn: ChatTurn) => void;
};
```

Streaming: consumes the SSE response from `POST /api/v1/help/chat/ask`. Renders `<RefusalCard />` on `refusal` events; renders `<DeprecationNotice />` on `deprecated_no_replacement` (FR-011d-AMEND). Citations attach to claims via `<CitationBadge />` (numbered, deep-link).

A11y: chat log is `role="log" aria-live="polite"`; status changes (typing, refusal, error) are announced. Input has visible focus indicator and minimum 44×44 px hit target.

### `<AnnotatedScreenshot />`

```ts
import type { AnnotatedScreenshot } from '@ama/domain/help';

export type AnnotatedScreenshotProps = {
  data: AnnotatedScreenshot;
  /** Theme is derived from the user's active theme; this prop is for Storybook tests only. */
  themeOverride?: 'light' | 'dark';
};
```

Renders the active-theme variant; `<picture>` with `prefers-color-scheme` fallback. Numbered callouts are presented as a list with `aria-describedby` pointing at the associated prose step. A `<KeyboardSteps />` block is always rendered adjacent (FR-008). When `data.staleness_flag_id` is set, `<StalenessBanner />` renders above (FR-010 / FR-010b).

### `<CitationBadge />`

```ts
export type CitationBadgeProps = {
  citation: Citation;
  /** Inline number, e.g. 1, 2, 3 — matches the order returned by the assistant. */
  number: number;
};
```

Renders an `<a>` with `aria-label="Open source: {source_title}"`. Activating it opens the cited article at the heading anchor. Hover/focus shows a popover with the snippet.

### `<StalenessBanner />`

```ts
export type StalenessBannerProps = {
  raisedAt: string;        // ISO
  graceReleaseId: string;
  downgraded?: boolean;    // true after grace expires (FR-010b)
};
```

`role="status"`. Wording: `"This image may be out of date — last verified for release {graceReleaseId}."` Downgraded variant adds: `"Screenshots not yet refreshed for this release."`

### `<DeprecationNotice />`

```ts
export type DeprecationNoticeProps = {
  retiredSnapshotId: string;
  retiredOn: string;       // ISO date
  replacementSlug?: string; // omitted ⇒ no replacement (FR-011d-AMEND triggers handoff)
};
```

When `replacementSlug` is omitted, the notice surfaces the tenant's `SupportHandoffRecord` channel inline (FR-011d-AMEND).

### `<RefusalCard />`

```ts
export type RefusalCardProps = {
  reason: 'out_of_scope' | 'cross_tenant' | 'no_corpus_match' | 'pii_blocked' | 'above_official_classification' | 'deprecated_no_replacement';
  suggestedSurfaces?: { label: string; href: string }[];
  handoff?: { label: string; href: string };
};
```

Always non-judgmental wording (FR-013); always offers a suggested surface or handoff (FR-014, FR-023).

### `<FeedbackBar />`

```ts
export type FeedbackBarProps = {
  targetKind: 'article' | 'chat_turn';
  targetId: string;
  onSubmitted?: (ack: { backlogItemId: string; promotedToNeedsReview: boolean }) => void;
};
```

Posts to `POST /api/v1/help/chat/feedback`. Confirms with a non-blocking toast. Never alters the rated content (FR-022a).

### `<PersonaTile />`

```ts
import type { PersonaHelpProfile } from '@ama/domain/help';

export type PersonaTileProps = {
  profile: PersonaHelpProfile;
  /** True when this is the user's currently-active persona. */
  active: boolean;
};
```

Multi-role landing renders the union of entitled tiles, ordered by `profile.authority_rank` descending (FR-028).

### `<KeyboardSteps />`

```ts
export type KeyboardStepsProps = {
  steps: string[];        // the ordered keyboard-equivalent path
  ariaLabelledby: string; // id of the screenshot caption
};
```

Renders an `<ol>` with `aria-labelledby` so screen-reader users hear the screenshot caption then the keyboard steps (FR-008).

---

## 3. Telemetry events (Application Insights — `appInsights.trackEvent`)

| Event name | Trigger | Properties |
|---|---|---|
| `help.affordance.opened` | `<HelpAffordance />` opens. | `surface_id`, `via: keyboard|click` |
| `help.article.viewed` | Article page mounts. | `article_id`, `persona_id`, `snapshot_id` |
| `help.search.performed` | `/help/search` returns. | `q_length`, `result_count`, `top_kind` |
| `help.chat.turn.requested` | SSE request started. | `session_id`, `persona_id`, `surface_id`, `degraded:false` |
| `help.chat.turn.completed` | `done` event received. | `session_id`, `turn_index`, `latency_ms`, `citation_count`, `refusal_reason?` |
| `help.chat.redaction_notified` | `meta.redaction_notice = true`. | `session_id` |
| `help.chat.degraded.shown` | Chat panel rendered in `degraded=true`. | `surface_id` |
| `help.feedback.submitted` | `<FeedbackBar />` submit. | `target_kind`, `target_id`, `rating` |
| `help.staleness.banner.shown` | `<StalenessBanner />` mounts. | `target_id`, `downgraded` |
| `help.deprecation.notice.shown` | `<DeprecationNotice />` mounts. | `retired_snapshot_id`, `has_replacement` |

PII rule: never include free-text user input in event properties. Telemetry pipeline is the existing AU-East App Insights workspace.

---

## 4. Accessibility primitives & gates

- All interactive elements: minimum 44×44 px hit target, visible focus ring (≥3:1 contrast), keyboard operability.
- Colour: minimum 4.5:1 (text) / 3:1 (UI components and graphics) per WCAG 2.2 AA.
- `lang` attributes on every embedded non-English fragment (FR-009a / FR-009a-AMEND); enforced via the rehype plug-in `tools/help/rehype-lang-attr.ts` at authoring time and `tools/help/lint_lang_attributes.py` at build.
- Screen-reader announcements: chat log uses `role="log" aria-live="polite"`; refusal/error states use `aria-live="assertive"`; status-bar banners use `role="status"`.
- Reduced-motion: any animations honour `prefers-reduced-motion`.
- Focus management: opening the Help side panel moves focus to the panel; closing returns focus to the affordance trigger.

CI gates (must pass to merge):

- `pnpm test:web-coverage:axe` — `@axe-core/playwright` over every Help route — zero Level A/AA violations.
- `pnpm --filter @ama/web test:a11y` — Vitest a11y unit suite (axe on rendered components).
- `pa11y-ci` over a representative URL list — zero AA violations.

---

## 5. Boundaries (out of scope for the UI module)

- Authentication/authorisation: relies on the existing MSAL flow (`@azure/msal-react`) and platform tenant claim; this module does not introduce its own auth.
- Persona entitlement check: server-side, rejected at `POST /help/chat/ask` with HTTP 403 if `persona_id` is not entitled (FR-028); UI shows a non-judgmental message but does not duplicate the policy.
- Audit log writes: server-side only; the UI never directly writes to `chat_audit_log`.
- MDX bundling: handled by Next.js build pipeline; not invoked at runtime.
