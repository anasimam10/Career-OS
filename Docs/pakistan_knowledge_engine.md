# Pakistan Knowledge Engine — Research & Data Architecture
### A&H Career — Karachi · Lahore · Islamabad MVP
**Status:** Extension design for the existing A&H Career system (Next.js + FastAPI + SQLAlchemy/SQLite + Pydantic + Qwen/DashScope + FastMCP). Does not replace or redesign the existing application.
**Prepared:** September 2026

---

## 1. Executive Summary

The Pakistan Knowledge Engine (PKE) is a data ingestion and provenance layer that feeds trustworthy, Pakistan-specific, city-scoped facts into the existing A&H Career backend. It does **not** change the existing app; it adds a source registry, a staging/verification pipeline, and twelve domain schemas that plug into the current database, MCP layer, and Qwen mentor via the existing opportunity-visibility gates.

Core design principles carried through this whole document:

1. **Real sources only.** Every source below was located and checked during this research pass; URLs are cited. Nothing is invented. Nationwide-only sources (HEC, NAVTTC, DigiSkills, PCB, PFF) are explicitly flagged as nationwide, not city-specific.
2. **Three cities only.** Karachi, Lahore, Islamabad. No silent expansion to Rawalpindi, Faisalabad, Peshawar, etc. — those only appear if a source is genuinely nationwide/online and labeled as such.
3. **Qwen extracts, never asserts.** Qwen classifies, normalizes and summarizes candidate records; deterministic Pydantic validation and human/verification gates decide what becomes a "VERIFIED" fact.
4. **Static vs dynamic.** Schools/colleges/universities/programs/careers are slow-moving and get long freshness windows; jobs/internships/scholarships/tournaments/trials are dynamic and get short windows, with provenance mandatory on every live record.
5. **No unauthorized access.** No CAPTCHA bypass, no scraping of platforms whose Terms of Service prohibit it (LinkedIn Jobs, most large job boards). Those sources are marked "discovery-only" or "manual import," not "automated."

---

## 2. Scope

**In scope (MVP):**
- Cities: Karachi, Lahore, Islamabad only.
- 12 domains: Schools, Colleges, Universities, Programs, Scholarships, Internships, Jobs, Sports, Tournaments, Trials, Learning Resources, Careers.
- Source discovery, authority classification, schema design, provenance model, verification states, freshness rules, ingestion architecture, and handoff instructions for Antigravity, ChatGPT, and Qwen.

**Out of scope (MVP):**
- Any other Pakistani city as a standalone target.
- Scraping any platform whose terms disallow it.
- Automatic promotion of unverified data to student-facing endpoints.
- Rebuilding the existing Next.js/FastAPI/Qwen application.

---

## 3. Three-City Strategy

Karachi, Lahore, and Islamabad are treated as **first-class, independently seeded city contexts**, not a single "Pakistan" blob:

- Each city has its own school/college regulatory body (Sindh — BIEK/BSEK/School Education & Literacy Department; Punjab — School Education Department/Higher Education Department/PHEC; Islamabad — FDE/FBISE), so schools/colleges ingestion is run **per city, per authority**, not as one national scrape.
- Universities are filtered to campuses physically located in, or with a named campus in, one of the three cities, cross-checked against the HEC recognised list.
- Jobs/internships/sports are filtered by explicit city field at the platform/listing level (Rozee, PCB, PFF, company career pages all expose city).
- Nationwide-only entities (HEC, NAVTTC, DigiSkills, PCB, PFF, Ignite) are stored once as `city_scope: NATIONWIDE`, and are linked to, rather than duplicated into, each city.

---

## 4. 12-Domain Architecture (Overview)

| # | Domain | Static/Dynamic | Primary authority tier |
|---|--------|-----------------|------------------------|
| 1 | Schools | Static | L1 (provincial education depts) / L2 (aggregators, discovery only) |
| 2 | Colleges | Static | L1 (education boards, HED) |
| 3 | Universities | Static | L1 (HEC, official university sites) |
| 4 | Programs | Static | L1 (official program/admissions pages) |
| 5 | Scholarships | Dynamic (deadlines) | L1 (HEC, university financial aid offices) |
| 6 | Internships | Dynamic | L1 (company career pages) / L2 (Rozee, BrightSpyre) |
| 7 | Jobs | Highly dynamic | L1 (company career pages) / L2 (Rozee, Mustakbil, BrightSpyre) |
| 8 | Sports | Hybrid | L1 (federations, university sports depts) |
| 9 | Tournaments | Very dynamic | L1 (federations, organizers) |
| 10 | Trials | Very dynamic | L1 (federations, academies, university teams) |
| 11 | Learning Resources | Hybrid | L1 (HEC/NAVTTC/DigiSkills/universities) |
| 12 | Careers | Static | Curated reference; existing DB is the base |

---

## 5. Source Authority Hierarchy

**LEVEL 1 — PRIMARY/OFFICIAL** — government bodies, HEC, official university/school-board sites, official employer career pages, official federations/tournament organizers, official scholarship providers. Usable directly for authoritative fields, subject to normal validation.

**LEVEL 2 — TRUSTED SECONDARY** — established platforms (Rozee, Mustakbil, BrightSpyre, Indeed Pakistan). Usable **only** with preserved provenance (source URL + fetched_at) and, for opportunity records, additional verification before student-facing exposure.

**LEVEL 3 — COMMUNITY/SOCIAL** — official Instagram/Facebook/LinkedIn/X accounts of L1 organizations. Discovery/supporting evidence; a post is a *lead*, not a record, until cross-checked against an L1 page or explicitly verified by a human reviewer.

**LEVEL 4 — DISCOVERY ONLY** — aggregator blogs, "top scholarships 2026" listicles, unverified forum posts. Never create production records directly; used only to discover candidate L1/L2 URLs for a human/Qwen pass to verify.

---

## 6. Full Source Inventory (Verified This Session)

