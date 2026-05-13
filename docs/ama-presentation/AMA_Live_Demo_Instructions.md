# Live demo runbook — Blue Mountains / Lithgow bushfire

> **Scenario.** Fast-moving bushfire on the western face of Blue Mountains National Park; ember attack threatening Lithgow within four hours. NSW RFS lead, with police, SES, ambulance, hospitals, transport and Lithgow City Council in the response.
>
> **Goal.** Run the same canonical scenario twice (deterministic seed) — once as a **Baseline (no AMA)** and once **AMA-assisted** — then walk an Incident Controller through the AMA workspace, hitting all five "watch for" markers below.

## Watch-for matrix (call these out live)

| # | Marker | Where on screen | When |
|---|---|---|---|
| 1 | Signal ingestion < 10 s | Window B → left panel **Signals & Resources** meter + **Event Log** timestamps | After §3a SITREP |
| 2 | Recommendation < 30 s | Window B → chat pane recommendation card timestamp − scenario-seeded timestamp | After §3b Risk |
| 3 | Approval request to a **named** Incident Controller | IC workspace → IC Approval Card → "Approver identity" field | §4 |
| 4 | Multilingual alert including Auslan stub | PIO workspace → 7 variant blocks (6 languages + auslan) | §5 |
| 5 | Audit chain reachable in two clicks | IC Approval Card → audit_id → Decision Chain panel | §6 |

---

## 0 · Pre-flight (do this **before** the audience is watching)

