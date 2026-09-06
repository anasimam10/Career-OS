"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Search,
  MapPin,
  BookOpen,
  Award,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Loader2,
  GraduationCap,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

// ── Types matching actual API response ────────────────────────────────────────

interface Program {
  id: number;
  university_id: number;
  name: string;
  degree_type?: string | null;
  field?: string | null;
  duration_years?: number | null;
  annual_fee_pkr?: number | null;
  admission_link?: string | null;
  career_ids?: number[];
}

interface University {
  id: number;
  name: string;
  short_name?: string | null;
  slug: string;
  city?: string | null;
  province?: string | null;
  type?: "PUBLIC" | "PRIVATE" | string | null;
  hec_recognized?: boolean | null;
  hec_category?: string | null;
  website_url?: string | null;
  website?: string | null;
  admissions_url?: string | null;
  ranking?: number | null;
  hec_ranking?: number | null;
  programs?: Program[];
  program_count?: number;
  entry_tests?: string[];
  merit_percentage?: number | null;
  established?: number | null;
}

// ── Curated Ranking & Detail Knowledge Maps ───────────────────────────────────

const UNIVERSITY_RANKINGS: Record<string, number> = {
  nust: 1,
  qau: 2,
  lums: 3,
  pieas: 4,
  aku: 5,
  comsats: 6,
  giki: 7,
  "uet-lahore": 8,
  "fast-nuces": 9,
  "iba-karachi": 10,
  pu: 11,
  ku: 12,
  ned: 13,
  uaf: 14,
  "gcu-lahore": 15,
  bahria: 16,
  air: 17,
  ist: 18,
  szabist: 19,
  kinnaird: 20,
  bnu: 21,
  habib: 22,
  kemu: 23,
  dow: 24,
  nca: 25,
  "uet-taxila": 26,
  nutech: 27,
  ndu: 28,
  iiui: 29,
  pide: 30,
  iobm: 31,
  kiet: 32,
  riphah: 33,
  superior: 34,
  umt: 35,
  uol: 36,
  fjmu: 37,
  aiou: 38,
  bzu: 39,
  uop: 40,
};

const UNIVERSITY_DETAILS: Record<
  string,
  { entry_tests?: string[]; merit_percentage?: number; established?: number }
> = {
  nust: { entry_tests: ["NET", "SAT", "ACT"], merit_percentage: 76, established: 1991 },
  qau: { entry_tests: ["QAU Entry Test", "Merit-based"], merit_percentage: 72, established: 1967 },
  lums: { entry_tests: ["LCAT", "SAT", "ACT"], merit_percentage: 82, established: 1985 },
  pieas: { entry_tests: ["PIEAS Written Test"], merit_percentage: 78, established: 1967 },
  aku: { entry_tests: ["AKU Test", "MDCAT"], merit_percentage: 85, established: 1983 },
  comsats: { entry_tests: ["NTS-NAT", "NTS-GAT"], merit_percentage: 68, established: 1998 },
  giki: { entry_tests: ["GIKI Admission Test"], merit_percentage: 74, established: 1993 },
  "uet-lahore": { entry_tests: ["ECAT"], merit_percentage: 72, established: 1921 },
  "fast-nuces": { entry_tests: ["NU Test", "NTS-NAT", "SAT"], merit_percentage: 71, established: 2000 },
  "iba-karachi": { entry_tests: ["IBA Aptitude Test", "SAT"], merit_percentage: 75, established: 1955 },
  pu: { entry_tests: ["PU Entry Test", "USAT"], merit_percentage: 65, established: 1882 },
  ku: { entry_tests: ["KU Entry Test"], merit_percentage: 60, established: 1951 },
  ned: { entry_tests: ["NED Entry Test"], merit_percentage: 70, established: 1921 },
  "gcu-lahore": { entry_tests: ["GCU Entry Test"], merit_percentage: 65, established: 1864 },
  bahria: { entry_tests: ["CBT Entry Test", "NTS-NAT"], merit_percentage: 60, established: 2000 },
  air: { entry_tests: ["AU Entry Test", "NTS-NAT"], merit_percentage: 65, established: 2002 },
  ist: { entry_tests: ["NTS-NAT", "SAT"], merit_percentage: 68, established: 2002 },
  szabist: { entry_tests: ["SZABIST Test"], merit_percentage: 60, established: 1995 },
  habib: { entry_tests: ["Habib Test", "SAT"], merit_percentage: 75, established: 2014 },
  nutech: { entry_tests: ["NU-TEST", "SAT"], merit_percentage: 68, established: 2018 },
  aiou: { entry_tests: ["Open Admissions"], merit_percentage: 50, established: 1974 },
};

