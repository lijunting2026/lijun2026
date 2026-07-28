<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { examApi, schoolApi, studentApi, scoreApi } from "@/api"
import type { Exam, Student, ClassInfo } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"

const router = useRouter()
const loading = ref(false)
const saving = ref(false)

const exams = ref<Exam[]>([])
const selectedExam = ref<Exam | null>(null)
const examSubjects = computed(() => selectedExam.value?.exam_subjects || [])

const classes = ref<ClassInfo[]>([])
const selectedClassId = ref("")

const students = ref<Student[]>([])
const scoreMap = ref<Record<string, Record<string, number>>>({})

const importDialogVisible = ref(false)
const importFile = ref<File | null>(null)
const importResult = ref("")
const importing = ref(false)

const exportClassId = ref("")

async function loadExams() { const r = await examApi.list(); exams.value = r.data }
async function loadClasses() { const r = await schoolApi.listClasses(); classes.value = r.data }

async function onExamChange() {
  if (!selectedExam.value) return
  if (selectedExam.value.grade_id) {
    const r = await schoolApi.listClasses(selectedExam.value.grade_id)
    classes.value = r.data
  } else { await loadClasses() }
  selectedClassId.value = ""; students.value = []; scoreMap.value = {}
}

async function loadStudents() {
  if (!selectedExam.value) return; loading.value = true
  try {
    const p: Record<string, string> = {}
    if (selectedClassId.value) p.class_id = selectedClassId.value
    const r = await studentApi.list(p)
    students.value = r.data.items
    const m: Record<string, Record<string, number>> = {}
    for (const s of r.data.items) {
      m[s.id] = {}
      for (const es of examSubjects.value) m[s.id][es.id] = 0
    }
    scoreMap.value = m
    if (p.class_id) {
      try {
        const sr = await scoreApi.list({ exam_id: selectedExam.value.id, class_id: p.class_id })
        for (const rec of (sr.data.items || sr.data)) { if (m[rec.student_id]) m[rec.student_id][rec.exam_subject_id] = rec.score_value }
      } catch {}
    }
  } finally { loading.value = false }
}

function focusNext(evt: Event, sid: string, idx: number) {
  if (!evt.target || idx >= examSubjects.value.length - 1) return
  const nid = examSubjects.value[idx + 1].id
  const el = document.getElementById("score-" + sid + "-" + nid) as HTMLInputElement
  if (el) el.focus()
}

async function saveScores() {
  if (!selectedExam.value) { ElMessage.warning("请先选择考试"); return }
  if (students.value.length === 0) { ElMessage.warning("当前没有学生数据"); return }
  await ElMessageBox.confirm("确定保存所有成绩？已有成绩将被覆盖。", "确认保存")
  saving.value = true
  try {
    const scores: Array<{ student_id: string; exam_subject_id: string; score_value: number }> = []
    for (const s of students.value) {
      for (const es of examSubjects.value) {
        const v = scoreMap.value[s.id]?.[es.id] ?? 0
        if (v > 0) scores.push({ student_id: s.id, exam_subject_id: es.id, score_value: v })
      }
    }
    if (scores.length === 0) { ElMessage.warning("没有可保存的成绩，请先输入分数"); return }
    await scoreApi.batchCreate({ exam_id: selectedExam.value.id, scores })
    ElMessage.success("成功保存 " + scores.length + " 条成绩")
  } catch (err: any) { ElMessage.error(err.response?.data?.detail || "保存失败") }
  finally { saving.value = false }
}

function goBack() { router.push("/exam-group/scores") }

