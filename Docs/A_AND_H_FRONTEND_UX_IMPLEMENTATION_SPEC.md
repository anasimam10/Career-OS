# A&H Career — Frontend Redesign & UX Architecture Specification

**Prepared for:** Implementation agent (Google Antigravity), with real repository access
**Prepared by:** Senior product design / UX architecture / frontend review (no repository access — specification based only on provided screenshots, `architecture_corrected.md` / `architecture_final.md` / `architecture_master.md`, `implementation-status.md`, and product-owner requirements)
**Target file:** this document, `A_AND_H_FRONTEND_UX_IMPLEMENTATION_SPEC.md`

> **Read this before anything else:** This document does **not** claim repository access. Every recommendation is labeled as one of four kinds: **Observed** (from provided screenshots/docs), **Design recommendation**, **Engineering requirement**, or **Unknown — Antigravity must inspect**. Where the provided `implementation-status.md` names actual files, routers, or endpoints, they are cited directly and treated as ground truth; everything else about the live repo state is explicitly flagged as unverified.

---

## 1. Executive Summary

A&H Career already has real substance behind it: a working FastAPI backend, a SQLite database seeded with genuine Pakistani university/opportunity/sports data, a Qwen-based mentor with a four-model fallback chain, an MCP retrieval layer with grounding/fallback discipline, and a Next.js 14 frontend with 11 pages and a working mock-mode. **This is not a UI-from-scratch project. It is a trust and polish project.** The backend is more mature than the frontend currently communicates.

The screenshots show a frontend that is functionally coherent but visually generic: heavy use of pill badges, red/orange "High/Very High" bars presented as if they were calculated scores, a hardcoded-feeling "demo student" journey state, and mentor UI that is closer to a labeled chatbot than a guidance product. `implementation-status.md` confirms the root causes are structural, not cosmetic: the frontend's session identity is **hardcoded to demo student ID=1** (`Frontend/lib/session.ts`), several "reality check" fields are AI-authored copy dressed as measurements, and there is no persisted per-visitor onboarding-to-profile flow described anywhere in the current implementation notes.

The good news: the backend has already solved the hard trust problem correctly. `career_service.py` enforces a **trust hierarchy in code** — Qwen may only contribute the `rewards` list and the verdict narrative; every factual field (demand, competition, difficulty, opportunity counts) is overwritten from SQLite after validation. The NBA (Next Best Action) engine is **candidate-constrained**: Qwen picks one candidate ID from a deterministic list generated from real DB records; it cannot invent a step. MCP search has a documented **ungrounded-answer guard**: if Qwen doesn't actually call a tool, its answer is discarded in favor of a direct DB query. This means the frontend's job is largely to **stop hiding this trust architecture behind decorative UI** and start **surfacing it directly** as the core visual language of the product.

This spec is organized so Antigravity can execute it as an ordered set of vertical slices: remove demo-student assumptions → real onboarding/profile persistence → structured mentor rendering → evidence-based reality check → visual system pass → remaining pages → polish. It does not propose new backend endpoints, new database tables, or a new tech stack. Where a recommendation would require a backend contract change, it is explicitly labeled **Backend change required**.

---

## 2. Product Diagnosis

### 2.1 What's actually working (Observed, from `implementation-status.md`)
- Next.js 14.2.5 App Router, TypeScript, Tailwind, shadcn-style primitives, Framer Motion, Radix — all in place.
- 11 pages build cleanly, lint is clean (0 warnings/errors as of the last audit date in the doc).
- Backend has 20 live student-facing endpoints plus 5 admin endpoints; 229+ backend tests passing at the point `implementation-status.md` was written, growing through later phases referenced (534 tests / 763 tests per later context).
- Real Pakistani data exists: verified universities, verified learning resources, curated/validated opportunities and sports records, template-labeled career data for the long tail.
- Mock mode (`NEXT_PUBLIC_USE_MOCK`) works and should keep working.
- Trust hierarchy for career reality data and candidate-constrained NBA selection are already implemented **in the backend**, not just planned.

### 2.2 What's broken, per the product owner's four stated problems

**Problem A — Demo student experience.** `implementation-status.md` confirms this precisely: *"Session management via localStorage (demo student ID=1)."* The journey page (Image 6) shows a specific stage ("Discover"), a specific NBA ("Learn JavaScript fundamentals"), and a specific pathway (10 named stages) that reads as pre-baked rather than personalized, because — per the docs — it currently *is* tied to a single fixed student record for every visitor.

**Problem B — Raw mentor output.** Not fully reproducible from the provided mentor screenshot (Image 9), which actually shows a clean, empty conversational shell. The product owner's description ("huge blocks of `###`, `**`, `---`, raw URLs") describes the *response-rendering* state, not the empty state shown. Treat this as **Observed via product-owner description, not via screenshot** — the failure mode is almost certainly that `CoachResponse.message` (a Markdown-formatted string returned by Qwen, per `coach_service.py`'s Pattern A generation) is being dropped into a plain text node instead of a semantic renderer. This is a **rendering-layer problem, not a backend problem** — `quick_actions[]` and `suggested_resource` already exist as separate structured fields in `CoachResponse` per `implementation-status.md §3`, which means the backend is *already* partially structuring output; the frontend likely isn't using those fields to their full potential and/or is rendering `message` as raw Markdown text.

