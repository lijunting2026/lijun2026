<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue"
import { scoreApi, examApi, schoolApi } from "@/api"
import type { ScoreRecord, Exam, ClassInfo, Grade } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"

interface ExamGroup {
  exam_id: string
  exam_name: string
  subject_list: string[]
  student_list: Array<{
    student_id: string
    student_no: string
    student_name: string
    subjects: Record<string, number>
  }>
}

const allScores = ref<ScoreRecord[]>([])
const exams = ref<Exam[]>([])
const classes = ref<ClassInfo[]>([])
const grades = ref<Grade[]>([])
const loading = ref(false)
const selectedIds = ref<string[]>([])
const batchDeleting = ref(false)
const activeExamNames = ref<string[]>([])
const filterExamId = ref("")
const filterClassId = ref("")
const filterGradeId = ref("")
const dateFrom = ref("")
const dateTo = ref("")
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const groupedByExam = computed<ExamGroup[]>(() => {
  const examMap = new Map<string, {
    exam_id: string
    exam_name: string
    students: Map<string, { student_id: string; student_no: string; student_name: string; subjects: Record<string, number> }>
    subjectNames: Set<string>
  }>()

  if (!allScores.value || allScores.value.length === 0) return []
  for (const s of allScores.value) {
    const examId = s.exam_id || ""
    const examName = s.exam_name || ""
    if (!examMap.has(examId)) {
      examMap.set(examId, { exam_id: examId, exam_name: examName, students: new Map(), subjectNames: new Set() })
    }
    const eg = examMap.get(examId)!
    eg.subjectNames.add(s.subject_name || "")

    if (!eg.students.has(s.student_id)) {
      eg.students.set(s.student_id, {
        student_id: s.student_id,
        student_no: s.student_no || "",
        student_name: s.student_name || "",
        subjects: {},
      })
    }
    eg.students.get(s.student_id)!.subjects[s.subject_name || ""] = s.score_value
  }

  return Array.from(examMap.values()).map(eg => ({
    exam_id: eg.exam_id,
    exam_name: eg.exam_name,
    subject_list: Array.from(eg.subjectNames).filter(Boolean),
    student_list: Array.from(eg.students.values()),
  }))
})

async function loadExams() {
  try {
    const res = await examApi.list({ grade_id: filterGradeId.value || undefined })
    exams.value = res.data as any
  } catch { /* ignore */ }
}

async function loadGrades() {
  try {
    const res = await schoolApi.listGrades()
    grades.value = res.data as any
  } catch { /* ignore */ }
}

async function loadClasses() {
  try {
    const res = await schoolApi.listClasses()
    classes.value = res.data as any
  } catch { /* ignore */ }
}

async function loadScores() {
  page.value = 1
  loading.value = true
  allScores.value = []
  try {
    const res = await scoreApi.list({
      exam_id: filterExamId.value || undefined,
      class_id: filterClassId.value || undefined,
      grade_id: filterGradeId.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value,
    })
    total.value = res.data.total
    allScores.value = res.data.items
  } catch {
    ElMessage.error("获取成绩数据失败")
  } finally {
    loading.value = false
  }
}

function loadSizes() {
  page.value = 1
  loadScores()
}

onMounted(() => {
  loadExams()
  loadGrades()
  loadClasses()
  loadScores()
})

// Auto-expand first exam when data loads
watch(groupedByExam, (val) => {
  if (val.length > 0 && activeExamNames.value.length === 0) {
    activeExamNames.value = [val[0].exam_name]
  }
})
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <span style="font-weight: 600">成绩管理</span>
          <div style="display: flex; gap: 8px">
            <el-select v-model="filterGradeId" placeholder="筛选年级" clearable style="width: 140px" @change="loadScores">
              <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-select v-model="filterExamId" placeholder="选择考试" clearable filterable style="width: 180px" @change="loadScores">
              <el-option v-for="e in exams" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
            <el-select v-model="filterClassId" placeholder="筛选班级" clearable style="width: 140px" @change="loadScores">
              <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-date-picker v-model="dateFrom" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width: 150px" @change="loadScores" />
            <el-date-picker v-model="dateTo" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 150px" @change="loadScores" />
            <el-button type="primary" @click="() => $router.push('/scores/entry')">录入成绩</el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading" element-loading-text="加载中...">
        <el-collapse v-model="activeExamNames" v-if="groupedByExam.length > 0">
        <el-collapse-item v-for="eg in groupedByExam" :key="eg.exam_id" :title="eg.exam_name + ' (' + eg.student_list.length + '人)'" :name="eg.exam_name">
          <el-table :data="eg.student_list" stripe border size="small">
            <el-table-column prop="student_no" label="学号" width="140" />
            <el-table-column prop="student_name" label="姓名" width="100" />
            <el-table-column v-for="subj in eg.subject_list" :key="subj" :label="subj" width="90" align="center">
              <template #default="{ row }">
                <span :style="(row.subjects[subj] ?? 0) < 60 ? 'color: #F56C6C; font-weight: bold' : ''">
                  {{ row.subjects[subj] ?? "-" }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
      </div>

      <el-empty v-if="!loading && groupedByExam.length === 0" description="暂无数据，请选择考试和班级" />

      <!-- Pagination -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px" v-if="!loading && total > 0">
        <span style="color: #909399; font-size: 13px">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          @current-change="loadScores"
          @size-change="loadSizes"
        />
      </div>
    </el-card>
  </div>
</template>








