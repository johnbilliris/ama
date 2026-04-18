# Research: Multi-Jurisdiction Filter for Preparedness Page

**Feature**: 022-multi-jurisdiction-filter | **Date**: 2025-07-20

## R-001: Page Architecture — Server vs Client Component

**Context**: The current preparedness page (`page.tsx`) is a server component that fetches data at request time with hardcoded `"nsw"`. With multi-select, the page must re-fetch data client-side based on user selections. What architecture pattern should we use?

**Decision**: Hybrid server/client architecture.

- `page.tsx` remains a server component that fetches the **jurisdiction list** (static, rarely changes) via `GET /api/jurisdictions` at request time, and reads URL search params to determine initial selection.
- A new `PreparednessClient` client component receives the jurisdiction list as a prop and owns all client-side state: selected jurisdictions, debounced API calls, URL synchronisation, loading/error states.
- `OperatingModelAnalyzer` becomes a presentation component receiving `organisations`, `frameworks`, `selectedJurisdictionIds`, and replay callbacks as props.

**Rationale**: This avoids converting the entire page to client-side while keeping the jurisdiction list (which changes infrequently) server-fetched for faster initial render. The client component handles dynamic state that changes with user interaction. This follows Next.js 16 App Router best practices of pushing client boundaries as low as possible.

**Alternatives considered**:
1. **Full client component**: Convert `page.tsx` to `"use client"`. Rejected because it loses server-side rendering benefits for the page shell and jurisdiction list, and doesn't follow the Next.js 16 composition pattern used elsewhere in the codebase.
2. **Server Actions with revalidation**: Use Next.js server actions to re-fetch. Rejected because server actions trigger full round trips and don't support the debounced, client-driven interaction model required (300ms debounce, inline loading).
3. **React Server Components with Suspense boundaries**: Use `searchParams` on the server to fetch filtered data on each navigation. Rejected because URL param changes would cause full server round trips instead of client-side API calls, violating the <2s update requirement and preventing inline loading indicators.

---

## R-002: Multi-Value Query Parameter Pattern for REST API

**Context**: The organisations and frameworks endpoints currently accept `?jurisdictionId=nsw` (single value). We need to support multiple jurisdictions. What REST pattern should we use?

**Decision**: Repeated query parameter pattern: `?jurisdictionId=nsw&jurisdictionId=vic&jurisdictionId=qld`.

- FastAPI natively supports this with `Query(default=[])` type annotation: `jurisdictionId: list[str] = Query(default=[])`.
- This is backward compatible — a single `?jurisdictionId=nsw` produces `["nsw"]`.
- When no `jurisdictionId` is provided, the parameter defaults to an empty list, which the service interprets as "no filter" (returns empty result per FR-006).

**Rationale**: Repeated query parameters are a well-established REST convention (RFC 6570), supported natively by browsers (`URLSearchParams.append()`), FastAPI (`Query` type), and HTTP clients. No custom parsing logic needed on either side.

**Alternatives considered**:
1. **Comma-separated single parameter**: `?jurisdictionId=nsw,vic`. Requires manual splitting on the server and doesn't leverage FastAPI's built-in query list support. Would need custom validation.
2. **JSON array in query string**: `?jurisdictionId=["nsw","vic"]`. Non-standard, requires URL encoding, not human-readable, and adds parsing complexity.
3. **POST request with body**: Changes the HTTP method semantics for what is fundamentally a read operation. Breaks RESTful conventions and prevents browser caching/bookmarking.

---

## R-003: URL State Persistence Pattern

**Context**: Per FR-014 and the URL-driven filter state pattern from spec 020, jurisdiction selection must be persisted in URL query parameters for shareability. What URL format should we use?

**Decision**: Comma-separated URL parameter: `/preparedness?jurisdictions=nsw,vic,qld`.

- Uses Next.js `useSearchParams()` hook to read and `useRouter().replace()` to update URL without navigation.
- On page load, `page.tsx` reads `searchParams.jurisdictions` (server-side from the `searchParams` prop), splits on comma, validates against the jurisdiction list, and passes valid IDs to the client component as `initialSelectedIds`.
- Invalid IDs are silently dropped per FR-014.
- When no params present, defaults to empty selection (empty state).

**Rationale**: Comma-separated is more URL-friendly and human-readable than repeated params for the user-facing URL (e.g., bookmarks, shared links). Note this is separate from the API query parameter pattern (R-002) — the URL uses `jurisdictions=nsw,vic` while the API call uses `jurisdictionId=nsw&jurisdictionId=vic`. This separation is intentional: the URL is for human consumption, the API follows REST conventions.

