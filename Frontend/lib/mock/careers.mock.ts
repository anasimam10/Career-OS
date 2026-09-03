import type {
  CareerListItem,
  Career,
  CareerRealityResponse,
  CareerTrialPlan,
} from "@/lib/types/career.types"

export const MOCK_CAREER_LIST: CareerListItem[] = [
  { slug: "software-engineering", name: "Software Engineering", field: "Technology", demand_level: "HIGH" },
  { slug: "data-science", name: "Data Science", field: "Technology", demand_level: "HIGH" },
  { slug: "cybersecurity", name: "Cybersecurity", field: "Technology", demand_level: "HIGH" },
  { slug: "ui-ux-design", name: "UI/UX Design", field: "Design", demand_level: "MEDIUM" },
  { slug: "mobile-development", name: "Mobile App Development", field: "Technology", demand_level: "HIGH" },
  { slug: "medicine", name: "Medicine (MBBS)", field: "Healthcare", demand_level: "HIGH" },
  { slug: "business-administration", name: "Business Administration", field: "Business", demand_level: "MEDIUM" },
  { slug: "finance-banking", name: "Finance & Banking", field: "Business", demand_level: "MEDIUM" },
  { slug: "electrical-engineering", name: "Electrical Engineering", field: "Engineering", demand_level: "HIGH" },
  { slug: "civil-engineering", name: "Civil Engineering", field: "Engineering", demand_level: "MEDIUM" },
  { slug: "mechanical-engineering", name: "Mechanical Engineering", field: "Engineering", demand_level: "MEDIUM" },
  { slug: "marketing", name: "Marketing & Digital Media", field: "Business", demand_level: "MEDIUM" },
  { slug: "teaching", name: "Teaching & Education", field: "Education", demand_level: "MEDIUM" },
  { slug: "pharmacy", name: "Pharmacy", field: "Healthcare", demand_level: "MEDIUM" },
  { slug: "accounting", name: "Accounting & Finance", field: "Business", demand_level: "HIGH" },
]

export const MOCK_CAREERS: Record<string, Career> = {
  "software-engineering": {
    slug: "software-engineering",
    name: "Software Engineering",
    field: "Technology",
    demand_level: "HIGH",
    competition_level: "HIGH",
    difficulty_level: "MEDIUM",
    required_skills: ["Python", "JavaScript", "Data Structures", "Git", "Algorithms"],
    pk_opportunities: [
      "Consistent demand across software houses and product startups in major cities",
      "Remote work opportunities for international and regional clients",
      "Active freelance and contract development market",
      "Broad career progression from junior developer to engineering lead",
    ],
    top_pk_universities: ["FAST-NUCES", "LUMS", "NUST", "UET Lahore", "IBA Karachi", "GIKI"],
    risks: [
      "Highly competitive degree admissions",
      "Requires continuous self-learning as industry tools change",
      "Entry-level roles vary significantly in quality and compensation",
    ],
    last_updated: "2025-06-01",
  },
  "data-science": {
    slug: "data-science",
    name: "Data Science",
    field: "Technology",
    demand_level: "HIGH",
    competition_level: "MEDIUM",
    difficulty_level: "HIGH",
    required_skills: ["Python", "Statistics", "Machine Learning", "SQL", "Data Visualisation"],
    pk_opportunities: [
      "Growing analytics requirements in Pakistani banking, telecom, and e-commerce",
      "Increasing adoption of machine learning in digital services",
      "Remote data analysis roles available internationally",
    ],
    top_pk_universities: ["LUMS", "FAST-NUCES", "NUST", "Karachi University"],
    risks: [
      "Strong mathematical and statistical foundations required",
      "Local market for specialized senior roles is still maturing",
    ],
    last_updated: "2025-06-01",
  },
  "medicine": {
    slug: "medicine",
    name: "Medicine (MBBS)",
    field: "Healthcare",
    demand_level: "HIGH",
    competition_level: "HIGH",
    difficulty_level: "HIGH",
    required_skills: ["Biology", "Chemistry", "Physics", "MDCAT preparation", "Clinical skills"],
    pk_opportunities: [
      "High ongoing societal demand for qualified medical professionals",
      "Clinical opportunities in public health systems and private hospitals",
      "Specialization pathways in surgery, pediatrics, internal medicine, and research",
    ],
    top_pk_universities: ["AKHSS", "PIMS", "CMH Lahore", "King Edward Medical University", "Aga Khan University"],
    risks: [
      "Demanding 5+ year MBBS program followed by intensive house job/residency",
      "Highly competitive national entrance testing (MDCAT)",
      "Extended timeline before reaching independent senior practice",
    ],
    last_updated: "2025-06-01",
  },
}

