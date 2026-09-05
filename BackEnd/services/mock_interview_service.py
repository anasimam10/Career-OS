"""Service layer for Mock Interviews."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from models.mock_interview import MockInterviewSession, MockInterviewQuestion
from models.learning import LearningResource
from models.career import Career
from schemas.mock_interview import (
    MockInterviewGenerationResult,
    MockInterviewQuestionSchema,
    MockInterviewOption,
    MockInterviewSetupRequest,
    MockInterviewSubmitAnswerRequest
)
from prompts.mock_interview import MOCK_INTERVIEW_SYSTEM_PROMPT, MOCK_INTERVIEW_USER_PROMPT_TEMPLATE
from services.ai_service import get_ai_service, AIServiceError

logger = logging.getLogger("ah_career.mock_interviews")

def _build_grounded_fallback(career_context: str, difficulty: str, db: Session) -> MockInterviewGenerationResult:
    """Deterministic fallback questions grounded in verified career skills if AI provider is unreachable."""
    # Find matching career
    career = db.query(Career).filter(
        (Career.name.ilike(f"%{career_context}%")) |
        (Career.field.ilike(f"%{career_context}%")) |
        (Career.slug.ilike(f"%{career_context}%"))
    ).first()

    skills = ["Fundamentals", "Problem Solving", "Core Concepts", "Analysis"]
    if career and career.required_skills:
        try:
            parsed = json.loads(career.required_skills) if isinstance(career.required_skills, str) else career.required_skills
            if isinstance(parsed, list) and parsed:
                skills = parsed
        except Exception:
            pass

    is_finance = any(k in career_context.lower() for k in ["account", "finance", "audit", "tax"])
    
    if is_finance:
        base_questions = [
            ("What is the primary objective of the Double-Entry Bookkeeping system?",
             [("A", "Ensure every transaction affects at least two accounts to maintain balance"),
              ("B", "Pay tax twice on all recorded business transactions"),
              ("C", "Keep two separate confidential accounting ledgers"),
              ("D", "Estimate future capital revenues")],
             "A", "Double-entry bookkeeping mandates equal debits and credits across accounts.", "Financial Accounting"),
            ("Which financial statement demonstrates financial position at a specific point in time?",
             [("A", "Balance Sheet / Statement of Financial Position"),
              ("B", "Income Statement"),
              ("C", "Cash Flow Statement"),
              ("D", "Statement of Retained Earnings")],
             "A", "A Balance Sheet reports assets, liabilities, and equity at a specific reporting date.", "Financial Reporting"),
            ("In cost accounting, how are fixed costs characterized relative to production volume?",
             [("A", "They remain constant in total within the relevant range"),
              ("B", "They increase proportionally per unit produced"),
              ("C", "They decrease to zero as volume decreases"),
              ("D", "They vary directly with labor hours")],
             "A", "Fixed costs remain unchanged in total regardless of output within the relevant range.", "Cost Accounting"),
            ("Under Pakistan's Companies Act and IFRS, what is the matching principle?",
             [("A", "Revenues and their associated expenses must be recognized in the same period"),
              ("B", "All assets must strictly match total liabilities with zero equity"),
              ("C", "Cash flows must equal accrued net income"),
              ("D", "Tax expenses must match previous year calculations")],
             "A", "The matching principle requires expenses to be recognized alongside related revenues.", "Accounting Standards"),
            ("What does the Current Ratio (Current Assets / Current Liabilities) evaluate?",
             [("A", "Short-term liquidity and ability to meet immediate debt obligations"),
              ("B", "Long-term solvency and leverage over 10 years"),
              ("C", "Asset depreciation rate"),
              ("D", "Gross margin profitability")],
             "A", "The Current Ratio is a standard measure of short-term liquidity.", "Financial Analysis"),
            ("When valuing capital budgeting projects, why is Net Present Value (NPV) preferred?",
             [("A", "It accounts for the time value of money and calculates net shareholder wealth creation"),
              ("B", "It ignores the cost of capital"),
              ("C", "It is always identical to the internal rate of return"),
              ("D", "It requires no discount rate")],
             "A", "NPV discounts future cash flows at the required rate of return.", "Corporate Finance"),
            ("What is the impact of recording unearned revenue on the balance sheet?",
             [("A", "Increases Cash and increases Current Liabilities"),
              ("B", "Decreases Cash and increases Retained Earnings"),
              ("C", "Increases Net Income immediately"),
              ("D", "Reduces total assets")],
             "A", "Unearned revenue is a liability representing an obligation to provide future goods/services.", "Financial Accounting"),
            ("What is a primary internal control to prevent payroll and disbursement fraud?",
             [("A", "Segregation of duties between authorization and payment disbursement"),
              ("B", "Allowing a single manager to issue and approve all checks"),
              ("C", "Eliminating monthly bank reconciliations"),
              ("D", "Processing all transactions in unrecorded petty cash")],
             "A", "Segregation of duties ensures no individual controls all stages of a transaction.", "Auditing & Internal Controls"),
            ("In financial management, what constitutes Working Capital?",
             [("A", "Current Assets minus Current Liabilities"),
              ("B", "Total Assets minus Total Equity"),
              ("C", "Cash plus Fixed Plant Equipment"),
              ("D", "Net Profit before Taxes")],
             "A", "Working capital is current assets minus current liabilities.", "Working Capital Management"),
            ("Under Pakistani taxation (FBR guidelines), what is Withholding Tax (WHT)?",
             [("A", "Tax deducted at the source of payment by the payer"),
              ("B", "A voluntary tip paid to the tax authority"),
              ("C", "Tax only applicable to unregistered individuals"),
              ("D", "An import-only customs surcharge")],
             "A", "Withholding tax is income tax deducted directly at source when payments are made.", "Taxation in Pakistan")
        ]
    else:
        base_questions = [
            ("What is the time complexity of searching for an element in a balanced Binary Search Tree (BST)?",
             [("A", "O(log n)"),
              ("B", "O(n)"),
              ("C", "O(1)"),
              ("D", "O(n log n)")],
             "A", "In a balanced BST, halving the search space at each step yields logarithmic time O(log n).", "Data Structures"),
            ("In object-oriented design, what does the SOLID 'Single Responsibility Principle' state?",
             [("A", "A class should have only one reason to change"),
              ("B", "A class should only have a single method"),
              ("C", "An interface must contain only one signature"),
              ("D", "All variables must be declared as private constants")],
             "A", "SRP specifies that every module or class should be responsible for one specific part of functionality.", "Software Architecture"),
            ("Which HTTP status code signifies that the requested resource was not found on the server?",
             [("A", "404 Not Found"),
              ("B", "500 Internal Server Error"),
              ("C", "200 OK"),
              ("D", "403 Forbidden")],
             "A", "404 indicates the origin server did not find a current representation for the target resource.", "Web Development & APIs"),
            ("In relational database systems, what property does ACID 'Atomicity' guarantee?",
             [("A", "All operations in a transaction succeed completely or all are rolled back"),
              ("B", "Data is instantly replicated to multiple physical drives"),
              ("C", "Queries always execute in sub-millisecond time"),
              ("D", "Keys are auto-incrementing integers only")],
             "A", "Atomicity ensures all-or-nothing execution for database transactions.", "Database Systems"),
            ("What is the primary difference between a Stack and a Queue data structure?",
             [("A", "Stack is Last-In-First-Out (LIFO); Queue is First-In-First-Out (FIFO)"),
              ("B", "Stack is FIFO; Queue is LIFO"),
              ("C", "Stack uses hashing; Queue uses pointers"),
              ("D", "Stack allows random access; Queue does not")],
             "A", "A stack operates on LIFO semantics, while a queue operates on FIFO semantics.", "Data Structures"),
            ("In RESTful API design, which HTTP method is typically used to create a new resource?",
             [("A", "POST"),
              ("B", "GET"),
              ("C", "DELETE"),
              ("D", "HEAD")],
             "A", "POST is conventionally used to submit data that creates a new subordinate resource.", "Web Development & APIs"),
            ("What does the 'DRY' principle stand for in software engineering?",
             [("A", "Don't Repeat Yourself"),
              ("B", "Data Recovery Yield"),
              ("C", "Deploy Rapidly Yearly"),
              ("D", "Dynamic Resource Yielding")],
             "A", "DRY focuses on reducing duplication of information and business logic in codebases.", "Software Engineering Practices"),
            ("Why is using an index on a database table advantageous for SELECT queries?",
             [("A", "It reduces disk I/O by allowing fast B-tree or hash lookups instead of full table scans"),
              ("B", "It automatically encrypts table data"),
              ("C", "It speeds up INSERT and UPDATE statements unconditionally"),
              ("D", "It prevents duplicate rows across all columns")],
             "A", "Indexes enable fast lookups for specific keys, avoiding costly full table scans.", "Database Systems"),
            ("What is the function of Git version control branching?",
             [("A", "Isolate work in progress without affecting the main stable codebase"),
              ("B", "Compress commits into a zip file"),
              ("C", "Permanently delete historical commits"),
              ("D", "Execute unit tests in the cloud")],
             "A", "Branches allow developers to work on features or fixes in isolation before merging.", "Version Control & DevOps"),
            ("In asynchronous programming (e.g. Python asyncio or JavaScript Promises), what is an Event Loop?",
             [("A", "A continuous loop that monitors and dispatches events and non-blocking I/O callbacks"),
              ("B", "An infinite CPU loop that halts thread execution"),
              ("C", "A recursive sorting function"),
              ("D", "A hardware timer on the motherboard")],
             "A", "The event loop manages the scheduling and execution of asynchronous tasks and callbacks.", "Concurrent Programming")
        ]

    # Look up actual learning resource IDs
    resources = db.query(LearningResource).filter(LearningResource.is_active == True).limit(5).all()
    res_ids = [str(r.id) for r in resources]

    questions = []
    for idx, (text, options_list, correct, expl, topic) in enumerate(base_questions, 1):
        opts = [MockInterviewOption(id=opt_id, text=opt_text) for opt_id, opt_text in options_list]
        questions.append(
            MockInterviewQuestionSchema(
                id=f"q_{idx}",
                question=text,
                options=opts,
                correct_option=correct,
                explanation=expl,
                topic=topic,
                source_resource_ids=res_ids[:2]
            )
        )

    return MockInterviewGenerationResult(
        title=f"{career_context} Mock Interview ({difficulty.capitalize()})",
        career=career_context,
        difficulty=difficulty,
        questions=questions
    )


# In-memory question bank cache: (normalized_career, difficulty) -> MockInterviewGenerationResult
_QUESTION_CACHE: dict[tuple[str, str], MockInterviewGenerationResult] = {}

_PRIMARY_GROUNDED_KEYWORDS = [
    "software", "computer", "cs", "web", "program", "develop",
    "account", "finance", "audit", "banking", "tax"
]


def generate_mock_interview(
    db: Session, student_id: int, request: MockInterviewSetupRequest
) -> MockInterviewSession:
    """
    Generates a 10-question mock interview session using Qwen (via ai_service),
    grounded in the existing Career OS knowledge base.
    Optimized with targeted grounding and in-memory question caching for sub-second latency.
    """
    norm_career = request.career_context.strip().lower()
    norm_diff = request.difficulty.strip().lower()
    cache_key = (norm_career, norm_diff)

    if cache_key in _QUESTION_CACHE:
        result = _QUESTION_CACHE[cache_key]
    else:
        # Check if this matches our primary grounded curricula
        is_primary = any(kw in norm_career for kw in _PRIMARY_GROUNDED_KEYWORDS)
        
        # 1. Career-specific grounding
        career = db.query(Career).filter(
            (Career.name.ilike(f"%{request.career_context}%")) |
            (Career.field.ilike(f"%{request.career_context}%")) |
            (Career.slug.ilike(f"%{request.career_context}%"))
        ).first()

        context_parts = []
        if career:
            context_parts.append(f"Target Career: {career.name} (Field: {career.field})")
            if career.required_skills:
                try:
                    skills = json.loads(career.required_skills) if isinstance(career.required_skills, str) else career.required_skills
                    context_parts.append(f"Required Skills in Pakistan: {', '.join(skills[:5])}")
                except Exception:
                    context_parts.append(f"Required Skills: {career.required_skills}")

        # 2. Grounding: gather up to 3 directly relevant learning resources
        search_kw = career.field if career and career.field else request.career_context
        resources = (
            db.query(LearningResource)
            .filter(
                LearningResource.is_active.is_(True),
                (
                    LearningResource.title.ilike(f"%{search_kw}%")
                    | LearningResource.skill_name.ilike(f"%{search_kw}%")
                ),
            )
            .limit(3)
            .all()
        )
        if not resources:
            resources = (
                db.query(LearningResource)
                .filter(LearningResource.is_active.is_(True))
                .limit(3)
                .all()
            )

        if resources:
            res_text = "\n".join(
                f"- {r.title} (Provider: {r.provider or 'Verified'}, ID: {r.id})"
                for r in resources
            )
            context_parts.append(f"Relevant Learning Resources:\n{res_text}")

        ai_service = get_ai_service()
        result = None

        if ai_service.is_configured():
            try:
                knowledge_context = "\n".join(context_parts) if context_parts else f"Context for {request.career_context}"
                system_prompt = MOCK_INTERVIEW_SYSTEM_PROMPT.format(difficulty=request.difficulty)
                user_prompt = MOCK_INTERVIEW_USER_PROMPT_TEMPLATE.format(
                    career_context=request.career_context,
                    difficulty=request.difficulty,
                    knowledge_context=knowledge_context
                )
                result = ai_service.call_structured(
                    prompt=user_prompt,
                    response_model=MockInterviewGenerationResult,
                    system_prompt=system_prompt,
                    operation="generate_mock_interview",
                )
                _QUESTION_CACHE[cache_key] = result
            except (AIServiceError, Exception) as e:
                logger.warning(f"AI question generation failed: {e}. Using grounded fallback.")
                result = _build_grounded_fallback(request.career_context, request.difficulty, db)
                _QUESTION_CACHE[cache_key] = result
        else:
            result = _build_grounded_fallback(request.career_context, request.difficulty, db)
            _QUESTION_CACHE[cache_key] = result

    # Save to database
    session = MockInterviewSession(
        student_id=student_id,
        career_context=request.career_context,
        difficulty=request.difficulty,
        total_questions=len(result.questions)
    )
    db.add(session)
    db.flush()

    for q in result.questions:
        options_json = json.dumps([{"id": opt.id, "text": opt.text} for opt in q.options])
        resource_ids = json.dumps(q.source_resource_ids)
        
        question_obj = MockInterviewQuestion(
            session_id=session.id,
            question_text=q.question,
            options=options_json,
            correct_option_id=q.correct_option,
            explanation=q.explanation,
            topic=q.topic,
            source_resource_ids=resource_ids
        )
        db.add(question_obj)
    
    db.commit()
    db.refresh(session)
    return session


def submit_answer(
    db: Session, student_id: int, session_id: int, request: MockInterviewSubmitAnswerRequest
):
    """Submits an answer for a specific question."""
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == session_id,
        MockInterviewSession.student_id == student_id
    ).first()
    
    if not session:
        raise ValueError("Session not found")
        
    if session.status != "in_progress":
        raise ValueError("Interview already completed")

    question = db.query(MockInterviewQuestion).filter(
        MockInterviewQuestion.id == request.question_id,
        MockInterviewQuestion.session_id == session_id
    ).first()
    
    if not question:
        raise ValueError("Question not found")

    question.selected_option_id = request.selected_option_id
    db.commit()


def complete_interview(db: Session, student_id: int, session_id: int) -> MockInterviewSession:
    """Completes the interview and calculates the deterministic score."""
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == session_id,
        MockInterviewSession.student_id == student_id
    ).first()
    
    if not session:
        raise ValueError("Session not found")
        
    questions = db.query(MockInterviewQuestion).filter(
        MockInterviewQuestion.session_id == session_id
    ).all()

    correct_count = 0
    for q in questions:
        if q.selected_option_id and q.selected_option_id == q.correct_option_id:
            correct_count += 1
            
    score_percentage = (correct_count / len(questions)) * 100 if questions else 0.0
    
    session.status = "completed"
    session.score = score_percentage
    session.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session