async function downloadTemplate(exportAll: any) {
  if (!selectedExam.value) { ElMessage.warning("请先选择考试"); return }
  const p = new URLSearchParams({ exam_id: selectedExam.value.id })
  if (exportAll !== true && typeof exportAll === "string") p.set("subject_id", exportAll)
  if (exportClassId.value) p.set("class_id", exportClassId.value)
  try {
    const token = localStorage.getItem("token") || ""
    const res = await fetch("/api/v1/scores/export-template?" + p.toString(), { headers: { Authorization: "Bearer " + token } })
    if (!res.ok) { const e = await res.json(); ElMessage.error(e.detail || "下载模板失败"); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a"); a.href = url
    a.download = (exportAll === true) ? (selectedExam.value.name + "_全部科目_成绩模板.xlsx") : (selectedExam.value.name + "_模板.xlsx")
    a.click(); URL.revokeObjectURL(url); ElMessage.success("模板已下载")
  } catch (err: any) { ElMessage.error("下载模板失败: " + (err.message || "")) }
}

function openImportDialog() { importDialogVisible.value = true; importResult.value = ""; importFile.value = null }
function onFileChange(file: any) { importFile.value = file || null }
async function submitImport() {
  if (!selectedExam.value || !importFile.value) { ElMessage.warning("请先选择考试和文件"); return }
  importing.value = true; importResult.value = ""
  try {
    const fd = new FormData(); fd.append("exam_id", selectedExam.value.id); fd.append("file", importFile.value)
    const token = localStorage.getItem("token") || ""
    const res = await fetch("/api/v1/scores/import", { method: "POST", headers: { Authorization: "Bearer " + token }, body: fd })
    const data = await res.json()
    if (!res.ok) { ElMessage.error(data.detail || "导入失败"); return }
    importResult.value = data.message; ElMessage.success(data.message); loadStudents()
  } catch (err: any) { ElMessage.error("导入失败: " + (err.message || "")) }
  finally { importing.value = false }
}

onMounted(() => { loadExams(); loadClasses() })
</script>

<template>
<div><el-card shadow="hover">
<template #header><div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px"><span style="font-weight:600">成绩录入</span><div style="display:flex;gap:8px">
<el-dropdown @command="downloadTemplate" v-if="selectedExam"><el-button>导出模板<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
<template #dropdown><el-dropdown-menu>
<el-dropdown-item :command="true">全部科目_成绩模板</el-dropdown-item>
<el-dropdown-item v-for="es in examSubjects" :key="es.id" :command="es.subject_id">仅_{{ es.subject_name }}</el-dropdown-item>
</el-dropdown-menu></template></el-dropdown>
<el-button v-if="selectedExam" @click="openImportDialog">导入成绩</el-button>
<el-button @click="goBack">取消</el-button>
</div></div></template>
<el-form :inline="true" style="margin-bottom:16px">
<el-form-item label="考试"><el-select v-model="selectedExam" value-key="id" placeholder="请选择考试" filterable style="width:280px" @change="onExamChange"><el-option v-for="e in exams" :key="e.id" :label="e.name" :value="e" /></el-select></el-form-item>
<el-form-item label="班级"><el-select v-model="selectedClassId" placeholder="选择班级（可选）" clearable filterable style="width:200px" @change="loadStudents"><el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
<el-form-item><el-button type="primary" :disabled="!selectedExam" @click="loadStudents">加载学生</el-button></el-form-item>
</el-form>
<template v-if="selectedExam && students.length > 0">
<el-alert title="分数大于 0 才会保存，留空或填 0 则跳过" type="info" :closable="false" show-icon style="margin-bottom:12px" />
<div style="overflow-x:auto">
<el-table :data="students" v-loading="loading" stripe border max-height="600">
<el-table-column type="index" label="#" width="50" fixed />
<el-table-column prop="student_no" label="学号" width="140" fixed />
<el-table-column prop="name" label="姓名" width="100" fixed />
<el-table-column v-for="(es, idx) in examSubjects" :key="es.id" :label="es.subject_name" :width="140">
<template #default="{ row }"><el-input-number :id="'score-' + row.id + '-' + es.id" v-model="scoreMap[row.id][es.id]" :min="0" :max="es.full_score" :step="0.5" :precision="1" size="small" controls-position="right" style="width:120px" @keyup.enter="focusNext($event, row.id, idx)" /><div style="font-size:11px;color:#909399">满分 {{ es.full_score }}</div></template>
</el-table-column>
</el-table></div>
<div style="margin-top:16px;text-align:right"><el-button @click="goBack" style="margin-right:8px">取消</el-button><el-button type="primary" :loading="saving" @click="saveScores" size="large">保存成绩</el-button></div>
</template>
<el-empty v-else-if="selectedExam && !loading" description="点击「加载学生」来开始录入成绩" />
<el-empty v-else-if="!selectedExam" description="请先选择一场考试" />
</el-card>
<el-dialog v-model="importDialogVisible" title="导入成绩" width="500px" :close-on-click-modal="false">
<div style="margin-bottom:16px"><p style="color:#909399;margin-bottom:8px">请先通过「导出模板」下载 Excel 模板，填写成绩后上传。</p>
<el-upload drag :auto-upload="false" :show-file-list="true" accept=".xlsx,.xls" :on-change="(u:any) => onFileChange(u.raw)" :limit="1">
<el-icon class="el-icon--upload" style="font-size:48px"><UploadFilled /></el-icon>
<div class="el-upload__text">将 Excel 文件拖到此处，或<em>点击选择</em></div>
<template #tip><div class="el-upload__tip">仅支持 .xlsx 格式</div></template>
</el-upload></div>
<div v-if="importResult" style="margin-bottom:12px"><el-alert :title="importResult" type="success" :closable="true" show-icon /></div>
<template #footer><el-button @click="importDialogVisible = false">取消</el-button><el-button type="primary" :loading="importing" :disabled="!importFile" @click="submitImport">开始导入</el-button></template>
</el-dialog>
</div>
</template>