**Problem C — Reality Check false precision.** Fully reproducible in Image 3. Four bars — Market Demand, Competition, Learning Difficulty, Pakistan Opportunity — are shown as colored horizontal meters (red/orange/green) that visually imply calculated percentages, but per `career_service.py`'s documented trust hierarchy, these are categorical labels (`demand_level`, `competition_level`, `difficulty_level` enums) sourced from the `careers` table — **not** computed scores. Rendering an enum value as a filled progress bar manufactures precision the data doesn't have. This is a pure **rendering/visual-design problem**: the data underneath is honest (it's a DB-sourced categorical field), the presentation is dishonest (it looks like a percentage).

**Problem D — "Vibe-coded" visual style.** Confirmed across all 9 screenshots: repeated white rounded cards with soft shadows, pill badges everywhere (HIGH DEMAND, MEDIUM DEMAND pills on every career card, category pills, status pills), a hero that uses a fairly generic dark-navy-gradient-with-glow treatment, and motivational percentage bars (Image 3's "Genuine Interest 80%, Salary Potential 60%...") that read as decorative rather than evidential.

### 2.3 Root cause summary
The backend already encodes restraint and honesty (trust hierarchy, candidate-constrained NBA, ungrounded-answer guard, freshness labeling). The frontend currently **does not visually communicate that restraint** — instead it borrows generic AI-product visual patterns (gradient hero, percentage bars, pill-everything) that work against the product's actual differentiator: it doesn't guess.

---

## 3. UX Principles

These principles govern every decision in this document. Where a section conflicts with a principle, the principle wins.

1. **Show evidence, not confidence.** A count ("12 verified programs") is always preferable to a rating ("Strong"). A rating is always preferable to a percentage. A percentage should almost never appear unless the backend genuinely computed it (e.g., `matching_service.py`'s `match_score = matched_required_skills / total_required_skills` — this is a real, code-computed ratio and *may* be shown as a percentage; `demand_level` is a DB enum and must **not**).
2. **One next action, always.** Every screen that can determine a next step shows exactly one primary action, not a menu of equally-weighted options. This mirrors the backend's own NBA design (`MAX_VISIBLE_STEPS = 3` progressive disclosure, one selected candidate).
3. **Personalization is structural, not cosmetic.** "Welcome, Anas" with a static page underneath is worse than no personalization at all — it's a trust violation once noticed. Personalization must change which data renders, not just which name renders.
4. **Progressive disclosure over density.** Career cards, opportunity cards, and reality-check cards should show the minimum useful surface, with a detail view for depth. Do not try to answer every question on the list view.
5. **Unknown is a valid, well-designed state.** Missing data (no deadline, no eligibility, no verdict yet) should look intentional, not like a bug or a placeholder.
6. **Restraint is the brand.** Every animation, gradient, pill, and badge must justify its presence. Default to removing, not adding.
7. **Pakistan-specific, not Pakistan-decorated.** Real city names, real institutions, real deadlines — not generic "your region" copy with a flag emoji.

---

## 4. Visual Direction

**Design recommendation.**

### 4.1 Recommended system: "Navy Editorial"
- **Primary (Deep Navy):** `#0B1220`–`#111C2E` range for hero/dark surfaces and primary text-on-light headings. Not pure black — navy signals "considered," black signals "generic dark mode."
- **Secondary (Indigo/Blue):** A single blue used for interactive elements, links, primary buttons, and the "you are here" journey marker — approximately the blue already visible in Image 1/5's step indicators. Keep to one blue hue across the whole product; the current screenshots already drift between a brighter button-blue and a deeper navy hero, which reads as two different design systems. Consolidate to one indigo scale (50→900).
- **Surfaces:** Off-white/cool-neutral (`#F7F8FA`–`#FFFFFF`) for all application content, not pure white — reduces the "template" flatness visible in Images 2, 7, 8.
- **Accent (restrained warm gold/orange):** Use for exactly one purpose across the whole product — **the single Next Best Action**. Nowhere else. Currently orange appears on demand pills, competition badges, verdict badges, and NBA cards simultaneously (Images 1–3), which dilutes it into decoration. Reclaiming it as an NBA-only signal makes it meaningful again.
- **Status color discipline:** Green = verified/positive evidence only. Red = should be reserved for genuine risk/warning language, not routinely used for "High Demand" (which is *good* news currently shown in a red pill in Image 2 — a red "High Demand" badge sends a subconscious warning signal for what should read as positive). Recolor demand/opportunity-positive states to blue or green; reserve red/orange strictly for competition and risk framing.

### 4.2 Aesthetic direction
**Dark premium hero + clean light application surfaces** (confirmed as the right call, per the product owner's own suggested direction and consistent with Image 1's existing hero). Keep the dark hero contained to the landing page and perhaps the mentor's empty state; every functional screen (careers, dashboard, journey, opportunities, sports) stays on light neutral surfaces for scannability and data density.

### 4.3 What to remove
- Colored left-accent progress bars used as fake metrics (Image 3's four demand/competition/difficulty/opportunity bars, and the "Genuine Interest / Salary Potential / Peer Influence / Family Expectations" percentage bars). See §13/§46.
- Redundant badge stacking — Image 2's career cards show a field pill AND a demand pill on every card; Image 7/8 stack a type pill and a status pill. Reduce to one badge per card unless the second genuinely adds decision-relevant information.
- The floating "Talk to AI Mentor" button's current styling competes visually with primary CTAs on every page (Images 1–9 all show it top-right in the same saturated blue as primary buttons). Recommend recoloring it to a lower-emphasis treatment (outline or navy-on-white) so it doesn't visually compete with the page's actual primary action.

---

## 5. Design System

**Design recommendation**, to be reconciled against actual existing Tailwind config/shadcn tokens (**Unknown — Antigravity must inspect** `Frontend/tailwind.config.ts` and `Frontend/app/globals.css` before applying).

| Token category | Recommendation |
|---|---|
| Typography | One serif-free system: a strong grotesk/sans for headings (already visible and working in the screenshots — keep it), one text sans for body. Avoid introducing a third display face. Type scale: 12/14/16/18/24/32/40/56 — the current hero (Image 1) reads as ~48–56px, keep that ceiling; don't go larger. |
| Spacing | 4px base unit, 8/12/16/24/32/48/64 scale. Current cards (Images 2, 7, 8) already use fairly consistent ~24px padding — retain, just apply it uniformly (some cards in Image 3/6 look tighter). |
| Radius | Reduce from the current large radius (~16–20px visible throughout) to a more restrained 8–12px on cards, 6–8px on buttons/inputs, and keep pills only where they are true status indicators (verified/unverified), not on every category label. Large radius everywhere is one of the strongest "template UI" signals in the current screenshots. |
| Surfaces | White cards on off-white page background (current pattern is close — keep, but reduce shadow intensity; several cards in Images 2/7/8 use a fairly heavy soft shadow that reads as "generic SaaS card") |
| Borders | Prefer a single 1px neutral border over shadow-only elevation for list/grid cards — cheaper visual weight, reads as more "data platform," less "marketing site." |
| Buttons | One primary style (solid indigo), one secondary (outline navy), one tertiary (text link with icon). Current screenshots already mostly follow this — the deviation is the floating mentor button competing with primary CTAs (§4.3). |
| Status/Badges | Reserve pill-shaped badges for **status only** (Verified, Unverified, Open, Closed, Deadline soon). Category labels (Technology, Business, Cricket) should be plain small-caps text labels, not pills — this alone removes a large share of the "too many pills" feedback. |
| Cards | Standardize card anatomy: eyebrow label → title → 1–2 line description → metadata row → single CTA. Every card type in this product (career, opportunity, sports, learning) should share this anatomy so the product feels like one system, not five. |
| Data visualization | Bars/gauges only for backend-computed ratios (match scores). Everything else (demand, competition, difficulty) renders as a labeled evidence chip with a short explanatory sentence, never a filled bar. See §13. |
| Source citations | A consistent, small "Source" component: organization name + external-link icon + "View source" — already close to what Images 7/8 show (`View Source ↗`); keep this pattern, reuse everywhere sourced data appears, including the mentor. |

---

## 6. Landing Page

### 6.1 Diagnosis of current hero (Image 1)
**Observed:** Strong headline, clear split CTA (Talk to AI Mentor / Reality-Check a Career), a 3-step process strip, and trust chips ("Pakistan-Specific Career Realities," "AI Guided by Your Personal Stage," "One Step at a Time"). This is a solid structural foundation — the redesign should **refine, not replace** the current hero concept.

### 6.2 Recommendations
**WHAT:** Keep the "Make a smarter career decision. Know what comes next." headline concept but tighten the CTA hierarchy: **one** primary CTA ("Start My Journey"), **one** secondary CTA ("Explore Careers"). Currently the hero offers "Talk to AI Mentor" as primary — that's the wrong default for a first-time, non-onboarded visitor, because the mentor without a profile has nothing personalized to say yet.
**WHY:** Per Problem A, a first-time visitor should not be steered into open-ended AI chat before they have a profile — the mentor is far more valuable *after* onboarding, when it has real context (per `coach_service.py`'s context-building from profile/roadmap/career/opportunities).
**HOW:** Swap primary/secondary CTA emphasis. "Start My Journey" → `/onboarding`. "Explore Careers" (secondary, outline style) → `/careers`, for the browsing-first visitor who isn't ready to commit to onboarding yet. Keep "Talk to AI Mentor" available but demote it to the floating button treatment already present, not a hero CTA.
**EXPECTED RESULT:** Every first-time visitor's default path leads to a persisted profile before they reach personalized surfaces — directly resolving Problem A at the entry point.

### 6.3 Section sequence (design recommendation, adopting §14 of the brief where each section is justified)
1. **Hero** — headline, one primary + one secondary CTA, 3-step process strip (keep, it's good), trust chips (keep, but verify none overstate — "AI Guided by Your Personal Stage" is fine only once personalization is real per §8).
2. **Why A&H Career** — three-column: Career Guidance / Real Pakistan Opportunities / Sports Pathways (matches the brief's required message).
3. **How it works** — Onboarding → Profile → Personalized dashboard → Mentor, shown as a compact 4-step visual, not prose.
4. **Career pathway preview** — 3 real career cards pulled live from `GET /careers`, using actual DB data, not decorative mockups.
5. **Sports pathway preview** — mirrors career pathway, 3 real sports opportunities from `GET /sports`.
6. **Trust / verified-source explanation** — plainly state what "verified" means in this product (see §19) — this is a genuine differentiator and currently underexplained.
7. **Final CTA** — repeat "Start My Journey," no new content.
8. **Footer** — keep current minimal footer (Observed in all screenshots, already appropriately restrained).

**Do not include:** a numeric stats section ("43 universities, 210 programs...") unless the product owner confirms these are safe to display publicly and are pulled live rather than hardcoded — hardcoding them recreates Problem A's static-content trust issue at the marketing layer. If shown, they must be fetched, not typed into JSX. Flag as **Backend change required** only if no existing endpoint returns aggregate counts — **Unknown — Antigravity must inspect** whether such an endpoint exists.

---

## 7. Onboarding

### 7.1 Diagnosis (Image 5)
**Observed:** Clean step-indicator pattern ("STEP 1 OF 6," 17% completed), large selectable option cards, single/multi-select radio-style treatment, Next Step CTA. This is already a strong, non-generic pattern — `implementation-status.md` confirms a real `OnboardingWizard (6 steps)` component with a `StepIndicator` exists. **This page needs the least visual rework of any screen.**

### 7.2 What must change
**WHAT:** Confirm (or fix) that submitting onboarding creates/updates a **real, uniquely identified student record** rather than overwriting demo student ID=1 for every visitor.
**WHY:** This is Problem A's actual mechanism. `POST /onboarding` already exists and returns `OnboardingResponse {profile_updated, next_best_action}` per `implementation-status.md §3` — the contract likely doesn't need to change, but the **session identity** created around it does.
**HOW:** See §8 for the concrete session-identity approach. On the onboarding UI itself: no visual change required beyond ensuring the final step transitions to a **freshly loaded** dashboard (a hard reload or explicit refetch after profile creation, not a client-side route push that reuses stale cached student state).
**EXPECTED RESULT:** Every visitor who completes onboarding sees a dashboard built from their own answers, not the last person's.

### 7.3 Content (per the brief's §16, mapped to what's likely already implemented)
Keep to 5–6 steps (matches "STEP 1 OF 6" already observed): Identity (name, city) → Education stage → Interests (subjects/careers) → Sports interest → Skills/strengths → Goals. This maps cleanly onto the existing `OnboardingPayload` fields (`education_stage, interests[], career_interests[], sports_interest, motivation_tags[], skills[], city`) confirmed in `implementation-status.md §3` — **no new fields need inventing**, the frontend should render the payload that already exists.

### 7.4 Visual polish (minor)
- Ensure back/next, keyboard navigation (arrow keys / enter), and progress preservation (if the visitor closes the tab mid-onboarding, resume rather than restart) — **Unknown — Antigravity must inspect** whether progress preservation currently exists.
- Consider a subtle completion-percentage color shift (e.g., progress bar brightens near completion) rather than new decorative elements.

---

## 8. Real Student / Profile Flow — P0

This is the highest-priority engineering item in this entire specification.

### 8.1 The problem, precisely
`implementation-status.md` states plainly: *"Session management via localStorage (demo student ID=1)"* and *"Session identity is demo student (ID=1) — no auth headers sent."* Every page that reads student state (`GET /journey`, career analysis context, coach chat context) is keyed to a single hardcoded ID for the whole application. `implementation-status.md §12` also notes *"Skip auth for MVP: Use demo-student session (architecture-approved); add JWT only if time permits"* — meaning this was a deliberate, documented Phase 1 decision, not an oversight. It has now become the top product blocker.

### 8.2 Recommended smallest-safe fix (per the brief's explicit instruction: no auth rewrite)
**WHAT:** Move from a single hardcoded student ID to a **per-browser generated student ID**, stored in `localStorage`, created at first onboarding submission — not a login system.
**WHY:** This preserves the existing "no auth" architecture decision (the brief explicitly forbids recommending a large auth rewrite) while fixing the actual symptom: every visitor currently shares state.
**HOW:**
1. `Frontend/lib/session.ts` (confirmed to exist, per `implementation-status.md`) currently hardcodes `id=1`. Change it to: on first visit with no stored session, do **not** assume a student exists. Gate all personalized routes (`/journey`, dashboard, career detail's personalized sections, mentor context) behind "has the visitor completed onboarding?"
2. On `POST /onboarding` success, persist the returned/created student identifier client-side (`localStorage`) and use it for all subsequent calls in that browser.
3. **Backend change required, likely minor:** confirm whether `POST /onboarding` can create a *new* student row (vs. always updating student ID=1) and whether it returns the student's ID in `OnboardingResponse`. If the current contract only supports a single demo student, this is the one true backend change needed to unblock Problem A — flag clearly to Antigravity as a scoped, minimal schema/service change (the `students` table already exists per the 9/17-table schema in `implementation-status.md §4`, so this is very likely an insert-new-row-instead-of-fixed-ID change in `onboarding_service.py`, not a new table).
4. Until that backend change lands, the frontend must **not silently pretend** multi-user support exists — see §8.3.

### 8.3 Interim state (if backend change isn't feasible immediately)
**Design recommendation:** If, per `implementation-status.md §12`'s "skip auth for MVP" decision, true per-visitor persistence is out of scope for the current milestone, the frontend must still stop the "static demo" *feeling* by:
- Never hardcoding a name, city, or specific stage into UI copy — always render whatever the current session's stored answers actually are.
- Making the loading/empty state after onboarding submission clearly reflect "your answers were just submitted" (a brief personalized confirmation, e.g., "Setting up your journey, [name]...") rather than jumping straight to what looks like a pre-existing dashboard.
- This is a **stopgap**, not a fix — §8.2's backend change remains the real solution and should be prioritized P0.

### 8.4 Real Student State conceptual flow (confirms brief §42)
```
New browser session
  → No stored student ID → route to onboarding (not dashboard)
  → Onboarding submitted → POST /onboarding → student created/updated
  → Student ID persisted client-side (localStorage)
  → Dashboard/Journey/Mentor all read using that ID
  → Returning visitor with stored ID → skip onboarding, go straight to dashboard
```
`localStorage` here stores an **identifier**, not the profile itself — the profile lives in SQLite via the existing `students`/`student_profiles` tables. This satisfies the brief's §42 instruction ("Do not make localStorage the sole source of truth for the student's profile").

---

## 9. Dashboard

**Observed:** No dedicated dashboard screenshot was provided (Images 1–9 cover home, careers, reality check, trial, onboarding, journey, opportunities, sports, mentor) — Image 6 ("Your Career Pathway") appears to function as the closest thing to a dashboard/journey hybrid. **Unknown — Antigravity must inspect** whether a separate `/dashboard` route exists distinct from `/journey`.

### 9.1 Recommended hierarchy (per brief §19, mapped to confirmed data)
1. Personalized greeting (first name from stored profile — never hardcoded)
2. Current journey stage (from `GET /journey`'s `stage` field — real enum, already exists)
3. **One** Next Best Action (from `next_best_action` — already candidate-constrained and DB-grounded per §2.1's trust-hierarchy note)
4. Recommended career direction (from `career_interests` resolved to verified slugs, per `onboarding_service.py`'s documented behavior)
5. Relevant real opportunities (2–3 cards, from `GET /opportunities` filtered by profile)
6. A learning recommendation (from `GET /learning`, confirmed to exist per Phase 13)
7. A sports option, only if `sports_interest` was set during onboarding — otherwise omit the section entirely rather than showing an empty/irrelevant sports card
8. Compact progress indicator (stage position, not a large timeline — save the full timeline for `/journey`)

**Design recommendation:** If `/journey` (Image 6) already serves this purpose end-to-end, do not build a duplicate dashboard route — extend `/journey` to be the single personalized home surface post-onboarding, and keep `/careers`, `/opportunities`, `/sports` as browsing/discovery surfaces. **Unknown — Antigravity must confirm actual route structure** before deciding whether to merge or keep separate.

---

## 10. Journey

### 10.1 Diagnosis (Image 6)
**Observed:** A 10-stage horizontal stepper (High School → Discover → Decide → University → Build Skills → Projects → Internship → Final Year → Job Prep → First Job), a prominent "Your Next Step" card, and a "Your Next 3 Steps" row. This closely matches the backend's real `EducationStage` enum (10 values, confirmed in `implementation-status.md §3`) and the `MAX_VISIBLE_STEPS = 3` roadmap design (confirmed in `roadmap_service.py`'s documented behavior). **This page's structure is already correct — it does not need conceptual redesign, only (a) real per-student state per §8, and (b) visual restraint.**

### 10.2 Visual recommendations
**WHAT:** Reduce the stepper's visual weight — currently every stage shows a numbered circle with a label, which at 10 stages creates a long horizontal scroll on mobile (Observed: the stage row in Image 6 already shows a cut-off 10th item, "First..."). 
**WHY:** A 10-item horizontal stepper is inherently a poor mobile pattern (§34 requires mobile-first treatment for exactly this component).
**HOW:** On mobile, collapse to: completed-stages count + current stage name + next stage name, with a tap-to-expand full stepper (bottom sheet or accordion), rather than horizontal scroll. On desktop, keep the current horizontal stepper but reduce label size and use color (not size) to differentiate completed/current/future.
**EXPECTED RESULT:** The journey reads as "you are here, this is next" at a glance on any device, with full detail available on demand.

### 10.3 "You are here" must be dynamic
Directly ties to §8 — the "YOU ARE HERE" badge and "Stage: Discover" label (Image 6) must render from the live `GET /journey` response for the current session's student, never a fixed value.

---

## 11. Career Exploration

### 11.1 Diagnosis (Image 2)
**Observed:** A clean, functional grid — search bar, field-filter chips, career cards with field label + demand pill + description + "Run Reality Check" CTA. This is close to correct; the main issue is redundant badge stacking (field pill + demand pill on every card, §4.3) and the description text being **identical boilerplate across every card** ("Explore verified realities, top Pakistani universities, and day-to-day requirements.") rather than career-specific.
**WHY this matters:** Identical description text across 15 distinct career cards is a strong "template/demo" signal — worse than no description.
**HOW:** Each career record in the `careers` table (per the confirmed schema) should have/need a short, career-specific one-line description. **Unknown — Antigravity must inspect** whether `CareerListItem` already carries a description field distinct from boilerplate, or whether this is frontend-hardcoded copy that should instead pull from the DB. If the field doesn't exist on `CareerListItem` (currently `{slug, name, field, demand_level}` per `implementation-status.md §3`), flag as **Backend change required**: add a short `summary`/`description` field to the list endpoint.

### 11.2 Card content (per brief §21)
Keep current fields (name, field, demand) but replace the pill-pill stacking with: one small-caps field label (not a pill) + one status-style demand badge (reserved styling, not the same visual weight as every other pill in the product) + career-specific description + CTA. Do not add arbitrary AI scores or decorative gauges (explicit brief requirement, §21).

---

## 12. Career Detail Page

**No screenshot provided for career detail as a standalone page** — Images 3/4 show Reality Check and Trial Plan, which are likely sub-routes of career detail (`/careers/[slug]/reality-check`, `/careers/[slug]/trial`, confirmed route names in `implementation-status.md §1`). **Unknown — Antigravity must inspect** `Frontend/app/careers/[slug]/page.tsx` for the base detail page's current state.

### 12.1 Recommended structure (per brief §22)
Overview → Skills → Programs → Learning → Opportunities → Reality Check (link out or inline summary) → Next Best Action. This should read as a table of contents / progressive disclosure page, with Reality Check remaining its own deep-dive route (since Image 3 shows it's already a rich, dedicated experience) rather than being flattened into the detail page.

---

## 13. Reality Check — P0, Most Important Redesign

### 13.1 The core problem, restated precisely
Image 3 shows four horizontal bars (Market Demand: High/red, Competition: High/red, Learning Difficulty: Medium/orange, Pakistan Opportunity: High/red) styled identically to a percentage-fill progress meter. Per the documented trust hierarchy in `career_service.py` (§2.1), these four fields are **categorical enum values pulled from the `careers` table** (`demand_level`, `competition_level`, `difficulty_level`, and an implied opportunity signal) — not computed scores. A filled bar is a percentage affordance; a three/four-value enum is not a percentage. This is the exact "false precision" the product owner flagged.

Separately, Image 3's "Motivation Reflection" section (Genuine Interest 80%, Salary Potential 60%, Peer Influence 40%, Family Expectations 20%) is AI-generated interpretive content (explicitly labeled "*AI reflection based on your answers*") rendered with the *same* bar-percentage visual language as the DB-sourced demand/competition data above it. This conflates two very different epistemic categories — real database facts vs. AI interpretation of onboarding answers — using identical visual weight. That conflation is arguably the single biggest trust problem on the page: a student cannot tell, by looking, which numbers are "real" and which are "AI's best guess."

### 13.2 Redesign principle
**Evidence, Interpretation, Student Fit, and Unknowns must be visually distinct card types, never share a bar-chart visual language.**

### 13.3 Recommended structure
**WHAT / HOW:**

**Section 1 — Pakistan Pathways Found (Evidence, DB-sourced counts).**
Replace the four colored bars with plain evidence chips using real counts wherever the backend has them: "12 verified programs · 6 relevant learning resources · 3 relevant opportunities." **Backend change required if these per-career counts aren't already returned** — `CareerReality` currently includes `required_skills[], pk_opportunities[], risks[], rewards[]` per `implementation-status.md §3`, so opportunity *count* may already be derivable client-side from `pk_opportunities.length`; programs/learning-resource counts are **Unknown — Antigravity must inspect** whether `Career`/`CareerReality` expose them, and if not, whether `GET /universities/{id}/programs` and `GET /learning` can be queried and counted client-side, or whether the career-analyze endpoint should be extended to include them directly (preferred, avoids N+1 fetching).

**Section 2 — Market Evidence (categorical, not numeric).**
Render `demand_level` and `competition_level` as a single labeled chip each ("Demand: High," "Competition: High") with a one-line plain-language explanation sentence underneath, sourced from the `rewards`/`risks` arrays already returned by the backend — not a bar.

**Section 3 — Learning Difficulty.**
Same chip treatment, no bar. Explicitly avoid inventing a numeric difficulty score if the backend only provides a category.

**Section 4 — Student Fit.**
This is the AI-authored verdict section (`CareerVerdict`: `verdict, headline, reasoning, student_strengths_match[], gaps_to_address[]`) — already well-structured data per the confirmed types. Image 3's existing "Your Strengths / Gaps to Address" two-column layout is **good and should be kept**, it's one of the better-designed sections already present. Just remove the percentage-bar "Motivation Reflection" section above it or redesign it per §13.4.

**Section 5 — Risks.**
Already exists as "Realities & Risks" (Image 3) — keep, it's honest, concise, appropriately labeled with warning icons rather than fake scores.

**Section 6 — Verdict.**
Keep the existing verdict badge concept (`GOOD FIT`/`WORTH EXPLORING`/`RECONSIDER` — matches the confirmed `CareerVerdict.verdict` enum exactly) but ensure the badge color logic maps 1:1 to those three enum values consistently everywhere the verdict appears (career cards, reality check, dashboard) — **Unknown — Antigravity must inspect** for consistency.

### 13.4 The "Motivation Reflection" section specifically
**WHAT:** Redesign from four percentage bars to either (a) a short AI-authored paragraph only (no bars) restating the reflection in prose, matching the existing "Reflection:" callout box already present below the bars in Image 3 (which is genuinely good and could stand alone), or (b) if the underlying data is a true ranked list (not a percentage), render as an ordered list of drivers ("Primarily driven by: genuine interest, then salary potential...") instead of a bar chart.
**WHY:** A percentage bar strongly implies a precise, comparable, out-of-100 measurement. "Motivation" derived from AI interpretation of a handful of onboarding answers cannot honestly support that precision.
**EXPECTED RESULT:** The page communicates "AI's interpretation" and "measured fact" as visually distinguishable categories throughout, resolving Problem C directly.

### 13.5 Contradiction handling (per brief §25)
Where demand is High and competition is also High, add a single connecting sentence (already partially present in Image 3's risks list — "Highly competitive degree admissions" — but not explicitly tied back to the demand figure). Recommended pattern: a short "What this means" line directly under the Market Evidence section, e.g., *"Strong employer demand exists, but entry-level competition is also high — build a portfolio before applying."* Only show this if it can be derived from the `rewards`/`risks` content already returned (do not fabricate new interpretive text not grounded in backend data).

---

## 14. Mentor UI — P0

### 14.1 Diagnosis
Image 9 shows a clean, appropriately restrained mentor shell — a welcome message, suggested-question chips, a text input. This screen, in its shown (empty) state, is actually well-designed and should not be substantially reworked structurally. The described problem (raw Markdown walls) manifests specifically in the **response state**, which is not shown in the screenshots.

### 14.2 Recommended response rendering architecture
**WHAT:** Parse `CoachResponse` into distinct visual regions rather than rendering `message` as a single Markdown blob.
**WHY:** `CoachResponse` already has structure: `{message, quick_actions[], suggested_resource}` (confirmed type, `implementation-status.md §3`). The backend has already done partial separation of concerns — `quick_actions` and `suggested_resource` are discrete fields, not embedded in the text. The frontend's job is to stop discarding that structure by dumping everything into one Markdown render.
**HOW:**
1. Render `message` through a proper Markdown renderer (e.g., a lightweight `react-markdown` with restrained custom component overrides) rather than displaying raw text with literal `#`/`*`/`-` characters — if the current bug is literally showing raw Markdown syntax unrendered, that alone is the most urgent fix.
2. Style the rendered Markdown to match the design system: headings become clear message section labels, not literal `###`; bold text becomes a subtle inline emphasis, not literal `**`.
3. Render `suggested_resource` as its own small resource card (title, source, link) below the message bubble — reusing the LearningResourceCard/OpportunityCard component pattern (§20).
4. Render `quick_actions[]` (max 3, per the documented backend validation) as tappable chips below the message, each of which sends that action's text back into the chat as the next user message — this pattern is already implied by the confirmed "SUGGESTED QUESTIONS" chip UI shown in Image 9's empty state; extend the same chip component to in-conversation quick actions.
5. If a mentor message references a specific opportunity, career, or source URL that the backend has structured data for, prefer rendering it as a compact card (title + source + link) rather than leaving it as inline Markdown link text — this is the **"What I found" / opportunity-card** pattern from the brief §27. **Backend change required if** the message text currently embeds raw opportunity data as prose with no structured accompanying field — **Unknown — Antigravity must inspect** whether `coach_service.py`'s context-building surfaces referenced opportunities/careers as separate structured data alongside `message`, or only as prose inside it. If only as prose, the safest fix without a backend contract change is simply the Markdown-rendering fix in step 1–2; true card-ification of "what I found" within a conversational answer is a **P1 stretch goal**, not a P0 blocker.

### 14.3 Visual chat structure
Compact right-aligned user bubbles (small, low visual weight, per brief §26) and left-aligned assistant messages that read as **structured guidance**, not chat-bubble text — i.e., the assistant "bubble" should be closer to a card than a speech bubble once it contains rendered Markdown + action chips + a resource card. Keep the initial system/welcome message as a simple bubble (Image 9's current treatment is fine for that specific message).

---

## 15. Beginner / Intermediate / Advanced UX

**Design recommendation**, no dedicated screenshot provided. This experience is most likely delivered through the mentor (coach chat) rather than a standalone page — **Unknown — Antigravity must inspect** whether a dedicated skill-level route exists.

**HOW:** If delivered via mentor response, apply the same structured-rendering approach from §14: "Your Level" as a small label, "Start With" as a numbered mini-list, "Recommended Resources" as resource cards (reusing `LearningResourceCard`), "What to Avoid" as a short callout, "Your Next Best Action" as the same NBA-styled component used on the dashboard/journey (§20) — reuse, don't rebuild a parallel component.

---

## 16. Opportunities

### 16.1 Diagnosis (Image 7)
**Observed:** Well-structured — an "AI-Powered Opportunity Match" panel (city + type inputs, one CTA) above a browsable grid with type/search filters. Cards show type pill, title, organization, location, deadline, skill tags, and "View Source." This page is already close to the target state described in brief §29.

### 16.2 Recommendations
- Reduce the type-pill + skill-tag-pill combination slightly (§4.3's pill discipline) but this page is otherwise the **least in need of rework** among the reviewed screens.
- Ensure unknown fields (no deadline, no eligibility) render as an explicit "Not specified" or are omitted entirely, never left visually blank or defaulted to a guess (per brief §29's explicit "Unknown data should remain unknown" instruction, and the backend's own documented freshness/`data_quality` fields).
- Surface `data_freshness: "unverified"` (confirmed field, `matching_service.py`) somewhere on the card when applicable — currently not visible in Image 7; this is real trust-relevant data the frontend isn't using. **Design recommendation, not currently shown:** small "Last verified [date]" or an "Unverified" tag distinct from the type pill, styled with clearly lower visual confidence (muted gray, not a colored pill).

---

## 17. Sports

### 17.1 Diagnosis (Image 8)
**Observed:** Mirrors the opportunities page structure closely (AI match panel + browsable grid), with sport-specific filter chips and eligibility details (age range, level) shown per card. This is a strong, already-functional pattern — sports doesn't read as a "separate mini-project" bolted on; it uses the same visual language as opportunities, which is correct per brief §30's goal.

### 17.2 Recommendations
Minor only: apply the same pill-reduction pass as §16.2, and ensure the age/level eligibility line (already shown, e.g., "Eligibility: age_min: 14, age_max: 22, level: intermediate") is rendered in natural language rather than raw field-name syntax — Image 8 currently shows literal `age_min:`/`age_max:` key names in the UI, which is a direct instance of exposing backend field names to students (explicitly warned against in brief §32 regarding provenance fields, and the same principle applies here). **HOW:** "Ages 14–22 · Intermediate level" instead of "age_min: 14, age_max: 22, level: intermediate."

---

## 18. Learning

No dedicated screenshot provided. **Unknown — Antigravity must inspect** current `/learning` implementation (confirmed to exist as an endpoint, `GET /learning`, per Phase 13). Apply the same card anatomy as Opportunities/Sports (§16/§17) for consistency: resource title, source organization, category/skill tags (sparingly), free/paid where known, CTA. Reuse the `LearningResourceCard` component already confirmed to exist in the component inventory if present — **Unknown — Antigravity must inspect** the actual component list against `implementation-status.md`'s named components (`CareerCard, CareerMetricBar, CareerVerdict, MotivationBar,` etc. — no `LearningResourceCard` is explicitly named in the audit, so this may need to be built fresh, following the shared card anatomy in §5).

---

## 19. Source / Citation UX

**Design recommendation.** The current "View Source ↗" link pattern (Images 7, 8) is good and should become the canonical citation component, reused in the mentor (§14) and reality check (§13). Do not expose raw provenance/internal fields (e.g., `data_source`, `data_quality` string values like `"unranked"`) directly — translate them into short human labels:
- `data_quality: "ranked"` / AI-matched → no special label needed (default state)
- `data_quality: "unranked"` (documented MCP-fallback state) → "Basic match" or similar honest, non-alarming label, not hidden and not exposed as raw enum text
- `data_freshness: "unverified"` → "Unverified" muted tag (§16.2)
- Verified DB records (universities, learning resources) → a small "Verified source" tag is appropriate here specifically because `implementation-status.md` confirms these particular datasets are genuinely manually verified (VERIFIED mode D) — do not apply "Verified" to TEMPLATE-labeled data (careers, some opportunities/sports seeds), since the backend itself distinguishes TEMPLATE vs VALIDATED vs VERIFIED data provenance. **Engineering requirement:** the frontend needs to know which provenance tier a given record belongs to — **Unknown — Antigravity must inspect** whether this tier is exposed in current API responses; if not, flag as **Backend change required** (likely small — expose an existing internal provenance/seed-label field that already exists in the data model per `implementation-status.md §4`'s described TEMPLATE/VALIDATED/VERIFIED labeling).

---

## 20. Navigation

**Design recommendation**, informed by confirmed routes (`implementation-status.md §1/§3`): Home, Careers, Opportunities, Sports, Journey, Mentor, and — if it exists as a separate route — Job Readiness (`Frontend/app/job-readiness/page.tsx`, confirmed to exist per Phase 8). Learning does not appear to have its own nav-level page per the confirmed component/page inventory; **Unknown — Antigravity must inspect** whether it's a standalone page or embedded within career detail / dashboard.

Recommended nav order (goal-first, not feature-count-first, per brief §33): **Dashboard/Journey · Careers · Opportunities · Sports · Mentor**, with Job Readiness reachable from the dashboard/journey rather than top-level nav if it's a secondary/deeper feature — **Unknown — Antigravity must confirm** its actual product prominence before demoting it.

---

## 21. Responsive Design

Mobile-first priority order (per brief §34), based on where the current screenshots (many captured at what appears to be a narrow/mobile-ish viewport already) show the most strain:
1. **Journey stepper** (§10.2) — the clearest current mobile problem (10-item horizontal stepper, visibly cut off in Image 6).
2. **Onboarding** — already close to correct (Image 5 reads well at narrow width).
3. **Mentor** — ensure the quick-action chips and suggested-resource cards (§14) don't overflow narrow viewports; test chip wrapping.
4. **Reality Check** — the new evidence-chip layout (§13) must stack cleanly in a single column on mobile; avoid the current four-bar grid's 2×2 layout forcing tiny text at narrow widths.
5. **Career/Opportunity/Sports cards** — already reasonably responsive per the screenshots (single-column stacking visible); maintain.

---

## 22. Accessibility

**Engineering requirement**, per brief §38:
- Semantic HTML: real `<nav>`, `<main>`, `<button>` (not `<div onClick>`) — **Unknown — Antigravity must audit** actual current markup.
- Keyboard navigation for onboarding option cards (already visually styled as radio-like — confirm they're real `<input type="radio">`/`<input type="checkbox">` under the hood, not divs, per Image 5).
- Focus states: visible focus ring on all interactive elements, including the selectable onboarding cards, filter chips, and career cards.
- Contrast: verify the red-on-light-red "HIGH Demand" pills (Image 2/3) meet WCAG AA — several pill treatments across the screenshots use fairly light background tints with saturated text, worth an explicit contrast check once §4's badge redesign lands anyway.
- Reduced motion: respect `prefers-reduced-motion` for all Framer Motion transitions (hero entrance, card reveal, mentor response reveal).
- Form errors: onboarding validation errors must be announced (aria-live) and visually adjacent to the relevant field, not a generic top-of-page banner.
- Screen reader support: the journey stepper (§10) needs an accessible name per stage ("Stage 2 of 10: Discover, current stage") since it's currently a purely visual circle-and-line pattern.

---

## 23. Motion

Per brief §39, current usage (hero entrance, presumably page transitions per the confirmed `PageTransition` component) should stay. Add: onboarding step transitions (slide/fade between steps), journey progress transitions (when a stage completes), mentor response reveal (message + chips + resource card animating in as a sequence, not all at once — reinforces the "structured, not a wall of text" redesign in §14). Explicitly avoid: floating/bouncing decorative elements, particle effects, glow pulses on buttons — none of these are currently visible in the screenshots, so this is a preventive guideline for new work, not a removal task.

---

## 24. Loading / Empty / Error States

**Design recommendation**, no dedicated screenshots provided, though `implementation-status.md` confirms shared `Empty, Error, Loading` state components already exist. Audit and standardize rather than rebuild:
- **Loading:** skeleton shapes matching each card type's real layout (career card skeleton ≠ opportunity card skeleton), not a generic spinner — for mentor responses specifically, a "thinking" skeleton that hints at the structured sections about to appear (message line, then chip row, then resource card) reinforces §14's redesign.
- **Empty:** "No verified opportunities match you right now" + one relevant next action (e.g., "Broaden your city filter" or "Talk to your mentor about alternatives") — never fabricate placeholder results (explicit brief requirement, §36).
- **Error:** student-friendly language, preserve user input (especially in onboarding and mentor input), offer retry, never show raw backend error text/stack traces (explicit brief requirement, §37) — this is doubly important given the documented `503`/`500` AI-failure error codes in the backend's error contract; a raw "503 Service Unavailable" must never reach the student.

---

## 25. API / Backend Safety

**Engineering requirement — hard constraint.** Per the brief and confirmed by `implementation-status.md`, the following must be preserved exactly as-is: FastAPI structure, PKE/MCP retrieval layer, the two mounted MCP SSE servers, Qwen four-model fallback chain, SQLite schema, the documented trust hierarchy in `career_service.py`, the candidate-constrained NBA engine, and the ungrounded-answer guard in `mcp_search_service.py`. 

**No new endpoint contracts should be invented by this spec.** Every place above where this document says "Backend change required," it refers to a **small, additive** change to an existing endpoint/service (e.g., returning a student ID from onboarding, adding a per-career program/resource count, exposing a provenance tier field) — never a new subsystem, new table category, or architectural change. Antigravity should verify actual current response shapes against `implementation-status.md §3`'s documented types before implementing any frontend change that assumes a field exists.

---

## 26. Mock Mode

`NEXT_PUBLIC_USE_MOCK=true` (confirmed env var) must continue to function per brief §43. Since real backend integration is confirmed complete (`NEXT_PUBLIC_USE_MOCK=false` is the current default per `implementation-status.md §3`), treat mock mode as a **development/demo-offline fallback**, not the primary path — but any UI/type change made in this spec must be mirrored in the mock data fixtures so mock mode doesn't silently drift out of sync with the real contract (a real risk once, e.g., §13's reality-check restructuring or §8's session-identity change land).

---

## 27. Component Architecture

Per brief §40's explicit instruction: **do not duplicate what exists.** `implementation-status.md` confirms a substantial existing component library: `NavBar, Footer, PageTransition, CareerCard, CareerMetricBar, CareerVerdict, MotivationBar, RealityCheckPanel, TrialPlanView, JourneyTimeline, NextStepCard, RoadmapSteps, CoachChat, ChatMessage, QuickActions, TypingIndicator, OnboardingWizard, StepIndicator`, shared `Empty/Error/Loading` states, `ProgressBar, SectionHeader`, plus shadcn primitives (`badge, button, card, input, progress, separator, skeleton`).

Mapping this spec's recommendations onto that inventory:
- **`CareerMetricBar` and `MotivationBar`** are very likely the exact components producing Problem C's false-precision bars (§13). **Recommendation: do not delete** — repurpose/redesign these specific components' internals to render evidence chips instead of filled bars, since every other page that references them (career cards, reality check) inherits the fix automatically. This is lower-risk than introducing new parallel components.
- **`QuickActions`** already exists — likely the component to extend for in-conversation mentor quick-action chips (§14.2), reusing rather than building new.
- **`ChatMessage`** already exists — extend to support rendering Markdown + nested resource cards rather than building a new message component.
- **New components likely needed** (not found in the confirmed inventory): `OpportunityCard`, `SportsPathwayCard`, `LearningResourceCard`, `EvidenceChip`/`RealitySignal`, `SourceCitation` (a standalone, reusable version distinct from inline "View Source" links scattered per-page). **Unknown — Antigravity must inspect** actual `Frontend/components/` before creating any of these — some may already exist under different names (e.g., an opportunity card may already exist given `/opportunities` and `/sports` pages are confirmed built in Phase 7).

---

## 28. Vibe-Code Audit

| # | Problem (Observed) | Professional alternative |
|---|---|---|
| 1 | Every career/opportunity/sports card stacks 2 pills (field + status) | One plain text category label + one reserved status badge (§5, §11.2) |
| 2 | Demand/competition/difficulty rendered as filled percentage bars from categorical DB enums (Image 3) | Evidence chips + plain-language sentence, no bar (§13) |
| 3 | "Motivation Reflection" AI interpretation rendered with the same bar visual as real DB facts (Image 3) | Distinct visual treatment for AI-interpretation vs. DB-fact (§13.4) |
| 4 | Identical boilerplate description text across all 15 career cards (Image 2) | Career-specific one-line description sourced from DB (§11.1) |
| 5 | Raw field-name syntax exposed in UI ("age_min: 14, age_max: 22") (Image 8) | Natural-language rendering of eligibility (§17.2) |
| 6 | Large, uniform border-radius on every surface — a strong generic-template signal | Reduced, more restrained radius scale (§5) |
| 7 | Session tied to a single hardcoded demo student for every visitor | Per-visitor session identity (§8) |
| 8 | Floating mentor CTA visually competes with each page's actual primary CTA (same saturated blue, same weight, present on every screenshot) | Demoted, lower-emphasis floating button styling (§4.3) |
| 9 | Orange/gold accent used simultaneously for demand pills, verdict badges, and NBA — no longer a meaningful signal | Reserve accent color for NBA only (§4.1) |
| 10 | "High Demand" (good news) shown in a red pill — red typically signals warning | Recolor positive-demand states away from red (§4.1) |
| 11 | Mentor responses reportedly render literal Markdown syntax (`###`, `**`) as plain text (per product-owner description) | Proper Markdown rendering + structured section components (§14) |

---

## 29. Product Copy

**Design recommendation.** Current copy tone (Observed across screenshots) is already largely on-brand: direct, non-hyperbolic ("An honest analysis comparing demand, difficulty, and your personal motivation in Pakistan," "You don't need to figure out your entire 5-year career right now. Just complete your single immediate action.") — this voice should be preserved and extended, not replaced. Two specific corrections:
- Remove any implied precision in copy that pairs with §13's bar removal — e.g., avoid phrases like "Top 5%" anywhere in the product (explicitly forbidden by the brief and not currently observed in the screenshots, but worth a copy audit given the false-precision pattern elsewhere).
- Ensure onboarding/dashboard copy never says something that was true for demo student ID=1 specifically but reads as universal (a risk while §8's fix is in progress).

---

## 30. File / Implementation Guidance

**Antigravity must verify all paths below before editing — these are informed inferences from `implementation-status.md`, not confirmed current file contents.**

| Area | Likely file(s) to inspect | Expected change | Why | Integration risk |
|---|---|---|---|---|
| Session identity | `Frontend/lib/session.ts` | Replace hardcoded `id=1` with stored-per-browser ID, gated on onboarding completion | Resolves Problem A (§8) | **High** — touches every page that reads student state; test all 11 pages after change |
| Onboarding submission | `Frontend/hooks/useOnboarding`, onboarding page/route | Persist returned student ID after `POST /onboarding` | Enables §8's flow | Medium |
| Reality check bars | `CareerMetricBar`, `MotivationBar` components, `RealityCheckPanel` | Redesign internals from bar-fill to evidence-chip rendering | Resolves Problem C (§13) | Medium — likely reused across career cards + reality check, verify all call sites |
| Mentor rendering | `ChatMessage`, `CoachChat`, `QuickActions` components | Add Markdown rendering + resource-card + quick-action extension | Resolves Problem B (§14) | Medium |
| Career card copy | `CareerCard` component, career list data source | Swap boilerplate description for DB-sourced summary | Resolves §11.1 | Low, contingent on confirming/adding the field |
| Journey stepper | `JourneyTimeline`, `RoadmapSteps` components | Add mobile collapsed/expandable variant | Resolves §10.2 | Low–Medium |
| Sports/opportunity eligibility text | opportunity/sports card components | Natural-language eligibility formatting | Resolves §17.2 | Low |
| Design tokens | `Frontend/tailwind.config.ts`, `globals.css` | Consolidate color scale, reduce radius scale, badge/pill discipline | Resolves §4/§5/§28 | Medium — touches every page visually, needs full visual regression pass |
| Provenance/trust labels | wherever `data_source`/`data_quality`/`data_freshness` are currently (not) surfaced | Add human-readable labels per §19 | Trust differentiation | Low–Medium, contingent on field availability |

---

## 31. QA Matrix

| Flow | Must verify |
|---|---|
| First-time visit | No demo-student data visible anywhere before onboarding is completed |
| Onboarding → Dashboard | Dashboard reflects the exact answers just submitted (spot-check city, interest, sports toggle) |
| Two separate browser sessions | Each shows independently different personalized state (post-§8 fix) |
| Reality Check | No bar/percentage visual for any enum-sourced field; AI-interpretation content visually distinct from DB facts |
| Mentor | A multi-part response renders as distinct sections/cards, not a single Markdown-syntax-visible block |
| Opportunities/Sports | Unknown fields (deadline, eligibility) never silently guessed or left blank without an explicit "not specified" |
| Mobile | Journey stepper, onboarding, mentor chip row, reality-check evidence cards all usable at ~375px width |
| Mock mode | `NEXT_PUBLIC_USE_MOCK=true` still renders every page without errors after all component changes |
| Accessibility | Keyboard-only completion of onboarding; screen-reader pass on journey stepper and reality-check verdict |

---

## 32. Acceptance Criteria

Restating the brief's §53 against this spec's proposed changes — each is met specifically by:
- **First visit / Onboarding / Profile / Dashboard:** §8 (session identity), §7 (onboarding), §9 (dashboard hierarchy)
- **Career / Reality Check:** §11, §13
- **Mentor / Beginner-Intermediate-Advanced:** §14, §15
- **Sports / Opportunities / Sources:** §16, §17, §19
- **Journey / NBA:** §10, backend's existing candidate-constrained NBA (unchanged, per §25)
- **Mobile / Design:** §21, §4–§5, §28
- **Backend / Mock:** §25, §26 (explicitly unchanged)

---

## 33. Implementation Priority

**P0 — Critical (do first, blocks everything else feeling real)**
1. Real per-visitor session identity (§8) — the single highest-leverage fix in this document.
2. Onboarding → profile persistence confirmation (§7.2, dependent on §8).
3. Mentor structured rendering fix (§14) — likely a contained, low-risk fix (Markdown renderer + reuse of existing `quick_actions`/`suggested_resource` fields).
4. Reality Check evidence-vs-bar redesign (§13).
5. Backend/frontend contract safety pass (§25, §30) — confirm every type this spec assumes still matches reality before broad rollout.

**P1 — High**
6. Landing page CTA/section pass (§6).
7. Dashboard/Journey consolidation and mobile stepper (§9, §10).
8. Career detail structure confirmation (§12).
9. Opportunities/Sports natural-language eligibility + trust labels (§16, §17, §19).
10. Learning page audit/build (§18).
11. Responsive pass across all P0 surfaces (§21).

**P2 — Polish**
12. Design token consolidation (badge/pill/radius/color discipline) (§4, §5, §28).
13. Motion refinement (§23).
14. Accessibility hardening (§22).
15. Loading/empty/error state standardization (§24).
16. Product copy audit (§29).

---

## 34. Risks / Unknowns

Explicitly flagged throughout; consolidated here for Antigravity's pre-work checklist:
- Whether `POST /onboarding` can create a genuinely new student record vs. only updating a fixed ID (§8.2) — **the single most important thing to verify before starting.**
- Whether `CareerListItem`/`CareerReality` expose per-career program/resource counts, or whether the reality-check evidence section (§13.3) needs a backend addition.
- Whether a dedicated `/dashboard` route exists separate from `/journey` (§9).
- Whether `coach_service.py`'s context-building surfaces structured "what I found" data alongside `message`, or only prose (§14.2, step 5).
- Whether provenance tier (TEMPLATE/VALIDATED/VERIFIED) is exposed in any current API response for source-trust labeling (§19).
- Actual current Tailwind config / token setup (§5) — this spec proposes a token direction, not a literal file diff.
- Actual current component file names/locations (§27, §30) — every mapping here is inference from `implementation-status.md`'s named component list, not a repository read.
- Whether onboarding progress is currently preserved across a closed tab (§7.4).

None of these unknowns should block starting P0 item 1 (§8) — that fix's frontend half (gating routes on a stored session, not assuming demo student ID=1) can proceed immediately; only the "can onboarding create a new student row" half needs backend inspection first.

---

## FINAL RECOMMENDATION

**Biggest UX problems:** (1) the product is more trustworthy on the backend than it appears on the frontend — the trust hierarchy, candidate-constrained NBA, and ungrounded-answer guard are real engineering work currently invisible to students; (2) false precision on the Reality Check page actively undermines the product's core differentiator (honesty about uncertainty); (3) a hardcoded demo-student session makes every personalization claim in the UI feel — and currently is — untrue for real visitors.

**Biggest engineering risks:** the session-identity fix (§8) is the one change in this spec that touches nearly every page and may require a small, scoped backend change to `onboarding_service.py`; everything else in this document is additive/cosmetic and lower-risk. The mentor rendering fix (§14) is likely smaller than it looks — the backend has already done the hard work of structuring `CoachResponse`; the frontend fix is largely "stop throwing that structure away."

**Top implementation priorities:** real session identity → mentor rendering → reality check honesty → design system consolidation → remaining page polish, in that order (§33).

**What must not be changed:** FastAPI/PKE/MCP architecture, the Qwen fallback chain, the SQLite schema, the trust hierarchy already enforced in `career_service.py`, the candidate-constrained NBA engine, mock mode, and the existing endpoint contracts (§25) — this is a frontend trust-and-polish pass, not a rebuild.

**What should be dramatically improved:** the Reality Check page's visual honesty (§13), the mentor's response structure (§14), and the elimination of the single-demo-student assumption (§8) — these three changes alone resolve all four of the product owner's stated problems and should be treated as one connected release, not three separate ones, since they share the same underlying fix pattern: **stop decorating uncertain or shared state as if it were precise and personal, and start rendering exactly what the backend actually knows.**

**Recommended implementation order:** §8 → §14 → §13 → §5/§4 (design tokens) → §6/§9/§10 (landing/dashboard/journey) → §11/§12 (careers) → §16/§17/§18 (opportunities/sports/learning) → §19 (trust UX, layered on top of everything above) → §21–§24 (responsive/accessibility/motion/states polish pass across the whole product).

**Final assessment:** A&H Career does not need a redesign in the sense of new features or a new architecture — it needs its frontend to catch up to the honesty already built into its backend. This is a comparatively low-risk, high-clarity project: every P0 item has a scoped, identifiable fix, none require touching PKE/MCP/Qwen, and the component inventory already confirmed to exist (`RealityCheckPanel`, `CareerMetricBar`, `ChatMessage`, `QuickActions`, `OnboardingWizard`) suggests most of this work is repurposing existing components rather than building new ones. The redesign strategy in this document is achievable without breaking anything the product owner explicitly protected.
