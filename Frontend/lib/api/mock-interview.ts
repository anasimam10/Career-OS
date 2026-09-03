import { apiGet, apiPost } from "./client"

export interface MockInterviewOption {
  id: string
  text: string
}

export interface MockInterviewQuestion {
  id: number
  question_text: string
  options: MockInterviewOption[]
  selected_option_id?: string | null
  topic: string
}

export interface MockInterviewSession {
  id: number
  career_context: string
  difficulty: string
  status: string
  score?: number | null
  total_questions: number
  started_at: string
  completed_at?: string | null
  questions: MockInterviewQuestion[]
}

export interface MockInterviewQuestionReview {
  id: number
  question_text: string
  options: MockInterviewOption[]
  selected_option_id?: string | null
  correct_option_id: string
  explanation: string
  topic: string
  source_resource_ids: string[]
  resource_url?: string | null
  resource_title?: string | null
}

export interface MockInterviewTopicPerformance {
  topic: string
  correct: number
  total: number
}

export interface MockInterviewResults {
  id: number
  career_context: string
  difficulty: string
  score: number
  total_correct: number
  total_questions: number
  performance_label: string
  topic_performance: MockInterviewTopicPerformance[]
  questions_review: MockInterviewQuestionReview[]
  next_best_action_text: string
  next_best_action_resource_id?: string | null
  next_best_action_url?: string | null
}

export async function setupMockInterview(career_context: string, difficulty: string): Promise<MockInterviewSession> {
  return apiPost<MockInterviewSession>("/mock-interviews/setup", {
    career_context,
    difficulty,
  })
}

export async function getMockInterview(sessionId: number | string): Promise<MockInterviewSession> {
  return apiGet<MockInterviewSession>(`/mock-interviews/${sessionId}`)
}

export async function submitMockInterviewAnswer(
  sessionId: number | string,
  questionId: number,
  selectedOptionId: string
): Promise<{ status: string }> {
  return apiPost<{ status: string }>(`/mock-interviews/${sessionId}/submit`, {
    question_id: questionId,
    selected_option_id: selectedOptionId,
  })
}

export async function completeMockInterview(sessionId: number | string): Promise<MockInterviewResults> {
  return apiPost<MockInterviewResults>(`/mock-interviews/${sessionId}/complete`, {})
}

export async function getMockInterviewResults(sessionId: number | string): Promise<MockInterviewResults> {
  return apiGet<MockInterviewResults>(`/mock-interviews/${sessionId}/results`)
}