All URLs below were located and read during this research session. "Verified" = the page was found to exist and be topically relevant at time of writing; it does not guarantee the page will remain unchanged, hence the mandatory `last_verified` field on every record.

### 6.1 Government / Cross-Domain Authorities

| source_id | Organization | URL | Domain(s) | City scope | Level | Access method | Automation OK? | Notes |
|---|---|---|---|---|---|---|---|---|
| GOV-HEC-01 | Higher Education Commission | https://www.hec.gov.pk | Universities, Programs, Scholarships | Nationwide | L1 | Public pages | Manual/semi-auto (page structure varies) | Central authority for university recognition and national/international scholarships |
| GOV-HEC-02 | HEC Recognised Universities list | https://www.hec.gov.pk/english/universities/pages/recognised.aspx | Universities | Nationwide | L1 | Public HTML table | Yes, page fetch + parse | Use as the ground-truth recognition check for every university record |
| GOV-HEC-03 | HEC Scholarships Portal | https://scholarship.hec.gov.pk (linked from hec.gov.pk) and https://www.hec.gov.pk/english/scholarshipsgrants/pages/default.aspx | Scholarships | Nationwide | L1 | Public pages + login portal for applicants | Listing page: yes. Application portal: no (requires user login) | Portal lists open national/international scholarships; deadlines change frequently |
| GOV-FDE-01 | Federal Directorate of Education (Islamabad) | https://fde.gov.pk | Schools, Colleges | Islamabad | L1 | Public pages ("Our Institutions" list) | Yes | Lists ~430 FDE schools/colleges in ICT with names, sectors, contacts |
| GOV-FBISE-01 | Federal Board of Intermediate & Secondary Education | https://fbise.edu.pk | Schools, Colleges | Islamabad (+ Cantt/Garrison, GB) | L1 | Public pages | Manual verify, then automate | Examination board for FDE/FGEI-affiliated institutions |
| GOV-FGEI-01 | Federal Government Educational Institutions (Cantonments/Garrisons) | https://www.fgei.gov.pk | Schools, Colleges | Islamabad + Cantt areas | L1 | Public pages | Manual/semi-auto | Covers cantonment schools; filter to Islamabad-area entries only |
| GOV-SINDH-EDU-01 | Sindh School Education & Literacy Department | https://www.sindheducation.gov.pk | Schools | Karachi | L1 | Public pages, some PDFs | Manual/semi-auto | Oversees BIEK, BSEK, and Karachi-region directorate |
| GOV-SINDH-DSE-01 | Directorate of Schools Education (Karachi Region) | http://www.dsekhisindh.gov.pk | Schools | Karachi | L1 | Public pages | Manual/semi-auto | Karachi-region school administration |
| GOV-BIEK-01 | Board of Intermediate Education, Karachi | https://biek.edu.pk | Colleges | Karachi | L1 | Public pages | Manual/semi-auto | Intermediate (college-level) examination board, affiliates ~354 colleges |
| GOV-BSEK-01 | Board of Secondary Education, Karachi | https://bsek.edu.pk | Schools | Karachi | L1 | Public pages | Manual/semi-auto | Secondary (school-level) examination board |
| GOV-PUNJAB-SED-01 | Punjab School Education Department | https://schools.punjab.gov.pk | Schools | Lahore | L1 | Public pages | Manual/semi-auto | Provincial policy body; school information system referenced on-site |
| GOV-PUNJAB-HED-01 | Punjab Higher Education Department | https://hed.punjab.gov.pk | Colleges | Lahore | L1 | Public pages | Manual/semi-auto | Oversees government/degree colleges in Punjab, including Lahore |
| GOV-PHEC-01 | Punjab Higher Education Commission | https://punjabhec.gov.pk | Universities, Colleges | Lahore | L1 | Public pages | Manual/semi-auto | Provincial HEI quality/recognition body, complements federal HEC |
| GOV-PEIRA-01 | Private Educational Institutions Regulatory Authority (Islamabad) | linked from mofept.gov.pk | Schools | Islamabad | L1 | Public pages | Manual | Regulates private schools in ICT; useful for private-school registry cross-check |
| GOV-NAVTTC-01 | National Vocational & Technical Training Commission | (official site; verify current domain each cycle) | Learning Resources | Nationwide | L1 | Public pages | Manual/semi-auto | Vocational/technical training; has city-level partner institutes including Karachi/Lahore/Islamabad |
| GOV-DIGISKILLS-01 | DigiSkills.pk (Ministry of IT & Telecom / Ignite / Virtual University) | https://digiskills.pk / https://www.digiskills.pk | Learning Resources | Nationwide (online) | L1 | Public pages, registration portal | Course catalog: yes. Registration/enrollment: no (user action) | Free, government-backed online skills training; label as NATIONWIDE/ONLINE |
| GOV-IGNITE-01 | Ignite National Technology Fund | (official site) | Learning Resources, Scholarships | Nationwide | L1 | Public pages | Manual | Co-funds DigiSkills and other national tech programs |

### 6.2 Universities (High Priority — Karachi / Lahore / Islamabad)

Use `GOV-HEC-02` as the master recognition check. Below are official institutional sources to seed programs/admissions data; each must be re-verified and expanded during ingestion (this list is a seed set, not exhaustive).