In three separate terminals from the repo root (see [README.md](../../README.md#run-locally)):

```pwsh
# Terminal 1 — API runtime
cd apps/api
uv run uvicorn main:app --reload --port 8000

# Terminal 2 — Agent runtime
cd apps/agents
uv run python -m agents

# Terminal 3 — Web runtime
cd apps/web
pnpm dev
```

Then open **two side-by-side browser windows** at <http://127.0.0.1:3000>:

- **Window A** — labelled "Baseline (no AMA)"
- **Window B** — labelled "AMA-assisted"

In each window confirm the top nav shows: *Disaster Map · Workspaces · Sectors · Governance · Simulations · Preparedness · Help* (rendered by [packages/ui/src/components/layout/app-shell.tsx](../../packages/ui/src/components/layout/app-shell.tsx#L6-L14)).

> **Determinism note.** The simulation engine seeds scenario cards from the prompt text + tenant scenario type. Use the **identical seed prompt** in both windows so the baseline and AMA runs see the same hazard envelope. The repo's demo NDJSON fixtures (e.g. `demo_cross_sector_v1.ndjson`) all use `seed=42`.

---

## 1 · Create the canonical scenario (do this in **both** windows)

In each window:

1. Click **🔬 Simulations** in the top nav → lands on [/simulations](../../apps/web/src/app/simulations/page.tsx).
2. Click the blue **Create Simulation** button (top right).
3. On [/simulations/create](../../apps/web/src/app/simulations/create/page.tsx):
   - **Scenario type** → `Bushfire`
   - **Jurisdictions** → click `NSW` (single select)
   - **Max signals** → `1000`, **Max recommendations** → `500`, **Max duration (h)** → `8`
   - **Time warp speed** → `5×` (so the 4-hour ember-attack window plays inside the demo slot)
4. Click **Create simulation**. You'll be redirected to `/simulations/{tenantId}` — the operator workspace.

> **Tip.** Write the two `tenantId`s on a sticky note. You'll need them for the post-run report in §7.

---

## 2 · Seed the scenario in **Window A (Baseline)** — no AMA assist

You're now on [/simulations/[tenantId]](../../apps/web/src/app/simulations/[tenantId]/page.tsx). On the **right-hand panel** ("Simulation Controller") paste this exact prompt into the chat box and press **Enter**:

```text
Fast-moving bushfire on the western face of Blue Mountains National Park,
ember attack threatening Lithgow within 4 hours. NW winds 55 km/h, 39 °C,
RH 8 %. NSW RFS lead; police, SES, ambulance, hospitals, transport, and
Lithgow City Council in the response. Start time 14:00 AEST.
```

Watch the centre map render the affected area and the left **Signals & Resources** meter start ticking up. **That is all you do in Window A.** The point of the baseline is to show:

- raw signals arriving with no automated triage
- no recommendation cards
- no approval request
- no multilingual draft
- the operator would now have to manually read each signal and call partners

Leave Window A on screen so the audience can compare.

---

## 3 · Seed the same scenario in **Window B (AMA-assisted)** — full chain

Paste the **same prompt** into the Simulation Controller chat. As soon as the green "Scenario seeded" card appears, run the agent chain by clicking the quick-action buttons at the bottom of the chat pane (defined in [apps/web/src/components/simulation-chat-pane.tsx](../../apps/web/src/components/simulation-chat-pane.tsx#L153-L160)) **in this order**:

| Step | Click | What it triggers | Watch-for marker |
|---|---|---|---|
| 3a | **📋 SITREP** | Monitoring agent fuses signals, posts a situation summary | **Signal ingestion < 10 s** — confirm via "Signals" meter jump and Event Log timestamps in the left panel |
| 3b | **⚠ Risk** | Risk Assessment agent generates a recommendation card | **Recommendation generation < 30 s** — confirm by the time delta between SITREP turn and the recommendation card |
| 3c | **🚒 Deploy** | Resource Allocation agent prioritises tasks | Coordination tasks appear in the simulation event log |
| 3d | **📢 Alert** | Communication agent drafts the public alert (this is what you'll approve in §5) | Alert turn lands in chat — leave it open |
| 3e | **⬆ Escalate** | Escalates to the named Incident Controller — **needed for the approval marker** | Banner: "Awaiting commander approval" |

While this is running the left panel shows: **PPRR badge → Response (red)**, **Status → Active**, the warp clock ticking, the **Signals** and **Recommendations** meters filling, and the **Event Log** capturing each turn with timestamps. Use the timestamps to call out the latency markers live.

---

## 4 · Open the Incident Controller workspace (named-approver step)

Open a **new tab** in Window B → click **👥 Workspaces** → pick **Incident Commander** → lands on [/workspaces/incident-commander](../../apps/web/src/app/workspaces/[personaId]/page.tsx).

Scroll to the **IC Approval Card** ([apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L37-L100)). It will show:

- **Rationale** from the Risk Assessment agent
- **Sources** with `doc_id` + excerpt links (citation envelope)
- **Confidence pill** (green ≥ 0.85, amber ≥ 0.6, rose otherwise)
- **Approver identity** — the named persona (e.g. `incident-commander`) — **this is your "Approval request to a named Incident Controller" marker**

Click the **Approve** button. The card will `POST /api/outcomes/sc-{N}/evaluate`, then re-fetch `/api/audit/list?correlation_id=...` and surface the resulting `audit_id` as a clickable link. **Hover over that link** — it points to `/governance/audit/{audit_id}`. **Don't click yet** — you'll need it for the two-click audit reveal in §6.

---

## 5 · Multilingual + Auslan draft (Public Information Officer)

Open a **new tab** → **Workspaces → Public Information Officer** → [/workspaces/public-information-officer](../../apps/web/src/app/workspaces/[personaId]/page.tsx). The **PIO AWS Composer** ([apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L41-L80)) loads with the language pack list from [apps/web/src/lib/i18n/language-packs.ts](../../apps/web/src/lib/i18n/language-packs.ts).

Configure the alert:

1. **Level** → `Emergency Warning`
2. **Hazard** → `Bushfire — ember attack`
3. **Location** → `Lithgow LGA`
4. **Action** → `Leave now via Great Western Highway eastbound. Avoid Bells Line of Road.`
5. **Languages** — tick: `en`, `zh-Hans`, `ar`, `vi`, `el`, `it`, **and `auslan`** (the Auslan stub is the last entry — see [language-packs.ts L89-L92](../../apps/web/src/lib/i18n/language-packs.ts#L89-L92))
6. Click **Draft variants** → the Communication agent returns six text blocks + the Auslan stub. **This is your "multilingual alert generation including Auslan stub" marker.**
7. Click **Run accessibility scan** to show the in-page WCAG 2.1 AA result.
8. Click **Request IC approval** to send the bundle back to the IC card.

> Mature Auslan rendering (video vs captioned still) lives at *Governance → Evidence → Public Information Channels* — open it as a follow-up if asked, see [PublicInformationChannels.tsx](../../apps/web/src/app/governance/evidence/_tabs/PublicInformationChannels.tsx#L1-L50).

---

## 6 · Audit chain reachable in **two clicks** ✅

From the IC Approval Card on the *Incident Commander* tab:

- **Click 1** → the `audit_id` link in the green success banner → opens [/governance/dashboard/audit](../../apps/web/src/app/governance/dashboard/audit/page.tsx).
- **Click 2** → click the matching audit row in the search table → the **Decision Chain** panel renders the full `signal → recommendation → approval → alert → publish` lineage with timestamps.

Call out the chain visually — that is your **"audit chain reachable in two clicks"** marker.

---

## 7 · Stop both runs and open the Exercise Report (baseline vs AMA-assisted)

In **each** window, on the simulation dashboard:

1. Click **Stop** (left **Controls** panel) → confirm the dialog. Status moves to `Archiving` then `Archived`.
2. The **▶ Review Playback** link appears next to "← Back to simulations". Click it to deep-replay the Event Log (scrub the clock, see annotations) — useful if a watcher missed a moment.
3. To compare metrics, navigate directly to:
   - `http://127.0.0.1:3000/simulations/reports/{tenantId-A}` — Baseline
   - `http://127.0.0.1:3000/simulations/reports/{tenantId-B}` — AMA-assisted

The report ([apps/web/src/app/simulations/reports/[reportId]/page.tsx](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L42-L160)) shows **Time to First Recommendation**, **Time to Alert Publication**, **Coordination Coverage %**, and a **Benchmark Comparison** table. Put the two browser tabs side by side — the AMA-assisted column will show populated metrics where the baseline shows `—`.

---

## Common gotchas

- If the Simulation Controller chat just echoes back without seeding a card, the agent runtime (Terminal 2) isn't reachable. Re-check `apps/agents` is running.
- If the IC Approval Card returns `evaluate-failed:404`, the audit pipeline isn't wired — check that the API in Terminal 1 mounted the `/api/outcomes/...` and `/api/audit/list` routes.
- Quick actions are disabled while the chat is **streaming** — wait for the previous turn to settle before clicking the next button so the audience sees clean per-step latencies.
- The **Stop** action is **terminal** — don't click it until you've finished §6.
