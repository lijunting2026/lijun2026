import axios from "axios"
import type {
  LoginResponse,
  Grade,
  ClassInfo,
  Subject,
  Student,
  Exam,
  ExamSubject,
  ScoreRecord,
  ExamAnalysis,
  DistributionResponse,
  PaginatedResponse,
  TransferRequest,
  TransferResponse,
  StudentScoreData,
  DashboardData,
  ClassOverview,
  ScoringScheme,
  ScoringBracket,
  ExamSubjectScoringConfig,
  ScoreLine,
  LineStats,
  OnePointTable,
} from "@/types"

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
})

// Request interceptor to add token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor to handle 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      window.location.hash = "#/login"
    }
    return Promise.reject(err)
  }
)

// =-======= Auth ==========
export const authApi = {
  login(data: { username: string; password: string }) {
    return api.post<LoginResponse>("/auth/login", data)
  },
  register(data: { username: string; password: string; display_name: string; role?: string }) {
    return api.post("/auth/register", data)
  },
  changePassword(data: { old_password: string; new_password: string }) {
    return api.post("/auth/change-password", data)
  },
}

// ========= Schools ===========
export const schoolApi = {
  listGrades() {
    return api.get<Grade>("/schools/grades")
  },
  createGrade(data: { name: string; sort_order?: number }) {
    return api.post<Grade>("/schools/grades", data)
  },
  deleteGrade(id: string) {
    return api.delete(`/schools/grades/${id}`)
  },
  listClasses(gradeId?: string) {
    return api.get<ClassInfo>("/schools/classes", { params: { grade_id: gradeId } })
  },
  createClass(data: { name: string; grade_id: string }) {
    return api.post<ClassInfo>("/schools/classes", data)
  },
  deleteClass(id: string) {
    return api.delete(`/schools/classes/${id}`)
  },
  updateGrade(id: string, data: { name: string; sort_order?: number }) {
    return api.put<Grade>(`/schools/grades/${id}`, data)
  },
  updateClass(id: string, data: { name: string; grade_id: string }) {
    return api.put<ClassInfo>(`/schools/classes/${id}`, data)
  },
}

// ========== Subjects ===========
export const subjectApi = {
  list() {
    return api.get<Subject>("/subjects")
  },
  create(data: { name: string; full_score?: number; sort_order?: number }) {
    return api.post<Subject>("/subjects", data)
  },
  update(id: string, data: { name: string; full_score?: number; sort_order?: number }) {
    return api.put<Subject>(`/subjects/${id}`, data)
  },
  delete(id: string) {
    return api.delete(`/subjects/${id}`)
  },
}

// ========== Students ===========
export const studentApi = {
  list(params?: { class_id?: string; keyword?: string; skip?: number; limit?: number }) {
    return api.get<PaginatedResponse<Student>>("/students", { params })
  },
  create(data: { student_no: string; name: string; gender?: string; class_id: string }) {
    return api.post<Student>("/students", data)
  },
  importBatch(data: { students: Array<{ student_no: string; name: string; gender?: string; class_id: string }> }) {
    return api.post("/students/import", data)
  },
  update(id: string, data: { student_no: string; name: string; gender?: string; class_id: string }) {
    return api.put<Student>("/students/" + id, data)
  },
  delete(id: string) {
    return api.delete(`/students/${id}`)
  },
  transfer(id: string, data: TransferRequest) {
    return api.post<TransferResponse>("/students/" + id + "/transfer", data)
  },
}