| source_id | University | City | Official site | Level | Notes |
|---|---|---|---|---|---|
| UNI-KHI-01 | University of Karachi | Karachi | uok.edu.pk | L1 | Largest public university in Karachi |
| UNI-KHI-02 | NED University of Engineering & Technology | Karachi | neduet.edu.pk | L1 | Public engineering university |
| UNI-KHI-03 | Aga Khan University | Karachi | aku.edu | L1 | Private, HEC-recognised (per HEC list) |
| UNI-KHI-04 | IBA Karachi | Karachi | iba.edu.pk | L1 | Business-focused public-sector institute |
| UNI-KHI-05 | Dawood University of Engineering & Technology | Karachi | duet.edu.pk | L1 | Public engineering university |
| UNI-LHE-01 | University of the Punjab | Lahore | pu.edu.pk | L1 | Largest public university in Punjab |
| UNI-LHE-02 | Lahore University of Management Sciences (LUMS) | Lahore | lums.edu.pk | L1 | Private, HEC-recognised |
| UNI-LHE-03 | Government College University, Lahore | Lahore | gcu.edu.pk | L1 | Public |
| UNI-LHE-04 | University of Engineering & Technology, Lahore | Lahore | uet.edu.pk | L1 | Public engineering university |
| UNI-LHE-05 | FAST-NUCES Lahore campus | Lahore | lahore.nu.edu.pk | L1 | Campus of a multi-city recognised university — must be recorded with campus-level city field |
| UNI-ISB-01 | Quaid-i-Azam University | Islamabad | qau.edu.pk | L1 | Top public research university |
| UNI-ISB-02 | National University of Sciences & Technology (NUST) | Islamabad | nust.edu.pk | L1 | Public, multi-campus |
| UNI-ISB-03 | COMSATS University Islamabad | Islamabad | comsats.edu.pk | L1 | Public, multi-campus (verify Islamabad campus specifically) |
| UNI-ISB-04 | Air University | Islamabad | au.edu.pk | L1 | Private/semi-govt |
| UNI-ISB-05 | Allama Iqbal Open University | Islamabad | aiou.edu.pk | L1 | Distance-learning; nationwide reach but HQ/campus in Islamabad |

**Ingestion rule:** for multi-campus universities (COMSATS, NUST, FAST-NUCES, Virtual University, etc.), always record at **campus level**, not university level, and tag each campus with its actual city. A university headquartered elsewhere with a Karachi/Lahore/Islamabad campus IS in scope for that campus record only.

### 6.3 Scholarships

| source_id | Organization | URL | City scope | Level | Notes |
|---|---|---|---|---|---|
| SCH-HEC-01 | HEC Need-Based Scholarships | hec.gov.pk/english/scholarshipsgrants/NBS/Pages/Eligibility-Criteria.aspx | Nationwide | L1 | Undergraduate need-based aid at HEC-selected public universities |
| SCH-HEC-02 | HEC National Scholarships index | hec.gov.pk/english/scholarshipsgrants/Pages/NationalScholarships.aspx | Nationwide | L1 | Indigenous PhD, regional programs, etc. |
| SCH-HEC-03 | HEC International/Overseas Scholarships index | hec.gov.pk/english/scholarshipsgrants/Pages/InternationalScholarships.aspx | Nationwide | L1 | Only include if explicitly open to Pakistani students studying abroad — label NATIONWIDE |
| SCH-UNI-* | Individual university financial-aid offices (e.g., IBA, LUMS, Aga Khan financial aid pages) | per-university domain | Per city | L1 | Each university's own site is the authority for its own scholarships |

### 6.4 Internships & Jobs (Platforms — Access Rules Are Critical)

| source_id | Platform | URL | Level | API/public access | robots/ToS position | Recommended mode |
|---|---|---|---|---|---|---|
| JOB-ROZEE-01 | Rozee.pk | rozee.pk | L2 | No public API found; public job-listing pages exist | ToS not fully reviewed in this pass — must be checked by ChatGPT/Antigravity before any automated fetch; historically the site has restricted bulk scraping | **Manual/curated import to start.** If a public API/partner feed is confirmed later, promote to semi-automated with provenance. |
| JOB-MUSTAKBIL-01 | Mustakbil.com | mustakbil.com | L2 | No confirmed public API | Must verify robots.txt/ToS before any fetch | Manual/discovery-only until verified |
| JOB-BRIGHTSPYRE-01 | BrightSpyre | brightspyre.com | L2 | No confirmed public API | Must verify robots.txt/ToS before any fetch | Manual/discovery-only until verified |
| JOB-INDEED-01 | Indeed Pakistan | pk.indeed.com | L2 | Indeed offers a limited official Publisher/XML feed program by application; no open scraping API | Indeed's ToS explicitly restricts unauthorized scraping | **API-only if approved as an Indeed publisher; otherwise discovery-only.** Never scrape directly. |
| JOB-LINKEDIN-01 | LinkedIn Jobs | linkedin.com/jobs | L2/L3 | No public jobs-search API exists even for approved partners (Talent Solutions API is enterprise/ATS-only, not a search/export API); scraping explicitly prohibited by ToS | Confirmed via 2026 developer documentation: LinkedIn removed open API access in 2015; no endpoint returns bulk job-search results | **Discovery-only.** Official org/company posts may be read manually for leads; never automate collection. |
| JOB-COMPANY-* | Individual employer career pages | per-company domain | L1 | Usually a normal public page | Respect each company's robots.txt individually | Preferred primary source — highest authority, lowest legal risk |

**Governing rule for §6.4:** No platform in this table is approved for unsupervised automated scraping in this document. Every entry defaults to **manual import or discovery-only** until a named engineer has (a) fetched and read that specific platform's robots.txt and Terms of Service, (b) confirmed an official API or data-partnership route, and (c) logged that confirmation as a `source_access_review` record. Company career pages remain the preferred, lowest-risk primary source for both jobs and internships.

### 6.5 Sports — Federations & City Bodies

| source_id | Organization | URL | Sport | City scope | Level |
|---|---|---|---|---|---|
| SPORT-PCB-01 | Pakistan Cricket Board | pcb.com.pk | Cricket | Nationwide (HQ Lahore; domestic tournaments touch all 3 cities) | L1 |
| SPORT-PCB-02 | PCB Domestic Tournaments page | pcb.com.pk/domestic-tournament.html | Cricket | Nationwide | L1 |
| SPORT-PCB-03 | PCB Age Verification / Players Development / NCA pages | pcb.com.pk (About PCB → NCA) | Cricket (trials, youth pathway) | Nationwide | L1 |
| SPORT-PFF-01 | Pakistan Football Federation | pff.com.pk | Football | Nationwide (HQ Lahore) | L1 |
| SPORT-PFF-02 | Islamabad Football Association | (affiliate of PFF; verify current URL) | Football | Islamabad | L1 |
| SPORT-NOC-01 | Pakistan Olympic Association | nocpakistan.org | Multi-sport | Nationwide | L1 |
| SPORT-UNI-* | University sports departments (e.g., NUST Sports Directorate, UET Sports Board, University of Karachi Sports Dept.) | per-university domain | Multi-sport | Per city | L1 |

