<script setup lang="ts">
import { ref, onMounted } from "vue"
import { examApi, schoolApi, subjectApi, scoringSchemeApi } from "@/api"
import type { Exam, Grade, Subject, ScoringScheme, ExamSubjectScoringConfig, ScoreLine } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"
import { Delete } from "@element-plus/icons-vue"

const exams = ref<Exam[]>([])
const grades = ref<Grade[]>([])
const subjects = ref<Subject[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const filterGradeId = ref("")
const filterType = ref("")
const editingId = ref<string | null>(null)
const form = ref({
  name: "",
  exam_date: "",
  exam_type: "月考",
  grade_id: "",
  subjects: [] as Array<{ subject_id: string; full_score: number; weight: number; id?: string; subject_name?: string }>,
})

async function loadData() {
  loading.value = true
  try {
    const [examRes, gradeRes, subjectRes] = await Promise.all([
      examApi.list({ grade_id: filterGradeId.value || undefined, exam_type: filterType.value || undefined }),
      schoolApi.listGrades(),
      subjectApi.list(),
    ])
    exams.value = examRes.data as any
    grades.value = gradeRes.data as any
    subjects.value = subjectRes.data as any
  } finally {
    loading.value = false
  }
}



function openEdit(exam: any) {
  form.value = {
    name: exam.name,
    exam_date: exam.exam_date || "",
    exam_type: exam.exam_type,
    grade_id: exam.grade_id,
    subjects: (exam.exam_subjects || []).map((s: any) => ({
      subject_id: s.subject_id,
      full_score: s.full_score,
      weight: s.weight,
      subject_name: s.subject_name,
    })),
  }
  editingId.value = exam.id
  dialogVisible.value = true
}

function openCreate() {
  form.value = {
    name: "",
    exam_date: "",
    exam_type: "月考",
    grade_id: "",
    subjects: [],
  }
  dialogVisible.value = true
}

function addSubject() {
  form.value.subjects.push({ subject_id: "", full_score: 100, weight: 1 })
}

function removeSubject(index: number) {
  form.value.subjects.splice(index, 1)
}

// Blueprint dialog
const blueprintDialog = ref(false)
const blueprintSubjectId = ref("")
const blueprintSubjectName = ref("")

function openBlueprintDialog(subjectId: string, subjectName: string) {
  blueprintSubjectId.value = subjectId
  blueprintSubjectName.value = subjectName
  blueprintDialog.value = true
}

async function save() {
  if (form.value.subjects.length === 0) {
    ElMessage.warning("请至少添加一个科目")
    return
  }
  try {
    if (editingId.value) {
      await examApi.update(editingId.value, form.value)
      ElMessage.success("更新成功")
    } else {
      await examApi.create(form.value)
      ElMessage.success("创建成功")
    }
    editingId.value = null
    dialogVisible.value = false
    await loadData()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "操作失败")
  }
}

async function remove(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该考试？")
    await examApi.delete(id)
    ElMessage.success("已删除")
    await loadData()
  } catch (err: any) {
    if (err !== "cancel") {
      ElMessage.error(err.response?.data?.detail || err.message || "删除失败")
    }
  }
}

function onDialogClose() {
  editingId.value = null
}

// ===== 赋分配置 =====
const scoringDialog = ref(false)
const scoringExamId = ref("")
const scoringConfigs = ref<ExamSubjectScoringConfig[]>([])
const schemes = ref<ScoringScheme[]>([])

async function openScoringDialog(exam: any) {
  scoringExamId.value = exam.id
  try {
    const [cfgRes, schemeRes] = await Promise.all([
      examApi.getScoringConfig(exam.id),
      scoringSchemeApi.list(),
    ])
    scoringConfigs.value = cfgRes.data as any
    schemes.value = schemeRes.data as any
    scoringDialog.value = true
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "加载失败")
  }
}

async function saveScoringConfig() {
  if (!scoringExamId.value) return
  try {
    await examApi.updateScoringConfig(scoringExamId.value, scoringConfigs.value.map((c) => ({
      exam_subject_id: c.exam_subject_id,
      scoring_type: c.scoring_type,
      scheme_id: c.scheme_id || null,
      conversion_mode: c.conversion_mode,
    })))
    ElMessage.success("赋分配置已保存")
    scoringDialog.value = false
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "保存失败")
  }
}

