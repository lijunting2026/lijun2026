export interface UserInfo {
  id: string
  username: string
  display_name: string
  role: string
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface Grade {
  id: string
  name: string
  sort_order: number
  created_at: string | null
}

export interface ClassInfo {
  id: string
  name: string
  grade_id: string
  grade_name: string | null
  student_count: number
  created_at: string | null
}

export interface Subject {
  id: string
  name: string
  full_score: number
  sort_order: number
  created_at: string | null
}

export interface Student {
  id: string
  student_no: string
  name: string
  gender: string
  class_id: string
  class_name: string | null
  grade_name: string | null
  created_at: string | null
}

export interface TransferRequest {
  target_class_id: string
  migrate_scores: boolean
}

export interface TransferResponse {
  id: string
  student_no: string
  student_name: string
  original_class_name: string
  target_class_name: string
  migrated_score_count: number
  scores_follow_student: boolean
}

export interface ExamSubject {
  id: string
  subject_id: string
  subject_name: string | null
  full_score: number
  weight: number
}

export interface Exam {
  id: string
  name: string
  exam_date: string | null
  exam_type: string
  grade_id: string
  grade_name: string | null
  exam_subjects: ExamSubject[]
  created_at: string | null
}

export interface ScoreRecord {
  id: string
  student_id: string
  exam_id: string | null
  exam_name: string | null
  student_no: string | null
  student_name: string | null
  exam_subject_id: string
  subject_name: string | null
  score_value: number
  status: string
}

export interface SubjectStats {
  subject_id: string
  subject_name: string
  full_score: number
  avg_score: number
  max_score: number
  min_score: number
  pass_rate: number
  excellent_rate: number
  std_dev: number
  avg_score_rate: number
}

export interface ClassSubjectStats {
  class_id: string
  class_name: string
  student_count: number
  stats: SubjectStats[]
}

export interface ExamAnalysis {
  exam_id: string
  exam_name: string
  exam_date: string | null
  total_students: number
  grade_stats: SubjectStats[]
  class_stats: ClassSubjectStats[]
}

export interface ScoreDistribution {
  range_label: string
  count: number
  percentage: number
}

export interface DistributionResponse {
  subject_id: string
  subject_name: string
  distributions: ScoreDistribution[]
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
}