**Note on football provincial bodies:** searches for "Punjab Football Association" and "Sindh Football Association" primarily surfaced India-based bodies with similar names — a good example of why every source must be individually re-verified for country/city relevance before ingestion, not assumed from a name match. Pakistani provincial football bodies should be confirmed directly through the PFF's own affiliate list, not through generic web search.

### 6.6 Learning Resources

| source_id | Organization | URL | City scope | Level |
|---|---|---|---|---|
| LEARN-DIGISKILLS-01 | DigiSkills.pk | digiskills.pk | Nationwide/Online | L1 |
| LEARN-NAVTTC-01 | NAVTTC | (official domain; verify each cycle) | Nationwide, with city-level partner institutes | L1 |
| LEARN-HEC-01 | HEC learning/training initiatives (FDP, IPFP, etc.) | hec.gov.pk | Nationwide | L1 |
| LEARN-UNI-* | University-hosted MOOCs / continuing-education centers | per-university domain | Per city | L1 |

### 6.7 Careers

The existing A&H Career database's career reference table is the seed. New career records should only be added with: field, required skills, Pakistan-market context, a university-pathway link into the Programs domain, and a source. Do not replace or delete existing career records — extend them.

### 6.8 Level 3/4 Discovery Sources (Never Direct-to-Production)

Official Instagram/Facebook/X/LinkedIn accounts of the L1 organizations above (e.g., @TheRealPCB, @TheRealPCBMedia, HEC's official social pages, FDE/HED Punjab Facebook pages) are useful for **early discovery** of tournaments, trials, and scholarship announcements — often days before the same information appears on the organization's own website. Treat every social post as a lead: extract the claim, then locate and cite the matching L1 page before the record can reach `VERIFIED`. Do not scrape these platforms with unauthorized tooling; use only their public post content as a human/Qwen-reviewed discovery signal, and never treat a listicle/blog aggregator (Level 4) as authoritative — use it only to discover candidate L1 URLs.

---

## 7. Source Access Rules (Summary)

1. **Never bypass CAPTCHAs, logins, or anti-bot systems.** If a page requires login to view (e.g., HEC scholarship application portal, most ATS application forms), that page is out of scope for automated ingestion — only the public listing/description page is in scope.
2. **Check robots.txt and ToS before any automated fetch**, per source, and log the check. Silence in robots.txt is not automatic permission — cross-check the Terms of Service too.
3. **Prefer official primary sources** (government, HEC, company career pages, federation sites) over secondary aggregators wherever both exist.
4. **Large job/internship platforms (Rozee, Mustakbil, BrightSpyre, Indeed, LinkedIn) default to manual/discovery-only** until a specific, logged access review says otherwise (see §6.4). This is the single most legally sensitive part of the whole system — treat it conservatively.
5. **Hugging Face or other public datasets**: inspect dataset card, source, license, and last-update date before use; never treat as automatically authoritative — run it through the same staging/verification pipeline as any other source.

---

## 8. Domain Schemas

Each schema below is implementation-ready: required/optional fields, validation rules, provenance fields (shared block, defined once in §9), freshness rule, dedup key, and an example record. All records also carry the shared **Provenance Block** from §9 — it is omitted from each table below to avoid repetition, but every table row implicitly includes it.

### 8.1 Schools

**Required:** `school_id`, `name`, `city` (enum: karachi/lahore/islamabad), `sector` (public/private), `level` (primary/secondary/higher-secondary/combined), `official_or_regulatory_source_id`
**Optional:** `curriculum` (Matric/O-Level/Cambridge/other), `address`, `official_website`, `admissions_contact`, `medium_of_instruction`
**Validation:** `city` must be one of the three MVP cities; `official_or_regulatory_source_id` must resolve to an entry in the source registry with `domain` including "Schools".
**Dedup key:** `(name_normalized, city, address_normalized)`
**Freshness:** long (review every 6–12 months) — school existence/level changes slowly, though FDE-style upgrades (see §6.1) do happen and should trigger a re-check when discovered.

```json
{
  "school_id": "SCH-ISB-000123",
  "name": "Islamabad Model College for Boys, G-9/1",
  "city": "islamabad",
  "sector": "public",
  "level": "combined",
  "curriculum": "Matric/FBISE",
  "official_or_regulatory_source_id": "GOV-FDE-01",
  "last_verified": "2026-08-25",
  "verification_status": "VERIFIED"
}
```

### 8.2 Colleges

**Required:** `college_id`, `name`, `city`, `sector`, `board_affiliation` (e.g., BIEK, PHEC, FBISE), `official_or_regulatory_source_id`
**Optional:** `official_website`, `programs_offered_summary`, `address`
**Validation:** `board_affiliation` must map to a known board per city (BIEK/BSEK for Karachi, HED/PHEC-linked boards for Lahore, FBISE for Islamabad).
**Dedup key:** `(name_normalized, city, board_affiliation)`
**Freshness:** long (6–12 months)

### 8.3 Universities

**Required:** `university_id`, `legal_name`, `hec_recognition_status` (recognised/NOC-suspended/not-found), `campus_city`, `sector` (public/private/semi-govt), `official_website`
**Optional:** `parent_university_name` (for multi-campus institutions), `major_departments` (list), `admissions_url`
**Validation:** `hec_recognition_status` must be cross-checked against `GOV-HEC-02` at ingestion time and again at every re-verification; a university/campus not found on the HEC list is flagged `NEEDS_REVIEW`, never auto-published as recognised.
**Dedup key:** `(legal_name_normalized, campus_city)` — campus-level, not university-level.
**Freshness:** long (6–12 months), but HEC recognition status specifically should be spot-re-checked more often (quarterly) since NOC suspensions do occur (e.g., Global Institute, Lahore, per §"Universities" search results).

### 8.4 Programs

**Required:** `program_id`, `university_id` (FK), `campus_city`, `program_name`, `degree_type` (BS/BBA/MS/MBA/PhD/etc.), `field`, `duration`, `admission_url`, `source_id`
**Optional:** `eligibility_summary` (never invent numeric cutoffs — only record what the official page states), `intake_terms`
**Validation:** `admission_url` must resolve to a page on the university's own official domain (or a domain explicitly recorded as that university's admissions portal). Do not invent tuition or eligibility figures not present on the source page — leave `null`.
**Dedup key:** `(university_id, campus_city, program_name_normalized, degree_type)`
**Freshness:** long (annual, aligned to admission cycles), but re-check at the start of each admission season.