// ===== 分数线 =====
const scoreLineDialog = ref(false)
const scoreLineExamId = ref("")
const scoreLineExamSubjects = ref<Array<{ subject_id: string; subject_name: string | null }>>([])
const scoreLines = ref<ScoreLine[]>([])
const scoreLineForm = ref({ line_name: "", line_type: "total", subject_id: null as string | null, score_value: 0, source: "official" })

async function openScoreLineDialog(exam: any) {
  scoreLineExamId.value = exam.id
  scoreLineExamSubjects.value = (exam.exam_subjects || []).map((es: any) => ({
    subject_id: es.subject_id,
    subject_name: es.subject_name || "",
  }))
  scoreLines.value = []
  try {
    const res = await examApi.listScoreLines(exam.id)
    scoreLines.value = res.data as any
    scoreLineDialog.value = true
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "加载失败")
  }
}

function addScoreLine() {
  if (!scoreLineForm.value.line_name || !scoreLineForm.value.score_value) {
    ElMessage.warning("请填写线名和分数")
    return
  }
  const subjectName = scoreLineExamSubjects.value.find((es) => es.subject_id === scoreLineForm.value.subject_id)?.subject_name || ""
  scoreLines.value.push({
    id: "",
    exam_id: scoreLineExamId.value,
    line_name: scoreLineForm.value.line_name,
    line_type: scoreLineForm.value.line_type,
    subject_id: scoreLineForm.value.line_type === "subject" ? scoreLineForm.value.subject_id : null,
    subject_name: subjectName,
    score_value: scoreLineForm.value.score_value,
    source: scoreLineForm.value.source,
  })
  scoreLineForm.value = { line_name: "", line_type: "total", subject_id: null, score_value: 0, source: "official" }
}

function removeScoreLine(idx: number) {
  scoreLines.value.splice(idx, 1)
}

async function saveScoreLines() {
  try {
    await examApi.saveScoreLines(scoreLineExamId.value, scoreLines.value.map((l) => ({
      line_name: l.line_name,
      line_type: l.line_type,
      subject_id: l.subject_id,
      score_value: l.score_value,
      source: l.source,
    })))
    ElMessage.success("分数线已保存")
    scoreLineDialog.value = false
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "保存失败")
  }
}