**Alternatives considered**:
1. **Repeated URL params**: `/preparedness?jurisdictions=nsw&jurisdictions=vic`. Longer URLs, less human-readable, harder to manually edit or share verbally.
2. **Path segments**: `/preparedness/nsw/vic`. Impractical for variable-length selections, breaks Next.js App Router routing.
3. **Hash fragment**: `/preparedness#nsw,vic`. Not accessible to server-side rendering, not indexed, non-standard for filter state.

---

## R-004: Client-Side Data Fetching and Debounce Strategy

**Context**: NFR-002 requires 300ms debounce on jurisdiction selection changes before triggering API calls. The codebase has no data fetching library (no SWR, React Query, etc.) — only native `fetch`. What approach should we use?

**Decision**: Custom `useDebounce` hook + native `fetch` with AbortController for request cancellation.

- A `useDebounce<T>(value: T, delay: number)` hook returns the debounced value.
- A `useEffect` watches the debounced `selectedJurisdictionIds` and triggers parallel `fetch` calls to `/api/organisations` and `/api/frameworks`.
- Each fetch uses `AbortController` to cancel stale in-flight requests when a newer selection arrives (addresses the edge case in the spec about stale response discarding).
- Loading and error states are managed per-catalog (organisations vs frameworks) for independent inline indicators per FR-013.

**Rationale**: The codebase uses no external data-fetching library — all existing API clients use native `fetch`. Adding SWR or React Query for a single feature would add a dependency the rest of the codebase doesn't use. A custom debounce hook is ~10 lines and provides exactly the behavior needed. `AbortController` is the standard Web API for request cancellation, supported in all target browsers.

**Alternatives considered**:
1. **SWR**: Powerful caching and revalidation, but adds a new dependency for a single page. The codebase doesn't use it elsewhere. Overkill for this feature's needs.
2. **React Query (TanStack Query)**: Even heavier than SWR. Same concern about introducing a new dependency.
3. **setTimeout/clearTimeout in event handler**: Less composable than a hook, harder to test, and doesn't integrate as cleanly with React's render cycle.

---

## R-005: Multi-Select Component Accessibility Pattern

**Context**: NFR-001 requires WCAG 2.1 AA compliance including full keyboard navigation and screen reader support. The codebase has no existing multi-select component. What pattern should we use?

**Decision**: Custom `<JurisdictionSelector>` using a listbox pattern with checkboxes.

- Uses a button that toggles a dropdown panel (disclosure pattern).
- Inside the panel: a list of checkboxes, one per jurisdiction, plus "Select All" and "Clear All" buttons at the top.
- ARIA attributes: `role="listbox"` on the container, `role="option"` with `aria-selected` on each item, `aria-expanded` on the trigger button, `aria-label` for the control.
- Keyboard: `Tab` focuses the trigger → `Enter`/`Space` opens dropdown → `Arrow Up/Down` navigates options → `Space` toggles selection → `Escape` closes dropdown.
- The trigger button displays a summary: "3 jurisdictions selected" or "No jurisdictions selected".

**Rationale**: A custom listbox with checkboxes matches the WAI-ARIA Listbox pattern for multi-select, provides full keyboard navigation, and allows custom styling consistent with the existing CSS-only approach (no Tailwind or CSS-in-JS). Using native `<input type="checkbox">` inside each option gives inherent accessibility without additional ARIA overhead on the toggle interaction.

**Alternatives considered**:
1. **Native `<select multiple>`**: Poor UX (requires Ctrl/Cmd+click), inconsistent cross-browser styling, no "Select All" capability, not accessible enough for complex multi-select workflows.
2. **Headless UI library (Radix, Headless UI)**: Would add a new dependency. The codebase uses plain CSS and no component library. The 9-item jurisdiction list doesn't need the complexity of a full headless combobox.
3. **Combobox with typeahead**: Over-engineered for 9 items. Typeahead is useful for long lists but unnecessary when all items are visible at once.

---

## R-006: Framework Filtering via FrameworkAssignment

**Context**: Per spec 018 and FR-003, `OperatingFramework` has no direct `jurisdiction_id` field. Jurisdiction applicability is determined via `FrameworkAssignment` records. However, the current seed data does NOT include a separate `framework_assignments_australia.json` file. The `PreparednessAnalysisService.analyse()` currently synthesises assignments on-the-fly. How should framework filtering work?

**Decision**: Add a `framework_assignments_australia.json` seed file and filter frameworks through assignments.

- Create a new seed file mapping framework IDs to jurisdiction IDs.
- Update `bootstrap_seed_data()` to load `framework_assignments`.
- The frameworks endpoint queries: "for the given jurisdiction_ids, find all FrameworkAssignment records where `jurisdiction_id` is in the set, then return the distinct OperatingFrameworks referenced by those assignments."
- This is the canonical approach per spec 018's data model.