### 8.5 Scholarships

**Required:** `scholarship_id`, `provider`, `name`, `city_scope` (karachi/lahore/islamabad/nationwide), `award_type`, `application_url`, `source_id`
**Optional:** `eligibility_summary`, `deadline` (nullable — **never inferred**), `amount_or_coverage_summary`
**Validation:** if no explicit deadline is stated on the source page, `deadline = null`; do not estimate from prior years.
**Dedup key:** `(provider, name_normalized, deadline)`
**Freshness:** short/medium (re-verify monthly during active application windows, quarterly otherwise)

### 8.6 Internships

**Required:** `internship_id`, `title`, `organization`, `city`, `field`, `source_url`, `application_url`, `status` (current/recurring/expired/discovery-only), `last_verified`
**Optional:** `skills` (list), `eligibility_summary`, `deadline` (nullable)
**Validation:** a record may only carry `status: current` if `last_verified` is within the domain's freshness window (see §11) AND it has a resolvable `source_url`. No live internship record without provenance — enforced at the database constraint level, not just application logic.
**Dedup key:** `(organization_normalized, title_normalized, city)`
**Freshness:** short (7–14 days for "current" status; anything older auto-transitions to `STALE`)

### 8.7 Jobs

**Required:** `job_id`, `title`, `organization`, `city`, `field`, `source_url`, `status`, `last_verified`
**Optional:** `application_url`, `skills`, `seniority_level`, `remote_option`
**Validation:** same provenance-mandatory rule as Internships. Jobs sourced from L2 platforms (Rozee etc.) must retain the original platform URL and be marked with their Level-2 provenance, never re-labeled as if they came from the employer directly.
**Dedup key:** `(organization_normalized, title_normalized, city, source_url)`
**Freshness:** very short (3–7 days) — jobs are the most volatile domain; never present a job older than its freshness window as current.

### 8.8 Sports (Organizations / Programmes / Opportunities)

**Required:** `sport_entity_id`, `entity_type` (organization/programme/opportunity), `sport`, `city`, `name`, `source_id`
**Optional:** `official_website`, `age_groups`, `contact`, `description`
**Validation:** `entity_type` must be one of the enumerated values; a "programme" or "opportunity" must reference a parent `organization` record where one exists.
**Dedup key:** `(sport, name_normalized, city, entity_type)`
**Freshness:** hybrid — organizations/programmes: long (6–12 months); opportunities (open registration windows): short (matches Internships cadence)

### 8.9 Tournaments

**Required:** `tournament_id`, `sport`, `title`, `organizer`, `city`, `registration_deadline` (nullable, never inferred), `registration_url`, `source_id`, `last_verified`
**Optional:** `dates` (nullable), `eligibility_summary`
**Validation:** never infer `dates` or `registration_deadline` — both must be explicitly present on the source page or left `null`.
**Dedup key:** `(sport, title_normalized, organizer, city)`
**Freshness:** very short (7 days)

### 8.10 Trials

**Required:** `trial_id`, `sport`, `organizer`, `city`, `trial_type` (cricket/football/university-team/academy/federation), `source_id`, `last_verified`
**Optional:** `date` (nullable), `registration_url`, `eligibility_summary`
**Validation:** every trial requires provenance — no exceptions; if `source_id` cannot be resolved to a registry entry, the record cannot leave `DISCOVERED` state.
**Dedup key:** `(sport, organizer, city, trial_type, date)`
**Freshness:** very short (7 days)

### 8.11 Learning Resources

**Required:** `resource_id`, `title`, `provider`, `access_type` (free/paid/scholarship-funded/university-provided), `city_scope` (karachi/lahore/islamabad/nationwide-online), `source_url`
**Optional:** `field`, `duration`, `certificate_issuer`
**Validation:** do not invent course availability or session dates not present on the provider's page.
**Dedup key:** `(provider, title_normalized)`
**Freshness:** medium (quarterly)

### 8.12 Careers

**Required:** `career_id`, `career_name`, `field`, `required_skills` (list), `pakistan_context_summary`, `source_id`, `last_updated`
**Optional:** `university_pathway_program_ids` (FK list into Programs), `risks_summary`, `general_rewards_summary`
**Validation:** must not duplicate or overwrite an existing career record from the current database; new records only, or explicit merge-with-review.
**Dedup key:** `career_name_normalized`
**Freshness:** long (annual review)

---

## 9. Shared Provenance Block (attached to every record in every domain)

```json
{
  "source_id": "GOV-HEC-02",
  "source_url": "https://www.hec.gov.pk/english/universities/pages/recognised.aspx",
  "source_name": "HEC Recognised Universities",
  "source_type": "government_official",
  "fetched_at": "2026-09-01T10:00:00Z",
  "last_verified": "2026-09-01",
  "content_hash": "sha256:...",
  "verification_status": "VERIFIED",
  "confidence": "high",
  "evidence": "Table row matched university legal_name and city."
}
```