async function importScoreLines(file: File) {
  if (!file) return
  try {
    const res = await examApi.importScoreLines(scoreLineExamId.value, file)
    ElMessage.success(res.data?.message || "导入成功")
    const reload = await examApi.listScoreLines(scoreLineExamId.value)
    scoreLines.value = reload.data as any
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "导入失败")
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>考试管理</span>
          <div style="display: flex; gap: 8px">
            <el-select v-model="filterGradeId" placeholder="筛选年级" clearable style="width: 140px" @change="loadData">
              <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-select v-model="filterType" placeholder="考试类型" clearable style="width: 130px" @change="loadData">
              <el-option label="月考" value="月考" />
              <el-option label="期中" value="期中" />
              <el-option label="期末" value="期末" />
              <el-option label="模拟考" value="模拟考" />
            </el-select>
            <el-button type="primary" @click="openCreate">创建考试</el-button>
          </div>
        </div>
      </template>
      <el-table :data="exams" v-loading="loading" stripe>
        <el-table-column prop="name" label="考试名称" min-width="160" />
        <el-table-column prop="exam_date" label="考试日期" width="120" />
        <el-table-column prop="exam_type" label="类型" width="80" />
        <el-table-column prop="grade_name" label="年级" width="100" />
        <el-table-column label="科目数" width="80">
          <template #default="{ row }">{{ row.exam_subjects?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" plain @click="openScoringDialog(row)">赋分</el-button>
            <el-button size="small" type="warning" plain @click="openScoreLineDialog(row)">分数线</el-button>
            <el-button size="small" type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑考试' : '创建考试'" width="600px" @close="onDialogClose">
      <el-form :model="form" label-width="80px">
        <el-form-item label="考试名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="考试日期">
          <el-date-picker v-model="form.exam_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="考试类型">
          <el-select v-model="form.exam_type">
            <el-option label="月考" value="月考" />
            <el-option label="期中" value="期中" />
            <el-option label="期末" value="期末" />
            <el-option label="模拟考" value="模拟考" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="form.grade_id" filterable>
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考试科目">
          <div>
            <div v-for="(s, idx) in form.subjects" :key="idx" style="display: flex; gap: 8px; margin-bottom: 8px">
              <el-select v-model="s.subject_id" placeholder="选择科目" filterable style="width: 160px">
                <el-option v-for="subj in subjects" :key="subj.id" :label="subj.name" :value="subj.id" />
              </el-select>
              <el-input-number v-model="s.full_score" placeholder="满分" :min="1" :max="300" style="width: 120px" />
              <el-input-number v-model="s.weight" placeholder="权重" :min="0.1" :step="0.1" :precision="1" style="width: 120px" />
              <el-button @click="removeSubject(idx)" :icon="Delete" circle />
              <el-button size="small" @click="openBlueprintDialog(s.id || '', s.subject_name || '')" :disabled="!s.subject_id">细目表</el-button>
            </div>
            <el-button size="small" @click="addSubject">+ 添加科目</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">{{ editingId ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="scoringDialog" title="赋分配置" width="720px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px"
        title="赋分科目（选考）需选择方案；原始分科目（语数外）无需配置。自动=系统按方案换算，手动=人工录入赋分，可随时切换。" />
      <el-table :data="scoringConfigs" stripe border size="small">
        <el-table-column prop="subject_name" label="科目" />
        <el-table-column label="计分方式" width="150">
          <template #default="{ row }">
            <el-select v-model="row.scoring_type" size="small">
              <el-option label="原始分" value="raw" />
              <el-option label="赋分" value="converted" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="赋分方案" width="220">
          <template #default="{ row }">
            <el-select v-model="row.scheme_id" size="small" :disabled="row.scoring_type !== 'converted'" placeholder="选择方案" clearable>
              <el-option v-for="sc in schemes" :key="sc.id" :label="sc.name" :value="sc.id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="换算模式" width="150">
          <template #default="{ row }">
            <el-select v-model="row.conversion_mode" size="small" :disabled="row.scoring_type !== 'converted'">
              <el-option label="自动换算" value="auto" />
              <el-option label="手动赋分" value="manual" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="scoringDialog = false">取消</el-button>
        <el-button type="primary" @click="saveScoringConfig">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="scoreLineDialog" title="分数线" width="780px">
      <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
        <el-input v-model="scoreLineForm.line_name" placeholder="线名（如：本科线/特控线）" style="width: 150px" />
        <el-select v-model="scoreLineForm.line_type" style="width: 110px">
          <el-option label="总分线" value="total" />
          <el-option label="单科线" value="subject" />
        </el-select>
        <el-select v-model="scoreLineForm.subject_id" placeholder="科目" clearable style="width: 120px" :disabled="scoreLineForm.line_type !== 'subject'">
          <el-option v-for="es in scoreLineExamSubjects" :key="es.subject_id" :label="es.subject_name" :value="es.subject_id" />
        </el-select>
        <el-input-number v-model="scoreLineForm.score_value" :min="0" :max="900" style="width: 120px" />
        <el-select v-model="scoreLineForm.source" style="width: 100px">
          <el-option label="官方" value="official" />
          <el-option label="参考" value="reference" />
          <el-option label="自定义" value="custom" />
        </el-select>
        <el-button type="primary" size="small" @click="addScoreLine">添加</el-button>
      </div>
      <el-table :data="scoreLines" stripe border size="small">
        <el-table-column prop="line_name" label="线名" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">{{ row.line_type === 'total' ? '总分线' : '单科线' }}</template>
        </el-table-column>
        <el-table-column prop="subject_name" label="科目" width="100" />
        <el-table-column prop="score_value" label="分数" width="80" />
        <el-table-column prop="source" label="来源" width="80" />
        <el-table-column label="操作" width="70">
          <template #default="{ $index }">
            <el-button size="small" type="danger" @click="removeScoreLine($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 12px">
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="(f: any) => importScoreLines(f.raw)" accept=".xlsx,.xls">
          <el-button size="small" type="warning" plain>Excel 批量导入分数线</el-button>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="scoreLineDialog = false">取消</el-button>
        <el-button type="primary" @click="saveScoreLines">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