export const MOCK_REALITY_CHECK: Record<string, CareerRealityResponse> = {
  "software-engineering": {
    reality: {
      career_name: "Software Engineering",
      demand_level: "HIGH",
      competition_level: "HIGH",
      difficulty_level: "MEDIUM",
      required_skills: ["Python", "JavaScript", "Data Structures", "Git", "Algorithms"],
      pk_opportunities: [
        "Consistent demand across software houses in Karachi, Lahore, and Islamabad",
        "Opportunities for remote development and freelance contracts",
        "Strong startup ecosystem in fintech and logistics",
      ],
      risks: [
        "Competitive entrance requirements at leading universities",
        "Continuous requirement to learn new tools and frameworks",
        "Initial learning curve for technical problem solving",
      ],
      rewards: [
        "Strong long-term earning potential for skilled problem solvers",
        "High flexibility and remote work possibilities",
        "Transferable skills applicable globally",
        "Practical ability to build independent products and tools",
      ],
      data_source: "Career OS verified database, updated 2025",
    },
    verdict: {
      verdict: "WORTH_EXPLORING",
      headline: "Software Engineering is a strong choice — but test it first.",
      reasoning:
        "Your interests align well with technology, and Pakistan's tech market is genuinely growing. However, competition is high and the field requires real passion to sustain. The 7-day trial will help you confirm this is the right path before committing.",
      student_strengths_match: ["Interest in technology", "Willingness to learn", "Access to free online resources"],
      gaps_to_address: ["Programming fundamentals", "Mathematics foundations", "Project experience"],
      suggested_trial: "7-Day CS Exploration",
    },
  },
}

export const MOCK_TRIAL_PLAN: Record<string, CareerTrialPlan> = {
  "software-engineering": {
    career_slug: "software-engineering",
    duration_days: 7,
    days: [
      {
        day_range: "Day 1–2",
        title: "Python Setup & First Program",
        tasks: [
          "Install Python and VS Code",
          "Complete the official Python beginner tutorial (python.org)",
          "Write a program that asks your name and greets you",
        ],
      },
      {
        day_range: "Day 3–4",
        title: "Build Something Simple",
        tasks: [
          "Build a simple calculator in Python",
          "Learn about variables, loops, and conditions",
          "Post your code to GitHub (create a free account)",
        ],
      },
      {
        day_range: "Day 5–6",
        title: "Explore What Engineers Actually Do",
        tasks: [
          "Watch: \"A Day in the Life of a Software Engineer in Pakistan\" on YouTube",
          "Read about how apps like Bykea or Foodpanda are built",
          "Join a Pakistani developer Discord or Facebook group",
        ],
      },
      {
        day_range: "Day 7",
        title: "Reflect & Decide",
        tasks: [
          "Answer the reflection prompt honestly",
          "Rate your enjoyment from 1–10",
          "Decide: continue or explore another field?",
        ],
      },
    ],
    reflection_prompt:
      "After 7 days, how did it feel? Was the problem-solving enjoyable or frustrating? Did you find yourself curious to learn more, or relieved to stop?",
  },
}