// ========== Exams ===========
export const examApi = {
  list(params?: { grade_id?: string; exam_type?: string }) {
    return api.get<Exam>("/exams", { params })
  },
  get(id: string) {
    return api.get<Exam>(`/exams/${id}`)
  },
  create(data: {
    name: string
    exam_date: string
    exam_type: string
    grade_id: string
    subjects: Array<{ subject_id: string; full_score: number; weight?: number }>
  }) {
    return api.post<Exam>("/exams", data)
  },
  update(id: string, data: {
    name: string
    exam_date: string
    exam_type: string
    grade_id: string
    subjects: Array<{ subject_id: string; full_score: number; weight?: number }>
  }) {
    return api.put<Exam>("/exams/" + id, data)
  },
  delete(id: string) {
    return api.delete(`/exams/${id}`)
  },
  getScoringConfig(id: string) {
    return api.get<ExamSubjectScoringConfig[]>(`/exams/${id}/scoring-config`)
  },
  updateScoringConfig(id: string, subjects: Array<{ exam_subject_id: string; scoring_type: string; scheme_id?: string | null; conversion_mode: string }>) {
    return api.put(`/exams/${id}/scoring-config`, { subjects })
  },
  listScoreLines(id: string) {
    return api.get<ScoreLine[]>(`/exams/${id}/score-lines`)
  },
  saveScoreLines(id: string, lines: Array<{ line_name: string; line_type: string; subject_id?: string | null; score_value: number; source?: string }>) {
    return api.post(`/exams/${id}/score-lines`, lines)
  },
  importScoreLinesUrl(id: string) {
    return `/api/v1/exams/${id}/score-lines/import`
  },
  importScoreLines(id: string, file: File) {
    const fd = new FormData()
    fd.append("file", file)
    return api.post(`/exams/${id}/score-lines/import`, fd)
  },
}

// ========== Scores ===========
export const scoreApi = {
  batchDelete(data: { ids: string[] }) {
    return api.post("/scores/batch-delete", data)
  },
  list(params?: { exam_id?: string; class_id?: string; grade_id?: string; date_from?: string; date_to?: string; skip?: number; limit?: number }) {
    return api.get<PaginatedResponse<ScoreRecord>>("/scores", { params })
  },
  batchCreate(data: { exam_id: string; scores: Array<{ student_id: string; exam_subject_id: string; score_value: number; status?: string; converted_score?: number | null }> }) {
    return api.post("/scores/batch", data)
  },
  convertSubject(examSubjectId: string, force = false) {
    return api.post(`/scores/${examSubjectId}/convert`, null, { params: { force } })
  },
}

// ========== Scoring Schemes ===========
export const scoringSchemeApi = {
  list(presetOnly = false) {
    return api.get<ScoringScheme[]>("/scoring-schemes", { params: { preset_only: presetOnly } })
  },
  create(data: { name: string; description?: string; brackets: ScoringBracket[]; sort_order?: number }) {
    return api.post<ScoringScheme>("/scoring-schemes", data)
  },
  update(id: string, data: { name?: string; description?: string; brackets?: ScoringBracket[]; sort_order?: number }) {
    return api.put<ScoringScheme>(`/scoring-schemes/${id}`, data)
  },
  remove(id: string) {
    return api.delete(`/scoring-schemes/${id}`)
  },
}

// ========== Analysis ===========
export const reportApi = {
  examWord(examId: string) {
    return `/api/v1/report/word/${examId}`
  },
  examPdf(examId: string) {
    return `/api/v1/report/pdf/${examId}`
  },
  classWord(classId: string) {
    return `/api/v1/report/word/class/${classId}`
  },
  classPdf(classId: string) {
    return `/api/v1/report/pdf/class/${classId}`
  },
  studentWord(studentId: string) {
    return `/api/v1/report/word/student/${studentId}`
  },
  studentPdf(studentId: string) {
    return `/api/v1/report/pdf/student/${studentId}`
  },
  // Error notebook
  errorNotebook(studentId: string, examId?: string) {
    return api.get<any>(`/report/error-notebook/${studentId}`, { params: { exam_id: examId } })
  },
  errorNotebookUrl(studentId: string, examId?: string) {
    let url = `/api/v1/report/error-notebook/${studentId}/export`
    if (examId) url += `?exam_id=${examId}`
    return url
  },
  // Practice generation
  generatePractice(studentId: string, data: { question_count?: number; include_types?: string[] }) {
    return api.post<any>(`/report/practice/${studentId}`, data)
  },
}