function resolveKnownRank(u: University): number | null {
  if (u.ranking) return u.ranking;
  if (u.hec_ranking) return u.hec_ranking;
  if (u.slug && UNIVERSITY_RANKINGS[u.slug]) return UNIVERSITY_RANKINGS[u.slug];

  const s = (u.short_name || "").toLowerCase();
  const n = u.name.toLowerCase();

  if (s === "nust" || n.includes("national university of sciences and technology")) return 1;
  if (s === "qau" || n.includes("quaid-i-azam") || n.includes("quaid-e-azam")) return 2;
  if (s === "lums" || n.includes("lahore university of management sciences")) return 3;
  if (s === "pieas") return 4;
  if (s === "aku" || n.includes("aga khan")) return 5;
  if (s.includes("comsats") || n.includes("comsats")) return 6;
  if (s === "giki" || n.includes("ghulam ishaq khan")) return 7;
  if (s.includes("uet") && (n.includes("lahore") || u.city === "Lahore")) return 8;
  if (s.includes("fast") || n.includes("emerging sciences")) return 9;
  if (s === "iba" || n.includes("institute of business administration")) return 10;

  return null;
}

function resolveKnownDetails(u: University) {
  const custom = u.slug ? UNIVERSITY_DETAILS[u.slug] : undefined;
  if (custom) return custom;

  const n = u.name.toLowerCase();
  const s = (u.short_name || "").toLowerCase();

  for (const [key, details] of Object.entries(UNIVERSITY_DETAILS)) {
    if (n.includes(key) || s === key) return details;
  }

  // Fallback defaults based on type
  const isMed = n.includes("medical") || n.includes("health");
  const isEng = n.includes("engineering") || n.includes("technology");

  return {
    entry_tests: isMed ? ["MDCAT"] : isEng ? ["ECAT", "NTS-NAT"] : ["NTS-NAT", "University Entry Test"],
    merit_percentage: u.type?.toUpperCase() === "PUBLIC" ? 65 : 55,
    established: null,
  };
}

// ── Constants ────────────────────────────────────────────────────────────────

const PROVINCES = [
  "All Provinces",
  "Punjab",
  "Sindh",
  "KPK",
  "Balochistan",
  "Islamabad",
  "AJK",
  "Gilgit-Baltistan",
];

const TYPES = ["All Types", "Public", "Private"];

const SORT_OPTIONS = [
  { value: "ranking", label: "By Ranking" },
  { value: "name", label: "A–Z" },
  { value: "programs", label: "Most Programs" },
];

function normalizeApiBase(): string {
  let base = (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "https://ah-career-backend.onrender.com"
  ).trim();

  base = base.replace(/\/+$/, "");
  if (!base.endsWith("/api/v1")) {
    if (base.endsWith("/api")) {
      base = `${base}/v1`;
    } else {
      base = `${base}/api/v1`;
    }
  }
  return base;
}

