export interface UserInfo {
    id: string
    username: string
    display_name: string
    role: string
    is_active: boolean
    needs_password_change: boolean
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


// Dashboard types
export interface DashboardStats {
  grades: number
  classes: number
  subjects: number
  students: number
  exams: number
  scores: number
}

export interface RecentExam {
  exam_name: string
  exam_date: string
  avg_rate: number
  student_count: number
}

export interface SubjectStat {
  subject_name: string
  full_score: number
  avg_score: number
  max_score: number
  count: number
}

export interface RiskStudent {
  student_name: string
  student_no: string
  avg_rate: number
}

export interface SubjectAlert {
  subject_name: string
  avg_score: number
  level: string
  desc: string
}

export interface ClassRankItem {
  class_name: string
  avg_rate: number
}

export interface ClassRanking {
  grade_name: string
  classes: ClassRankItem[]
}

export interface TrendInfo {
  direction: string
  description: string
}

export interface ExamTypeStats {
  monthly: number
  midterm: number
  final: number
}

export interface DashboardData {
  regression_alerts: any[]
  stats: DashboardStats
  recent_exams: RecentExam[]
  subject_stats: SubjectStat[]
  trend: TrendInfo
  risk_students: RiskStudent[]
  subject_alerts: SubjectAlert[]
  class_ranking: ClassRanking[]
  exam_type_stats: ExamTypeStats
}

export interface StudentTrend {
  subject_name: string
  scores: Array<{ exam_name: string; rate: number }>
}

export interface StudentScoreData {
  student_name: string
  exam_count: number
  overall_trend: string
  strengths: Array<{ subject_name: string; avg_rate: number }>
  weaknesses: Array<{ subject_name: string; avg_rate: number }>
  trends: StudentTrend[]
  exams: Array<{
    exam_name: string
    exam_date: string
    avg_rate: number
    subjects: Array<{ subject_name: string; score: number; rate: number }>
  }>
}

export interface ClassOverview {
  class_name: string
  grade_name: string
  student_count: number
  exam_count: number
  subject_stats: Array<{
    subject_name: string
    avg_score: number
    max_score: number
    min_score: number
    count: number
  }>
  exam_summary: Array<{
    exam_name: string
    exam_date: string
    avg_rate: number
  }>
}



// Score Summary types
export interface SubjectSummary {
  subject_id: string
  subject_name: string
  full_score: number
  avg_score: number
  max_score: number
  min_score: number
  median_score: number
  pass_count: number
  total_count: number
  pass_rate: number
  excellence_count: number
  excellence_rate: number
  fail_count: number
  fail_rate: number
  std_dev: number
}

export interface ClassSummaryItem {
  class_id: string
  class_name: string
  avg_score: number
  max_score: number
  min_score: number
  total_count: number
  rank: number
}

export interface ScoreSummaryResponse {
  exam_name: string
  grade_name: string
  total_students: number
  total_subjects: number
  subject_summaries: SubjectSummary[]
  class_summaries: ClassSummaryItem[]
  overall_avg: number
  overall_pass_rate: number
}
