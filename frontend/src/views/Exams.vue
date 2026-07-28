<script setup lang="ts">
import { ref, onMounted } from "vue"
import { examApi, schoolApi, subjectApi } from "@/api"
import type { Exam, Grade, Subject } from "@/types"
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
  subjects: [] as Array<{ subject_id: string; full_score: number; weight: number }>,
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
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
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
  </div>
</template>