export default function UniversitiesPage() {
  const [universities, setUniversities] = useState<University[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [province, setProvince] = useState("All Provinces");
  const [type, setType] = useState("All Types");
  const [sort, setSort] = useState("ranking");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Cache for on-demand fetched programs by university id
  const [programsMap, setProgramsMap] = useState<Record<number, Program[]>>({});
  const [loadingPrograms, setLoadingPrograms] = useState<Record<number, boolean>>({});

  const apiBase = useMemo(() => normalizeApiBase(), []);

  useEffect(() => {
    let isCancelled = false;

    async function loadUniversities() {
      setLoading(true);
      setError(null);

      // Attempt primary configured API base
      try {
        const res = await fetch(`${apiBase}/universities?limit=300`);
        if (!res.ok) throw new Error("Primary fetch failed");
        const data = await res.json();
        const rawList = Array.isArray(data) ? data : data.universities || data.data || [];
        if (!isCancelled) {
          setUniversities(rawList);
          setLoading(false);
        }
        return;
      } catch {
        // Fallback to live Render backend if localhost is offline
        if (apiBase.includes("localhost")) {
          try {
            const fallbackRes = await fetch("https://ah-career-backend.onrender.com/api/v1/universities?limit=300");
            if (!fallbackRes.ok) throw new Error("Fallback fetch failed");
            const data = await fallbackRes.json();
            const rawList = Array.isArray(data) ? data : data.universities || data.data || [];
            if (!isCancelled) {
              setUniversities(rawList);
              setLoading(false);
            }
            return;
          } catch {
            // fall through to error
          }
        }

        if (!isCancelled) {
          setError("Couldn't load universities. Please try again.");
          setLoading(false);
        }
      }
    }

    loadUniversities();

    return () => {
      isCancelled = true;
    };
  }, [apiBase]);

  // Fetch programs on-demand when a university card is expanded
  const handleToggleExpand = useCallback(
    async (uniId: number) => {
      if (expandedId === uniId) {
        setExpandedId(null);
        return;
      }

      setExpandedId(uniId);

      // If programs already fetched, return
      if (programsMap[uniId] !== undefined) return;

      setLoadingPrograms((prev) => ({ ...prev, [uniId]: true }));

      try {
        let res = await fetch(`${apiBase}/universities/${uniId}/programs`);
        if (!res.ok && apiBase.includes("localhost")) {
          res = await fetch(`https://ah-career-backend.onrender.com/api/v1/universities/${uniId}/programs`);
        }

        if (res.ok) {
          const data = await res.json();
          const list: Program[] = Array.isArray(data) ? data : data.programs || [];
          setProgramsMap((prev) => ({ ...prev, [uniId]: list }));
        } else {
          setProgramsMap((prev) => ({ ...prev, [uniId]: [] }));
        }
      } catch {
        setProgramsMap((prev) => ({ ...prev, [uniId]: [] }));
      } finally {
        setLoadingPrograms((prev) => ({ ...prev, [uniId]: false }));
      }
    },
    [expandedId, programsMap, apiBase]
  );

  // ── Filter + Sort ──────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    const sLower = search.trim().toLowerCase();

    let result = universities.filter((u) => {
      const matchSearch =
        !sLower ||
        u.name.toLowerCase().includes(sLower) ||
        (u.short_name && u.short_name.toLowerCase().includes(sLower)) ||
        (u.city && u.city.toLowerCase().includes(sLower));

      const uProv = u.province || "";
      const matchProvince =
        province === "All Provinces" ||
        uProv === province ||
        (province === "KPK" && (uProv === "Khyber Pakhtunkhwa" || uProv === "KPK")) ||
        (province === "AJK" && (uProv === "Azad Jammu and Kashmir" || uProv === "AJK"));

      const uType = (u.type || "").toUpperCase();
      const matchType =
        type === "All Types" ||
        (type === "Public" && uType === "PUBLIC") ||
        (type === "Private" && uType === "PRIVATE") ||
        uType === type.toUpperCase();

      return matchSearch && matchProvince && matchType;
    });

    result.sort((a, b) => {
      if (sort === "ranking") {
        const ra = resolveKnownRank(a) ?? 9999;
        const rb = resolveKnownRank(b) ?? 9999;
        if (ra !== rb) return ra - rb;
        return a.name.localeCompare(b.name);
      }
      if (sort === "name") {
        return a.name.localeCompare(b.name);
      }
      if (sort === "programs") {
        const pa = programsMap[a.id]?.length ?? a.program_count ?? a.programs?.length ?? 0;
        const pb = programsMap[b.id]?.length ?? b.program_count ?? b.programs?.length ?? 0;
        if (pa !== pb) return pb - pa;
        return a.name.localeCompare(b.name);
      }
      return 0;
    });

    return result;
  }, [universities, search, province, type, sort, programsMap]);

  // ── Loading Skeleton ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <div className="h-4 w-28 bg-gray-800 rounded animate-pulse mb-3" />
        <div className="h-9 w-64 sm:w-80 bg-gray-800 rounded animate-pulse mb-2" />
        <div className="h-4 w-60 sm:w-96 bg-gray-800/80 rounded animate-pulse mb-8" />
        <div className="flex flex-wrap gap-3 mb-6">
          <div className="h-11 flex-1 min-w-[200px] bg-gray-800/60 rounded-lg animate-pulse" />
          <div className="h-11 w-36 bg-gray-800/60 rounded-lg animate-pulse" />
          <div className="h-11 w-32 bg-gray-800/60 rounded-lg animate-pulse" />
          <div className="h-11 w-36 bg-gray-800/60 rounded-lg animate-pulse" />
        </div>
        <div className="flex flex-col gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-800/50 border border-gray-800 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error State ────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-20 text-center">
        <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto flex items-center justify-center mb-4 border border-red-500/20">
          <Award className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Failed to Load Universities</h2>
        <p className="text-gray-400 text-sm max-w-md mx-auto mb-6">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors cursor-pointer"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="mb-8">
        <p className="text-xs font-semibold tracking-widest text-blue-400 uppercase mb-2 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          Higher Education Explorer
        </p>
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-2">
          Pakistani Universities
        </h1>
        <p className="text-gray-400 text-sm leading-relaxed max-w-2xl">
          {universities.length} universities · verified degree programs, merit thresholds, and entry tests across Pakistan.
        </p>
      </div>

      {/* ── Filters ──────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 mb-6">
        {/* Search */}
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search universities, short names, or cities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900/90 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white placeholder-gray-500 pl-9 pr-4 py-2.5 rounded-lg transition-colors"
          />
        </div>

        {/* Province filter */}
        <select
          value={province}
          onChange={(e) => setProvince(e.target.value)}
          aria-label="Filter by Province"
          className="bg-gray-900/90 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white px-3 py-2.5 rounded-lg transition-colors cursor-pointer"
        >
          {PROVINCES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>

        {/* Type filter */}
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          aria-label="Filter by University Type"
          className="bg-gray-900/90 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white px-3 py-2.5 rounded-lg transition-colors cursor-pointer"
        >
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        {/* Sort */}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          aria-label="Sort Universities"
          className="bg-gray-900/90 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white px-3 py-2.5 rounded-lg transition-colors cursor-pointer"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* ── Results count ─────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
        <span>
          Showing {filtered.length} of {universities.length} universities
        </span>
        {(search || province !== "All Provinces" || type !== "All Types") && (
          <button
            onClick={() => {
              setSearch("");
              setProvince("All Provinces");
              setType("All Types");
            }}
            className="text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
          >
            Reset all filters
          </button>
        )}
      </div>

      {/* ── Empty filter state ────────────────────────────────────────────── */}
      {filtered.length === 0 && (
        <div className="text-center py-16 px-4 rounded-xl border border-gray-800/80 bg-gray-900/40 text-gray-400">
          <GraduationCap className="w-10 h-10 text-gray-600 mx-auto mb-3" />
          <p className="text-base font-semibold text-gray-300">No universities match your filters.</p>
          <p className="text-xs text-gray-500 mt-1">Try broadening your search term or selecting a different province.</p>
          <button
            onClick={() => {
              setSearch("");
              setProvince("All Provinces");
              setType("All Types");
            }}
            className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-blue-400 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* ── University list ───────────────────────────────────────────────── */}
      <div className="flex flex-col gap-2.5">
        {filtered.map((uni) => {
          const rank = resolveKnownRank(uni);
          const details = resolveKnownDetails(uni);
          const isExpanded = expandedId === uni.id;
          const loadedPrograms = programsMap[uni.id];
          const isLoadingProgs = loadingPrograms[uni.id];
          const progCount = loadedPrograms !== undefined ? loadedPrograms.length : uni.program_count ?? null;
          const websiteUrl = uni.website_url || uni.website;
          const admissionsUrl = uni.admissions_url;
          const formattedType =
            uni.type?.toUpperCase() === "PUBLIC"
              ? "Public"
              : uni.type?.toUpperCase() === "PRIVATE"
              ? "Private"
              : uni.type || "Accredited";

          return (
            <div
              key={uni.id}
              className={`bg-gray-900/70 border transition-all duration-200 rounded-xl overflow-hidden ${
                isExpanded ? "border-blue-500/50 shadow-lg shadow-blue-950/20" : "border-gray-800 hover:border-gray-700"
              }`}
            >
              {/* ── Card row (always visible) ─────────────────────────────── */}
              <button
                type="button"
                onClick={() => handleToggleExpand(uni.id)}
                className="w-full flex items-center gap-3.5 sm:gap-4 px-4 sm:px-5 py-4 text-left cursor-pointer"
                aria-expanded={isExpanded}
              >
                {/* Ranking badge */}
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold ${
                    rank && rank <= 10
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.15)]"
                      : rank && rank <= 50
                      ? "bg-blue-500/15 text-blue-400 border border-blue-500/25"
                      : "bg-gray-800 text-gray-500 border border-gray-700"
                  }`}
                  title={rank ? `National Rank #${rank}` : "HEC Recognized Institution"}
                >
                  {rank ? `#${rank}` : "—"}
                </div>

                {/* Name + location */}
                <div className="flex-1 min-w-0 pr-2">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-white truncate">{uni.name}</p>
                    {uni.short_name && (
                      <span className="hidden sm:inline-block text-[11px] font-mono text-gray-400 bg-gray-800 px-1.5 py-0.2 rounded border border-gray-700/60">
                        {uni.short_name}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3 h-3 text-blue-400/80 shrink-0" aria-hidden="true" />
                    <span className="truncate">
                      {uni.city}
                      {uni.city && uni.province ? ", " : ""}
                      {uni.province}
                    </span>
                  </p>
                </div>

                {/* Type badge */}
                <span
                  className={`hidden sm:inline-flex flex-shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${
                    formattedType === "Public"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : formattedType === "Private"
                      ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                      : "bg-gray-700/50 text-gray-400 border-gray-600/30"
                  }`}
                >
                  {formattedType}
                </span>

                {/* Programs count (if loaded or known) */}
                {progCount !== null && (
                  <span className="hidden md:inline-flex flex-shrink-0 items-center gap-1 text-xs text-gray-400">
                    <BookOpen className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                    {progCount} {progCount === 1 ? "program" : "programs"}
                  </span>
                )}

                {/* Expand chevron */}
                <span className="flex-shrink-0 text-gray-500">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </span>
              </button>

              {/* ── Expanded detail ──────────────────────────────────────── */}
              {isExpanded && (
                <div className="px-4 sm:px-5 pb-5 border-t border-gray-800/80 bg-gray-950/30">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    {/* Merit threshold */}
                    {details.merit_percentage !== null && details.merit_percentage !== undefined && (
                      <div>
                        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Min. Merit
                        </p>
                        <p className="text-sm font-semibold text-white">~{details.merit_percentage}%</p>
                      </div>
                    )}

                    {/* Entry tests */}
                    {details.entry_tests && details.entry_tests.length > 0 && (
                      <div className="col-span-2">
                        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Entry Tests
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {details.entry_tests.map((test) => (
                            <span
                              key={test}
                              className="text-xs bg-gray-800 text-gray-300 px-2.5 py-0.5 rounded border border-gray-700"
                            >
                              {test}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Established */}
                    {details.established ? (
                      <div>
                        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Established
                        </p>
                        <p className="text-sm font-semibold text-white">{details.established}</p>
                      </div>
                    ) : (
                      <div className="sm:hidden">
                        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Sector
                        </p>
                        <p className="text-sm font-semibold text-white">{formattedType}</p>
                      </div>
                    )}
                  </div>

                  {/* Programs section */}
                  <div className="mt-5 pt-4 border-t border-gray-800/60">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mb-2">
                      Verified Programs
                    </p>

                    {isLoadingProgs ? (
                      <div className="flex items-center gap-2 py-3 text-xs text-gray-400">
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                        <span>Loading verified programs for {uni.name}...</span>
                      </div>
                    ) : loadedPrograms && loadedPrograms.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {loadedPrograms.slice(0, 12).map((prog) => (
                          <span
                            key={prog.id}
                            className="text-xs bg-gray-800/80 text-gray-300 px-2.5 py-1 rounded-lg border border-gray-700/60"
                          >
                            {prog.name}
                            {prog.degree_type && (
                              <span className="ml-1 text-[10px] text-blue-400 font-semibold">
                                ({prog.degree_type})
                              </span>
                            )}
                          </span>
                        ))}
                        {loadedPrograms.length > 12 && (
                          <span className="text-xs text-blue-400 font-medium px-2 py-1 flex items-center">
                            +{loadedPrograms.length - 12} more programs
                          </span>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500 italic">
                        No specific programs cataloged in database yet. Refer to official university admissions for current offerings.
                      </p>
                    )}
                  </div>

                  {/* Action Links */}
                  <div className="flex flex-wrap items-center gap-4 mt-5 pt-3 border-t border-gray-800/60 text-xs">
                    {websiteUrl && (
                      <a
                        href={websiteUrl.startsWith("http") ? websiteUrl : `https://${websiteUrl}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-blue-400 hover:text-blue-300 transition-colors font-medium"
                      >
                        Visit university website
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}

                    {admissionsUrl && (
                      <a
                        href={admissionsUrl.startsWith("http") ? admissionsUrl : `https://${admissionsUrl}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 transition-colors font-medium"
                      >
                        Admissions portal
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Back link ─────────────────────────────────────────────────────── */}
      <div className="mt-10 pt-6 border-t border-gray-800">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-300 transition-colors inline-flex items-center gap-1.5">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
