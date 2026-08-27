export type Phase = "INGEST" | "REVIEW" | "RESULT"
export type ReviewStatus = "pending" | "approved" | "rejected" | "corrected"

export interface Evidence extends Record<string, unknown> {
  source_document?: string
  snippet?: string
  page?: number | null
  confidence?: number
  bbox?: number[] | null
}

export interface SkillExperience extends Record<string, unknown> {
  skill: string
  months: number
  evidence?: Evidence[]
}

export interface ExtractedField extends Record<string, unknown> {
  name: string
  ai_value?: string | null
  human_value?: string | null
  review_status?: ReviewStatus
  evidence?: Evidence[]
}

export interface ExperienceEntry extends Record<string, unknown> {
  title: string
  company: string
  start_date: string
  end_date?: string | null
  skills_used?: string[]
  domains?: string[]
  evidence?: Evidence[]
}

export interface CandidateProfile extends Record<string, unknown> {
  candidate_id: string
  full_name?: string | null
  email?: string | null
  phone?: string | null
  location?: string | null
  current_title?: string | null
  current_company?: string | null
  total_experience_months?: number
  work_authorization?: string | null
  notice_period_days?: number | null
  skills?: SkillExperience[]
  experiences?: ExperienceEntry[]
  fields_for_review?: ExtractedField[]
  [key: string]: unknown
}

export interface JobRequirement extends Record<string, unknown> {
  role_title: string
  min_total_experience_months?: number
  mandatory_skills?: string[]
  preferred_skills?: string[]
  required_domains?: string[]
  [key: string]: unknown
}

export interface MandatoryRule extends Record<string, unknown> {
  id: string
  type: string
  severity?: "hard_fail" | "soft" | string
  weight?: number
  skill?: string | null
  min_months?: number | null
  max_days?: number | null
  domain?: string | null
  expected_value?: string | null
}

export interface ScreeningRequest {
  candidate: CandidateProfile
  job: JobRequirement
  rules: MandatoryRule[]
}

export interface RuleResult extends Record<string, unknown> {
  rule_id: string
  passed: boolean
  severity?: string
  weight?: number
  message: string
  evidence?: Evidence[]
}

export interface ScoreBreakdown extends Record<string, unknown> {
  mandatory_fit: number
  experience_depth: number
  skill_match: number
  domain_relevance?: number
  recency?: number
  evidence_confidence?: number
  final_score: number
}

export interface InterviewQuestion extends Record<string, unknown> {
  question: string
  type: string
  purpose: string
  good_answer_signals: string
  evidence_anchor?: string | null
}

export interface ScreeningResponse extends Record<string, unknown> {
  recommendation: string
  grade?: string
  hard_fail: boolean
  rule_results: RuleResult[]
  scores: ScoreBreakdown
  explanation: string
  strengths?: string[]
  concerns?: string[]
  red_flags?: string[]
  next_action?: string
  interview_questions?: InterviewQuestion[]
  communication_draft?: string | null
}

export interface ParseDocumentResponse {
  filename?: string
  text?: string
  error?: string
}

export interface HealthResponse {
  status: string
  groq_configured?: boolean
}

export interface ExtractPayload {
  resume_text: string
  jd_text: string
  mandatory_rule_notes: string
}