---

## 10. Database Design

**Recommendation: Hybrid model (Option C)** — a shared `opportunities` table for the six inherently opportunity-shaped, deadline-driven domains (Scholarships, Internships, Jobs, Tournaments, Trials, and Sports "opportunity" rows), plus **separate normalized reference tables** for the structurally different, relationship-heavy domains (Schools, Colleges, Universities→Campuses→Programs, Sports organizations/programmes, Careers). This avoids both extremes flagged in the brief: it is not 12 independent giant tables, and it does not force structurally different things (a university degree program vs. a 2-week trial) into one oversized polymorphic table.

**Core relationships:**

```
Source (registry)
   ├── School (city, board)
   ├── College (city, board)
   ├── University
   │      └── Campus (city)
   │             └── Program
   ├── SportOrganization (city)
   │      └── SportProgramme
   ├── Career
   └── Opportunity (shared table)
          ├── kind: scholarship | internship | job | tournament | trial | sports_opportunity
          ├── organization_ref  → University | SportOrganization | free-text employer
          ├── city
          └── Source (FK, required)
```

**Compatibility with the existing system:** the shared `Opportunity` table is designed to be a natural extension of whatever `opportunity` concept already exists in the current SQLAlchemy models (per the brief's mention of "opportunity visibility gates") — add a `kind` discriminator column and `city`/domain-specific JSON `details` column rather than creating a parallel opportunity system. Existing gates (visibility, verification) apply unchanged to all six `kind` values.

**New tables to add (illustrative names, adapt to existing naming conventions):**
`source_registry`, `schools`, `colleges`, `universities`, `campuses`, `programs`, `sport_organizations`, `sport_programmes`, `careers`, and an extension of the existing `opportunities` table with `kind`, `city`, `sport` (nullable), `source_id` (FK, NOT NULL), `verification_status`, `content_hash`.

---

## 11. Provenance & Verification

**Verification states** (as specified): `DISCOVERED → EXTRACTED → VALIDATED → NEEDS_REVIEW → VERIFIED → REJECTED → STALE`

**Auto-verification eligibility by domain:**

| Domain | Auto-verification allowed? | Rationale |
|---|---|---|
| Schools, Colleges, Universities, Programs, Careers | Yes, for L1-sourced records that pass deterministic validation (Pydantic + HEC cross-check) | Static, low ambiguity, official sources |
| Learning Resources | Yes for L1 sources; human review for L2/L3 | Moderate ambiguity |
| Scholarships, Internships, Jobs, Tournaments, Trials | **No — human review required** before `VERIFIED`, regardless of source level | Deadline-bearing, directly actionable, highest harm if wrong (a student missing/mis-timing a real deadline) |
| Sports organizations/programmes | Auto for L1; review for L2/L3 | Mixed — the static "organization" shell can auto-verify, but any date-bearing "opportunity" row under it follows the Opportunity rule above |

Only `VERIFIED` records may be surfaced as authoritative student-facing claims; everything else stays behind the existing opportunity-visibility gates.

---

## 12. Freshness Rules by Domain

| Domain | Freshness window | Behavior on expiry |
|---|---|---|
| Jobs | 3–7 days | Auto-transition to `STALE`; hidden from student-facing results until re-verified |
| Internships | 7–14 days | Same |
| Tournaments | 7 days | Same |
| Trials | 7 days | Same |
| Scholarships | 14–30 days (shorter near known deadlines) | Same |
| Learning Resources | ~90 days | Flagged for re-check, not hidden |
| Sports organizations/programmes | 90–180 days | Flagged for re-check |
| Schools, Colleges | 180–365 days | Flagged for re-check |
| Universities, Programs | 180–365 days, HEC-recognition spot-check quarterly | Flagged for re-check |
| Careers | 365 days | Flagged for re-check |

No single 30-day rule is applied uniformly, per the requirement — each domain has its own window above.

---

## 13. Deduplication

Each domain's dedup key is defined in its schema (§8). General rules:
- Normalize names (lowercase, strip punctuation/whitespace) before key comparison.
- For opportunities (jobs/internships/scholarships/tournaments/trials), also fold in `source_url` domain so that the same job re-posted on two different platforms is stored as **two distinct records with cross-links**, not silently merged — different platforms may have different application flows.
- Campus-level dedup for universities (§8.3) prevents one multi-city university from colliding across Karachi/Lahore/Islamabad campus records.

---

## 14. Retrieval / Search

Retrieval facets: exact name, city, field, sport, skills, opportunity type, university, program — using the existing FTS engine.

**Recommended indexes:**
- FTS index over `(name, description, field, skills)` per table, or over the shared `details` JSON for the `Opportunity` table.
- B-tree/composite index on `(city, kind, verification_status)` for the `Opportunity` table — this is the hot path for almost every student query ("internships in Karachi in software").
- B-tree index on `(campus_city, field)` for `Program`.
- Composite `(sport, city)` index for sport tables.

**Enforcement:** every retrieval path that is student-facing must filter `verification_status = VERIFIED` (or whatever states the existing visibility gate already allows) — this is enforced at the query layer, not left to the caller.

---

## 15. Qwen Extraction Architecture

**Qwen's role:** extraction, normalization, classification, summarization. **Never** the source of truth.

```
SOURCE → extraction (Qwen) → deterministic validation (Pydantic) → provenance → verification (human/rule) → database
```
Not:
```
SOURCE → Qwen → production database   ✗ (never do this)
```

**Qwen input contract (per extraction call):**
```json
{
  "source_text": "<raw fetched page text or relevant excerpt>",
  "source_metadata": {"source_id": "...", "source_url": "...", "fetched_at": "..."},
  "target_schema": "<one of the 12 domain JSON schemas from §8>"
}
```

**Qwen output contract:**
```json
{
  "candidate_record": { "...fields matching target_schema..." },
  "evidence": "short quote or pointer to where in source_text each key field was found",
  "missing_fields": ["deadline", "eligibility_summary"],
  "confidence": "high | medium | low"
}
```

Qwen must never populate `source_url`, `source_id`, or any provenance field itself — those come only from the fetch layer, never from model generation. If Qwen cannot find a field in the source text, it must return it as `missing_fields`, not guess it (this directly enforces the "never infer dates" rules in §8.5/§8.9/§8.10).

Model routing follows the existing pattern already in production: `qwen3.7-plus` primary, with the existing fallback chain (`qwen3.6-plus` → `qwen-plus-2025-07-28` → `qwen3-vl-235b-a22b-thinking`) unchanged.

---

## 16. Ingestion Architecture

```
SOURCE → FETCH → EXTRACT (Qwen) → NORMALIZE → DEDUP → VALIDATE (Pydantic)
      → STAGE → VERIFY / HUMAN REVIEW → DATABASE → FTS/CACHE → MCP → A&H Career → Qwen (mentor) → STUDENT
```

Supported input formats: CSV, JSON, HTML (fetched pages), API responses, manually supplied exports, Hugging Face datasets (with mandatory dataset-card/license/provenance inspection before use), and permitted public pages only.

**Staging model:** every candidate record lands in a `staging_records` table with its full provenance block and verification_status, decoupled from the live, student-facing tables. Promotion from staging to live tables happens only at `VERIFIED`.

---

## 17. Static vs. Dynamic Strategy

**STATIC/slow-changing:** Schools, Colleges, Universities, Programs, Careers — batch-ingested, long freshness windows, low-frequency re-crawl scheduler (monthly/quarterly).

**DYNAMIC:** Internships, Jobs, Scholarships-with-deadlines, Tournaments, Trials — event-driven/frequent re-crawl scheduler (daily to weekly depending on domain per §12), mandatory provenance, human review before `VERIFIED`.

**HYBRID:** Learning Resources, Sports programmes — the shell (course catalog entry, programme description) is static; specific cohorts/enrollment windows are dynamic and should be modeled as child `Opportunity` rows under the static parent.

The ingestion scheduler should run two cadences: a slow static crawl and a fast dynamic crawl, sharing the same STAGE → VERIFY → DATABASE pipeline.

---

## 18. Target Dataset Sizes (MVP, Three Cities)

| Domain | Target range | Basis |
|---|---|---|
| Schools | Low hundreds per city (start with FDE's ~430 Islamabad institutions as a fully-covered pilot city; Karachi/Lahore seeded from board affiliate lists) | FDE publishes a complete institution list; Sindh/Punjab require board-by-board aggregation |
| Colleges | Dozens to ~150 per city (BIEK alone affiliates ~354 colleges across Karachi region — filter to city proper) | BIEK affiliation count |
| Universities/Campuses | All HEC-recognised campuses physically located in the 3 cities (realistically 40–70 total across all three) | HEC recognised list, filtered by city |
| Programs | Several hundred to low thousands (avg. 10–30 programs × 40–70 campuses) | Derived from campus count |
| Scholarships | 2–4 dozen active at any time (HEC national/international index + major university financial-aid pages) | HEC scholarship index breadth |
| Internships | Low hundreds if legally/technically available, sourced primarily from company career pages | Conservative given platform access restrictions (§6.4) |
| Jobs | Dynamic ingestion only — no static target; expect continuous churn, prioritizing company career pages | Volatility of domain |
| Sports | Several dozen organizations/programmes across the three cities and covered sports | Federation + university sports department coverage |
| Tournaments | Dynamic — no static target; seasonal spikes around PCB/PFF calendars | Event-driven |
| Trials | Dynamic — no static target | Event-driven |
| Learning Resources | Several dozen to ~150 (DigiSkills course catalog + NAVTTC partner institutes + university continuing-ed) | DigiSkills + NAVTTC catalog breadth |
| Careers | 20–30 stable references, extending the existing database | Per brief |

These are realistic starting ranges, not hard caps — the ingestion system should scale organically as more L1 sources are verified.

---

## 19. QA / Testing

- Every new domain table gets: schema/Pydantic validation tests, dedup-key collision tests, and a provenance-completeness test (no record may exist in a live table without a resolvable `source_id`).
- Freshness-expiry tests: a record older than its domain window must be demonstrably excluded from student-facing queries.
- HEC cross-check test: any `University`/`Campus` record with `hec_recognition_status = recognised` must have been checked against a fetch of `GOV-HEC-02` within the current quarter.
- "Never-infer" tests for nullable date fields (`deadline`, `dates`, `registration_deadline`) — a test fixture with no date present in source text must produce `null`, not a guessed date, from the Qwen extraction step.
- Extend the existing 300+ automated test suite; do not create a parallel test framework.

---

## 20. Legal / Platform Constraints

- No automated scraping of platforms whose Terms of Service prohibit it (confirmed for LinkedIn Jobs; presumed-restricted and unverified for Rozee/Mustakbil/BrightSpyre/Indeed pending a logged robots.txt/ToS review — see §6.4).
- No CAPTCHA/anti-bot bypass, ever, for any source.
- Government and HEC sources are public-interest data and generally safe for automated fetch of public pages, but application portals requiring login remain out of scope.
- Hugging Face or other third-party datasets require license/provenance review before ingestion, and are never auto-treated as authoritative.
- Instagram/Facebook/X content from official organization accounts should be read via the platform's own public post view or (preferably) an approved official API; do not use unauthorized scraping tools against these platforms either.

---

## 21. Implementation Roadmap (Data Collection Workflow)

Optimized around value (universities/programs are highest-value, lowest-volatility) and freshness (dynamic domains need a working pipeline before they're worth populating):

**Week 1 — Foundations:** Source registry implementation; Universities + Programs (Karachi/Lahore/Islamabad, HEC cross-checked); Schools + Colleges seed (start with Islamabad/FDE as the pilot, fully-covered city); Careers extension.

**Week 2 — Funding & Skills:** Scholarships (HEC + top university financial-aid pages); Learning Resources (DigiSkills, NAVTTC, HEC initiatives, university continuing-ed).

**Week 3 — Opportunity Pipeline:** Internships + Jobs — build the dynamic ingestion pipeline and human-review queue first, then populate from company career pages as the primary source; only add L2 platform data after a logged access review per §6.4.

**Week 4 — Sports:** Sports organizations/programmes, Tournaments, Trials — federation and university sports-department sourcing, dynamic pipeline reuse from Week 3.

Each week ends with a QA pass against §19 before moving on.

---

## 22. Handoff to Antigravity

Implement, without rewriting the existing application:

**Files/modules to create:**
- `knowledge_engine/source_registry.py` (or equivalent per existing module layout) — CRUD + validation for the source table in §6.
- `knowledge_engine/models/` — SQLAlchemy models for `schools`, `colleges`, `universities`, `campuses`, `programs`, `sport_organizations`, `sport_programmes`, `careers`, and the `kind`/`city`/`source_id` extension to the existing `opportunities` model.
- `knowledge_engine/staging.py` — staging table + promotion logic (`DISCOVERED → ... → VERIFIED`).
- `knowledge_engine/ingestion/` — fetch adapters per source type (HTML page, JSON/API, CSV import, Hugging Face dataset import), all writing into staging only.
- `knowledge_engine/validation/` — Pydantic schemas mirroring §8, including the "never-infer-dates" rule as a validator.
- `knowledge_engine/dedup.py` — normalization + dedup-key logic per domain.
- `knowledge_engine/freshness.py` — scheduler jobs implementing §12's windows and auto-`STALE` transitions.
- Admin/review interface: a lightweight staging-review screen (reuse existing admin patterns if present) so human reviewers can move `NEEDS_REVIEW` opportunity records to `VERIFIED`/`REJECTED`.

**Database changes:** new tables listed above; extend `opportunities` with `kind`, `city`, `sport` (nullable), `source_id` (FK NOT NULL), `content_hash`; add FTS indexes and the composite indexes from §14.

**MCP changes:** expose new MCP tools/resources for querying schools/colleges/universities/programs/careers (read-mostly) and the extended opportunities table (filtered to `VERIFIED` for student-facing tool calls, matching the existing opportunity-visibility gate pattern).

**API changes:** new read endpoints per domain under the existing FastAPI router conventions; no breaking changes to existing endpoints.

**Search/caching/refresh:** wire new tables into the existing FTS/search layer; add scheduler entries for the static (monthly/quarterly) and dynamic (daily/weekly) crawl cadences from §17.

**Tests:** extend the existing 300+ test suite per §19 rather than creating a separate suite.

---

## 23. Handoff to ChatGPT

Tasks suited to ChatGPT-driven research/ops work, one source at a time:

1. For each source_id in §6, fetch and read that platform's robots.txt and Terms of Service; log a `source_access_review` record (allowed/manual-only/discovery-only) before any automated fetch is attempted — this is mandatory for §6.4 platforms specifically.
2. Verify every URL in §6 is still live and topically correct; flag broken or redirected links.
3. Produce seed JSON files per domain (§8 schemas) from the L1 sources in §6, city by city, starting with the Week 1 roadmap items.
4. Normalize and deduplicate CSV/JSON exports supplied by university/government offices.
5. Cross-check every candidate `University`/`Campus` record against the HEC recognised list (`GOV-HEC-02`) before marking `VALIDATED`.
6. Audit a sample of `VERIFIED` records each week for data-quality drift (broken links, stale deadlines).
7. Write/maintain migration scripts for the new tables listed in §22.
8. Produce small test/fixture datasets for the QA suite in §19, including deliberately incomplete source text to test the "never-infer-dates" validator.

---

## 24. Handoff to Qwen

Qwen receives exactly the input contract in §15 (`source_text`, `source_metadata`, `target_schema`) and returns exactly the output contract (`candidate_record`, `evidence`, `missing_fields`, `confidence`). Qwen never creates or edits `source_url`/`source_id`, never invents a value for a field absent from `source_text`, and never writes directly to any live/production table — only to the staging layer, via the deterministic validation step. Use the existing model fallback chain unchanged (`qwen3.7-plus` → `qwen3.6-plus` → `qwen-plus-2025-07-28` → `qwen3-vl-235b-a22b-thinking`).

---

## 25. Definition of Done (MVP)

- [ ] Source registry populated with the entries in §6, each with a logged `source_access_review`.
- [ ] All 12 domain tables/models created per §22, extending (not replacing) the existing schema.
- [ ] Staging → verification pipeline operational end-to-end for at least one domain in each of the Static/Dynamic/Hybrid buckets (§17).
- [ ] HEC cross-check enforced for every `University`/`Campus` record.
- [ ] "Never-infer-dates" validator enforced and tested for Scholarships/Tournaments/Trials.
- [ ] Freshness auto-`STALE` scheduler running for Jobs, Internships, Tournaments, Trials.
- [ ] FTS + composite indexes from §14 live and query-tested.
- [ ] MCP tools exposing the new domains, filtered to `VERIFIED`/visibility-gated records only.
- [ ] Existing 300+ test suite extended and passing with the new modules included.
- [ ] Roadmap Weeks 1–4 (§21) data populated for at least the pilot city (Islamabad, via FDE) end-to-end, with Karachi/Lahore following the same pipeline.
- [ ] No domain, table, or ingestion job references any city outside Karachi, Lahore, Islamabad except explicitly labeled `NATIONWIDE`/`ONLINE` entities.

---

*End of document. All sources cited above were located via live web research during this session; URLs should be re-verified by the ingestion team before production use, per the mandatory `source_access_review` and `last_verified` fields defined throughout.*