**Rationale**: The current `analyse()` method creates synthetic assignments (every framework × every jurisdiction), which means frameworks are never actually filtered by jurisdiction. For the multi-jurisdiction filter to be meaningful, real assignment data must exist. Adding a seed file follows the established seed data pattern and makes the feature testable with known data.

**Alternatives considered**:
1. **Add `jurisdiction_ids` directly to OperatingFramework**: Contradicts the spec 018 data model which explicitly uses junction records. Would require model changes across the codebase.
2. **Keep synthetic assignments**: Would mean the frameworks endpoint always returns ALL frameworks regardless of jurisdiction selection, making the filter meaningless.
3. **Infer from organisation-framework relationships**: No such relationship exists in the current data model.

---

## R-007: Tenant Scoping for Data Layer Queries

**Context**: FR-005 requires tenant_id in all data layer queries (per specs 007, 021). Currently, the organisations and frameworks routes don't use tenant_id. The tenant middleware sets `request.state.tenant_context` but the preparedness routes don't read it. How should we handle this?

**Decision**: Acknowledge tenant_id requirement; implement as pass-through in route handlers.

- Add `request: Request` parameter to the organisations, frameworks, and jurisdictions route handlers.
- Extract `tenant_id` from `request.state.tenant_context.tenant_id` (set by existing `TenantMiddleware`).
- Pass `tenant_id` to service methods for future Cosmos DB scoping.
- For the current seed-data-based implementation, tenant_id is accepted but not used for filtering (seed data is shared across tenants). This is consistent with how other seed-based services work.
- Log a debug message when tenant_id is received for observability.

**Rationale**: Adding the tenant_id parameter now ensures the API contract is correct for when the data layer migrates from seed files to Cosmos DB. It also satisfies FR-005's requirement without breaking existing functionality.

**Alternatives considered**:
1. **Ignore tenant_id entirely**: Violates FR-005 and specs 007/021. Would require API changes later.
2. **Full Cosmos DB integration**: Out of scope for this feature. Seed data is the current storage mechanism.
3. **Filter seed data by tenant_id**: Seed data has no tenant_id concept. Would require adding tenant_id to all seed records.

---

## R-008: Backward Compatibility of API Changes

**Context**: Existing code calls `GET /api/organisations?jurisdictionId=nsw` (single value). Tests verify this contract. How do we ensure backward compatibility?

**Decision**: The `list[str]` Query parameter in FastAPI automatically handles both single and multiple values.

- `?jurisdictionId=nsw` → `["nsw"]` ✅ backward compatible
- `?jurisdictionId=nsw&jurisdictionId=vic` → `["nsw", "vic"]` ✅ new multi-value
- No `jurisdictionId` param → `[]` ✅ new empty-state behavior (returns empty list per FR-006)

**Rationale**: FastAPI's `Query` type with `list[str]` default handles all three cases. The only behavioral change is when no `jurisdictionId` is provided: previously, the organisations endpoint returned ALL organisations; now it returns an empty list (per FR-006: "When no jurisdictions are selected, return empty"). The frameworks endpoint previously defaulted to `["nsw"]`; now it returns empty. This is the intended breaking change per the spec.

**Alternatives considered**:
1. **New endpoint versions**: `/api/v2/organisations`. Over-engineered for this change; the behavior change only affects the empty-parameter case.
2. **Optional backward-compat default**: Fall back to `["nsw"]` when empty. Contradicts FR-006's explicit requirement for empty-state behavior.

---

## R-009: Stale Replay Results Handling

**Context**: FR-015 requires clearing replay results when jurisdiction selection changes after a replay has completed. How should this be implemented?

**Decision**: Track `replayJurisdictions` state in the client component.

- When a replay completes, store the `selectedJurisdictionIds` at the time of replay as `replayJurisdictions`.
- On every jurisdiction selection change, compare current `selectedJurisdictionIds` with `replayJurisdictions`.
- If they differ, clear the replay results and show a notice: "Replay results were generated for different jurisdictions. Run a new replay for updated results."
- Use a deep equality check (sorted array comparison) since jurisdiction order doesn't matter.

**Rationale**: Simple state comparison avoids complex event tracking. Storing the replay's jurisdiction context alongside its results makes the staleness check self-contained in the client component.

**Alternatives considered**:
1. **Timestamp-based invalidation**: Complex and doesn't address the actual requirement (jurisdiction mismatch, not time).
2. **Server-side replay invalidation**: Adds unnecessary server round trips for a purely client-side UX concern.
3. **Always clear replay on any change**: Overly aggressive — doesn't show the helpful notice about why results were cleared.
