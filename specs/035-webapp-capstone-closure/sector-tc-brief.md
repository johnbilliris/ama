# Spec-035 — Sector Panel: Territories + Commonwealth + Cross-sector

**To**: All territory + Commonwealth + cross-sector agents in `.github/agents/sectors/{act,nt,commonwealth,cross-sector,*}/`.
**From**: Spec author.
**Subject**: We need user requirements and clarifications for spec-035 — Web Application Capstone Closure.

## Why you are being asked

Spec-034 cycle-1 review surfaced 5 material gaps from your panel (consolidated-review.md §D). Cycle-1 implement closed them **in the test suite** by adding 8 net-new specs (T192..T199): ACT national-capital, NT ATSI, NT tropical disease, Commonwealth ABC AWS, Commonwealth SBS AWS, cross-sector insurance, cross-sector DACC/JATWC, cross-sector built+economic recovery. Those specs assert against UI affordances that **do not yet exist in `apps/web/src/`**. Spec-035 must close that delta.

## Web-app gaps you raised (confirm or escalate)

### ACT — National-capital security mechanics
Spec needs: a Parliamentary-precinct / Defence-precinct overlay UI showing federal-tenancy collisions, AFP-led command transitions, and emergency-declaration mechanics for the ACT territory-government flow (which has different mechanics from a state). Web app today: ACT renders identically to every state; no precinct overlay; no federal-tenancy view; emergency-declaration UI does not differentiate territory vs state.

### NT — ATSI multilingual at persona level
Spec needs: NT-specific ATSI language packs (Yolŋu Matha, Pitjantjatjara, Warlpiri at minimum), persona-level multilingual surfaces (not just cross-cutting plumbing), and remote-area community-elder approval routing. Web app today: generic territory multilingual guidance; no NT-specific language pack; no remote-elder approval surface.

### NT — Tropical disease + remote-area logistics
Spec needs: a tropical-disease scenario surface (mosquito-borne outbreak, Strongyloides cluster, melioidosis post-flood), remote-area logistics (air-medevac, RFDS coordination, store-and-forward telemedicine), and a public-health audit trail. Web app today: not present.

### Commonwealth — ABC / SBS AWS exercise at persona level
Spec needs: ABC Emergency / SBS Emergency persona surfaces that consume a published AWS warning, render multi-language broadcast scripts, and audit broadcast acknowledgement. Web app today: PIO publishes warnings (see operational-brief.md), but no downstream broadcaster persona consumes them.

### Commonwealth — Additional persona surfaces
Spec needs: AGD, ABC Emergency, ABCB, BNHCRC, JATWC, JUSF, SBS Emergency, Insurance Council Australia personas (currently only 11 Commonwealth personas vs. roster requirement). Each requires its own workspace surface, role-specific audit, and handoff to operational personas.

### Cross-sector — Insurance recovery + DACC/JATWC handoff
Spec needs: an insurance-recovery surface (Insurance Council Australia liaison, claims-velocity dashboard, recovery-funding handoff to state authority), a DACC (Defence Aid to the Civil Community) request/approval surface, and a JATWC (Joint Australian Tsunami Warning Centre) handoff surface that connects BoM's tsunami warning to state SES + Commonwealth NEMA. Web app today: not present.

### Cross-sector — Built + Economic Recovery Environment
Spec needs: built-environment recovery surface (housing-restoration tracking, infrastructure rebuild prioritisation) and economic-recovery surface (small-business grants, supply-chain restoration, tourism reactivation). Web app today: only response-phase surfaces exist; recovery is reduced to a single "handover" stub.

## Cross-cutting for your panel

- **AWS warning compliance**: must be enforceable across BoM-adjacent personas, ABC/SBS broadcasters, AFAC AWS-style public-warning personas, and territory-government channels (ACT-specific + NT-specific).
- **Sovereignty + Foundry carve-out**: spec-034 only mentions sovereignty in plumbing; this panel needs the **UI to surface** when an AI-assisted recommendation is from a sovereign-only model vs. a carve-out model, and audit the choice. Today: not surfaced.
- **DACC lifecycle**: ADF → NEMA → state pathway needs a UI surface, including request, approval, deployment, withdrawal, and after-action.

## Asks of you

For each gap, please respond with:
1. Final user requirement statement
2. Acceptance criteria (Given/When/Then form)
3. Constitutional anchor (NN-1..NN-5, QG-1..QG-3) and any spec-034 FR / SC clause your requirement falls under
4. Edge cases — federal-state-territory escalation, multi-jurisdictional simultaneity, ATSI/palawa-protocol fallback
5. Whether the existing spec-034 cycle-1 net-new spec for your jurisdiction (T192..T199) correctly captures the depth your persona needs (PASS / NEEDS-DEEPENING)
6. Any persona currently absent from the FR-002 inventory that you believe must be added (will require a separate scope decision — flag it)