export const analysisApi = {
  examAnalysis(examId: string, scoreMode = "auto") {
    return api.get<ExamAnalysis>("/analysis/exam/" + examId, { params: { score_mode: scoreMode } })
  },
  lineStats(examId: string, scoreMode = "auto") {
    return api.get<LineStats>("/analysis/exam/" + examId + "/line-stats", { params: { score_mode: scoreMode } })
  },
  onePointTable(examId: string, scoreMode = "auto") {
    return api.get<OnePointTable>("/analysis/exam/" + examId + "/one-point-table", { params: { score_mode: scoreMode } })
  },
  scoreDistribution(examSubjectId: string, bins?: number) {
    return api.get<DistributionResponse>("/analysis/distribution/" + examSubjectId, { params: { bins } })
  },
  getStudentAnalysis(studentId: string) {
    return api.get<StudentScoreData>("/analysis/student/" + studentId)
  },
  getStudentAdvice(studentId: string) {
    return api.get<any>("/analysis/student/" + studentId + "/advice")
  },
  dashboard() {
    return api.get<DashboardData>("/analysis/dashboard")
  },
  getClassAnalysis(classId: string) {
    return api.get<ClassOverview>("/analysis/class/" + classId)
  },
  // Knowledge point analysis
  getExamKnowledgeAnalysis(examId: string) {
    return api.get<any>("/analysis/exam/" + examId + "/knowledge")
  },
  getClassKnowledgeAnalysis(classId: string, examId?: string) {
    return api.get<any>("/analysis/class/" + classId + "/knowledge", { params: { exam_id: examId } })
  },
  getStudentKnowledgeAnalysis(studentId: string) {
    return api.get<any>("/analysis/student/" + studentId + "/knowledge")
  },
}

// ========== User Management ===========
export const userApi = {
  list() {
    return api.get<any[]>("/auth/users")
  },
  update(id: string, data: Record<string, any>) {
    return api.put("/auth/users/" + id, data)
  },
  delete(id: string) {
    return api.delete("/auth/users/" + id)
  },
}

export default api

// ========== Knowledge Points ===========
export const knowledgeApi = {
  getTree(subjectId: string) {
    return api.get<any[]>(`/knowledge-points/tree/${subjectId}`)
  },
  list(subjectId: string) {
    return api.get<any[]>(`/knowledge-points/${subjectId}`)
  },
  create(data: { subject_id: string; name: string; parent_id?: string; sort_order?: number; description?: string }) {
    return api.post("/knowledge-points/", data)
  },
  update(id: string, data: { name?: string; parent_id?: string; sort_order?: number; description?: string }) {
    return api.put(`/knowledge-points/${id}`, data)
  },
  delete(id: string) {
    return api.delete(`/knowledge-points/${id}`)
  },
  getExamQuestions(examSubjectId: string) {
    return api.get<any[]>(`/knowledge-points/exam-questions/${examSubjectId}`)
  },
  importBlueprint(data: {
    exam_subject_id: string
    difficulty?: number
    discrimination?: number
    reliability?: number
    questions: Array<{
      question_no: number
      question_type: string
      full_score: number
      knowledge_point_id?: string
      difficulty?: number
      cognitive_level: string
      estimated_pass_rate?: number
      content: string
    }>
  }) {
    return api.post("/knowledge-points/import-blueprint", data)
  },
}

export const knowledgeImportApi = {
  templateUrl() {
    return "/api/v1/knowledge-points/import/template.xlsx"
  },
  importExcel(subjectId: string, file: File, sourceName?: string) {
    const fd = new FormData()
    fd.append("file", file)
    fd.append("subject_id", subjectId)
    if (sourceName) fd.append("source_name", sourceName)
    return api.post("/knowledge-points/import/excel", fd)
  },
  importText(subjectId: string, text: string, sourceName?: string, sourceType = "curriculum") {
    return api.post("/knowledge-points/import/text", {
      subject_id: subjectId,
      source_name: sourceName || "",
      text,
      source_type: sourceType,
    })
  },
  importAi(subjectId: string, file: File, sourceName?: string) {
    const fd = new FormData()
    fd.append("file", file)
    fd.append("subject_id", subjectId)
    if (sourceName) fd.append("source_name", sourceName)
    return api.post("/knowledge-points/import/ai", fd)
  },
  commitPreview(subjectId: string, items: any[], sourceName?: string, sourceType = "curriculum", importMode = "rules") {
    return api.post("/knowledge-points/import/preview", {
      subject_id: subjectId,
      source_name: sourceName || "",
      source_type: sourceType,
      import_mode: importMode,
      items,
    })
  },
  listSources(subjectId?: string) {
    return api.get<any[]>("/knowledge-points/sources", { params: { subject_id: subjectId } })
  },
  deleteSource(id: string) {
    return api.delete(`/knowledge-points/sources/${id}`)
  },
}


