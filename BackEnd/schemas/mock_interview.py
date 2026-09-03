"""Mock Interview Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MockInterviewOption(BaseModel):
    id: str
    text: str

class MockInterviewQuestionSchema(BaseModel):
    id: str
    question: str
    options: List[MockInterviewOption]
    correct_option: str
    explanation: str
    topic: str
    source_resource_ids: List[str] = []

class MockInterviewGenerationResult(BaseModel):
    title: str
    career: str
    difficulty: str
    questions: List[MockInterviewQuestionSchema]

class MockInterviewSetupRequest(BaseModel):
    career_context: str
    difficulty: str

class MockInterviewQuestionResponse(BaseModel):
    id: int
    question_text: str
    options: List[MockInterviewOption]
    # No correct_option in the response to prevent cheating
    selected_option_id: Optional[str] = None
    topic: str

class MockInterviewSessionResponse(BaseModel):
    id: int
    career_context: str
    difficulty: str
    status: str
    score: Optional[float] = None
    total_questions: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[MockInterviewQuestionResponse]

class MockInterviewSubmitAnswerRequest(BaseModel):
    question_id: int
    selected_option_id: str

class MockInterviewResultTopic(BaseModel):
    topic: str
    correct: int
    total: int

class MockInterviewQuestionReview(BaseModel):
    id: int
    question_text: str
    options: List[MockInterviewOption]
    selected_option_id: Optional[str]
    correct_option_id: str
    explanation: str
    topic: str
    source_resource_ids: List[str] = []
    resource_url: Optional[str] = None
    resource_title: Optional[str] = None

class MockInterviewResultsResponse(BaseModel):
    id: int
    career_context: str
    difficulty: str
    score: float
    total_correct: int
    total_questions: int
    performance_label: str
    topic_performance: List[MockInterviewResultTopic]
    questions_review: List[MockInterviewQuestionReview]
    next_best_action_text: str
    next_best_action_resource_id: Optional[str] = None
    next_best_action_url: Optional[str] = None
