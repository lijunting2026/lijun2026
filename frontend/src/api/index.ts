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

// ======== Auth ========
export const authApi = {
  login(data: { username: string; password: string }) {
    return api.post<LoginResponse>("/auth/login", data)
  },
  register(data: { username: string; password: string; display_name: string; role?: string }) {
    return api.post("/auth/register", data)
  },
}

// ======== Schools ========
export const schoolApi = {
  listGrades() {
    return api.get<Grade[]>("/schools/grades")
  },
  createGrade(data: { name: string; sort_order?: number }) {
    return api.post<Grade>("/schools/grades", data)
  },
  deleteGrade(id: string) {
    return api.delete(`/schools/grades/${id}`)
  },
  listClasses(gradeId?: string) {
    return api.get<ClassInfo[]>("/schools/classes", { params: { grade_id: gradeId } })
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

// ======== Subjects ========
export const subjectApi = {
  list() {
    return api.get<Subject[]>("/subjects")
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

// ======== Students ========
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

// ======== Exams ========
export const examApi = {
  list(params?: { grade_id?: string; exam_type?: string }) {
    return api.get<Exam[]>("/exams", { params })
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
  delete(id: string) {
    return api.delete(`/exams/${id}`)
  },
}

// ======== Scores ========
export const scoreApi = {
  list(params?: { exam_id?: string; class_id?: string; grade_id?: string; date_from?: string; date_to?: string; skip?: number; limit?: number }) {
    return api.get<PaginatedResponse<ScoreRecord>>("/scores", { params })
  },
  batchCreate(data: { exam_id: string; scores: Array<{ student_id: string; exam_subject_id: string; score_value: number; status?: string }> }) {
    return api.post("/scores/batch", data)
  },
}

// ======== Analysis ========
export const analysisApi = {
  examAnalysis(examId: string) {
    return api.get<any>("/analysis/exam/" + examId)
  },
  scoreDistribution(examSubjectId: string, bins?: number) {
    return api.get<any>("/analysis/distribution/" + examSubjectId, { params: { bins } })
  },
  getStudentAnalysis(studentId: string) {
    return api.get<any>("/analysis/student/" + studentId)
  },
  getStudentAdvice(studentId: string) {
    return api.get<any>("/analysis/student/" + studentId + "/advice")
  },
  dashboard() {
    return api.get<any>("/analysis/dashboard")
  },
  getClassAnalysis(classId: string) {
    return api.get<any>("/analysis/class/" + classId)
  },
}

// ======== User Management ========
export const userApi = {
  list() {
    return api.get<any[]>("/auth/users")
  },
  update(id: string, data: any) {
    return api.put<any>("/auth/users/" + id, data)
  },
  delete(id: string) {
    return api.delete("/auth/users/" + id)
  },
}

export default api
