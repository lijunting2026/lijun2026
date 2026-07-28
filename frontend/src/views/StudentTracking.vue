<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from "vue"
import { studentApi, schoolApi, analysisApi } from "@/api"
import type { Student, ClassInfo } from "@/types"
import { ElMessage } from "element-plus"
import AIChatDialog from "@/components/AIChatDialog.vue"

const students = ref<Student[]>([])
const classes = ref<ClassInfo[]>([])
const selectedStudentId = ref("")
const filterClassId = ref("")
const keyword = ref("")
const loading = ref(false)
const aiChatVisible = ref(false)
const errorMsg = ref("")
const studentData = ref<any>(null)
const adviceData = ref<any>(null)

const chartTrend = ref<any>(null)
const chartRadar = ref<any>(null)
const trendOptions = ref<any>({})
const radarOptions = ref<any>({})

async function loadClasses() {
  try {
    const res = await schoolApi.listClasses()
    classes.value = res.data
  } catch {
    console.error("Failed to load classes")
  }
}

async function loadStudents() {
  loading.value = true
  try {
    const res = await studentApi.list({
      class_id: filterClassId.value || undefined,
      keyword: keyword.value || undefined,
    })
    students.value = res.data.items || []
  } catch {
    console.error("Failed to load students")
  } finally {
    loading.value = false
  }
}

async function search() {
  selectedStudentId.value = ""
  studentData.value = null
  adviceData.value = null
  errorMsg.value = ""
  await loadStudents()
}

async function selectStudent() {
  if (!selectedStudentId.value) return
  loading.value = true
  try {
    const [sRes, aRes] = await Promise.all([
      analysisApi.getStudentAnalysis(selectedStudentId.value),
      analysisApi.getStudentAdvice(selectedStudentId.value),
    ])
    studentData.value = sRes.data
    adviceData.value = aRes.data
    buildCharts()
  } catch (err: any) {
    console.error("StudentTracking error:", err)
    errorMsg.value = err?.response?.data?.detail || err?.message || "获取学情数据失败"
    ElMessage.error(errorMsg.value)
  } finally {
    loading.value = false
  }
}

function buildCharts() {
  try {
    if (!studentData.value) return

    const exams = studentData.value.exams || []
    const subjects = studentData.value.trends || []

    // Trend line chart
    const series = []
    const examNames = exams.map((e: any) => e.exam_name)

    for (const t of subjects) {
      if (!t.scores || !Array.isArray(t.scores)) continue
      const data = examNames.map((name: string) => {
        const found = t.scores.find((s: any) => s && s.exam_name === name)
        return found ? found.rate : null
      })
      if (data.some((v: any) => v !== null)) {
        series.push({ name: t.subject_name, type: "line", data, smooth: true })
      }
    }

    if (series.length > 0) {
      trendOptions.value = {
        tooltip: { trigger: "axis" },
        legend: { top: 0, type: "scroll" },
        grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
        xAxis: { type: "category", data: examNames, axisLabel: { rotate: 15, fontSize: 10 } },
        yAxis: { type: "value", name: "得分率(%)", max: 100 },
        series,
      }
    }

    // Radar chart - latest scores
    if (exams.length > 0) {
      const latest = exams[exams.length - 1]
      if (latest && latest.subjects) {
        const indicators = latest.subjects.map((s: any) => ({ name: s.subject_name, max: 100 }))
        const values = latest.subjects.map((s: any) => s.rate || 0)
        if (indicators.length > 0) {
          radarOptions.value = {
            tooltip: { trigger: "item" },
            radar: { indicator: indicators, radius: "60%" },
            series: [{
              type: "radar",
              data: [{ value: values, name: "得分率", areaStyle: { color: "rgba(64,158,255,0.2)" }, lineStyle: { color: "#409EFF" }, itemStyle: { color: "#409EFF" } }],
            }],
          }
        }
      }
    }

    nextTick(() => window.dispatchEvent(new Event("resize")))
  } catch (chartErr) {
    console.error("Chart error:", chartErr)
  }
}

function getTrendColor(dir: string) {
  return dir === "up" ? "#67C23A" : dir === "down" ? "#F56C6C" : "#909399"
}

function getPriorityType(p: string) {
  return p === "high" ? "warning" : p === "medium" ? "primary" : "info"
}


async function exportStudentData() {
  if (!selectedStudentId.value) return
  await downloadBlob("/api/v1/analysis/student/" + selectedStudentId.value + "/export", (studentData.value?.student_name || "学情") + "_学情分析.xlsx")
}

async function exportStudentWord() {
  if (!selectedStudentId.value) return
  await downloadBlob("/api/v1/report/word/student/" + selectedStudentId.value, (studentData.value?.student_name || "学情") + "_学情报告.docx")
}

async function exportStudentPdf() {
  if (!selectedStudentId.value) return
  await downloadBlob("/api/v1/report/pdf/student/" + selectedStudentId.value, (studentData.value?.student_name || "学情") + "_学情报告.pdf")
}

async function downloadBlob(url: string, filename: string) {
  const token = localStorage.getItem("token") || ""
  const res = await fetch(url, { headers: { Authorization: "Bearer " + token } })
  if (!res.ok) { ElMessage.error("导出失败"); return }
  const blob = await res.blob()
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob)
  link.download = filename; link.click()
  URL.revokeObjectURL(link.href)
  ElMessage.success("导出成功")
}

onMounted(() => {
  loadClasses()
  loadStudents()
})
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <span style="font-weight: 600">学情跟踪</span>
          <div style="display: flex; gap: 8px">
            <el-select v-model="filterClassId" placeholder="筛选班级" clearable style="width: 160px" @change="search">
              <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-input v-model="keyword" placeholder="搜索姓名/学号" clearable style="width: 180px" @keyup.enter="search" />
            <el-button @click="search">搜索</el-button>
            <el-select v-model="selectedStudentId" placeholder="选择学生" filterable style="width: 220px" @change="selectStudent">
              <el-option v-for="s in students" :key="s.id" :label="s.name + ' (' + s.student_no + ')'" :value="s.id" />
            </el-select>
              <el-button v-if="studentData" type="success" @click="exportStudentData">Excel</el-button>
              <el-button v-if="studentData" type="primary" @click="exportStudentWord">Word</el-button>
              <el-button v-if="studentData" type="danger" @click="exportStudentPdf">PDF</el-button>
          </div>
        </div>
      </template>

      <template v-if="studentData">
        <el-descriptions title="学生信息" :column="4" border style="margin-bottom: 16px">
          <el-descriptions-item label="姓名">{{ studentData.student_name }}</el-descriptions-item>
          <el-descriptions-item label="学号">{{ studentData.student_no }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ studentData.class_name }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ studentData.grade_name }}</el-descriptions-item>
          <el-descriptions-item label="考试次数">{{ studentData.exam_count }}</el-descriptions-item>
          <el-descriptions-item label="总体趋势">
            <el-tag :type="studentData.overall_trend === '持续进步' ? 'success' : studentData.overall_trend === '有所下滑' ? 'danger' : 'info'">
              {{ studentData.overall_trend }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-row :gutter="16">
          <el-col :span="14">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">各科成绩趋势</span></template>
              <v-chart v-if="trendOptions.series?.length" :option="trendOptions" autoresize style="height: 340px" />
              <el-empty v-else description="暂无趋势数据" />
            </el-card>
          </el-col>
          <el-col :span="10">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">最近一次得分率</span></template>
              <v-chart v-if="radarOptions.series" :option="radarOptions" autoresize style="height: 340px" />
              <el-empty v-else description="暂无数据" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Strengths & Weaknesses -->
        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header><span style="font-weight: 600; color: #67C23A">优势科目</span></template>
              <div v-for="s in studentData.strengths" :key="s.subject_name" style="margin-bottom: 8px">
                <el-tag type="success" style="margin-right: 8px">{{ s.subject_name }}</el-tag>
                <span>平均得分率" {{ s.avg_rate }}% / 最新" {{ s.latest_rate }}%</span>
              </div>
              <el-empty v-if="!studentData.strengths?.length" description="暂无数据" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header><span style="font-weight: 600; color: #F56C6C">薄弱科目</span></template>
              <div v-for="s in studentData.weaknesses" :key="s.subject_name" style="margin-bottom: 8px">
                <el-tag type="danger" style="margin-right: 8px">{{ s.subject_name }}</el-tag>
                <span>平均得分率" {{ s.avg_rate }}% / 最新" {{ s.latest_rate }}%</span>
              </div>
              <el-empty v-if="!studentData.weaknesses?.length" description="暂无数据" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Subject trends -->
        <el-card shadow="hover" style="margin-top: 16px">
          <template #header><span style="font-weight: 600">各科趋势详情</span></template>
          <el-table :data="studentData.trends" stripe>
            <el-table-column prop="subject_name" label="科目" width="120" />
            <el-table-column label="趋势" width="120">
              <template #default="{ row }">
                <el-tag :type="row.direction === 'up' ? 'success' : row.direction === 'down' ? 'danger' : 'info'" size="small">
                  {{ row.description }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="历次得分率">
              <template #default="{ row }">
                <span v-for="(s, i) in row.scores" :key="i" style="margin-right: 12px">
                  {{ s.exam_name }}: {{ s.rate }}%
                </span>
                <span v-if="!row.scores?.length">暂无</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        

        <!-- AI Advice -->
        <el-card shadow="hover" style="margin-top: 16px" v-if="adviceData">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px">
              <span style="font-weight: 600">AI 学习建议</span>
              <el-tag size="small" type="warning">基于数据分析生成</el-tag>
              <span style="font-size: 12px; color: #909399">生成时间: {{ adviceData.generated_at }}</span>
            </div>
          </template>
          <div v-for="(item, idx) in adviceData.advice_items" :key="idx" style="margin-bottom: 12px; padding: 12px; background: #f5f7fa; border-radius: 8px">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px">
              <el-tag :type="getPriorityType(item.priority)" size="small" effect="dark" style="min-width: 48px; text-align: center">
                {{ item.priority === "high" ? "重要" : item.priority === "medium" ? "建议" : "参考" }}
              </el-tag>
              <strong>{{ item.category }}</strong>
            </div>
            <p style="margin: 4px 0 0 0; color: #606266; line-height: 1.6; white-space: pre-wrap">{{ item.content }}</p>
          </div>
        </el-card>

        <!-- Score history table -->
        <el-card shadow="hover" style="margin-top: 16px">
          <template #header><span style="font-weight: 600">成绩记录</span></template>
          <el-table :data="studentData.exams" stripe border>
            <el-table-column prop="exam_name" label="考试" min-width="160" />
            <el-table-column prop="exam_date" label="日期" width="100" />
            <el-table-column prop="avg_rate" label="综合得分率" width="100">
              <template #default="{ row }">{{ row.avg_rate }}%</template>
            </el-table-column>
            <el-table-column label="各科成绩">
              <template #default="{ row }">
                <span v-for="s in row.subjects" :key="s.subject_id" style="margin-right: 12px">
                  {{ s.subject_name }}: {{ s.score ?? "-" }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>

      <el-empty v-if="errorMsg" :description="errorMsg" />
      <el-empty v-else-if="!errorMsg && !loading && !studentData" description="请先选择一名学生" />

      <!-- Student list after search -->
      <template v-if="!studentData && students.length > 0 && !errorMsg">
        <el-table :data="students" stripe @row-click="(row: any) => { selectedStudentId = row.id; selectStudent(); }" style="cursor: pointer" max-height="400">
          <el-table-column prop="student_no" label="学号" width="150" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="class_name" label="班级" />
        </el-table>
      </template>
    </el-card>
  </div>


  <!-- AI Chat Button -->
  <el-button
    v-if="selectedStudentId"
    type="warning"
    size="large"
    style="position: fixed; bottom: 30px; right: 30px; z-index: 1000; border-radius: 50%; width: 56px; height: 56px; font-size: 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.2)"
    @click="aiChatVisible = true"
  >
    <el-icon><ChatDotSquare /></el-icon>
  </el-button>

  <AIChatDialog v-model:visible="aiChatVisible" context-type="student" :context-id="selectedStudentId" :context-label="studentData?.student_name" />


</template>
<style scoped>
.chart-card { margin-bottom: 0; }
.chart-card :deep(.el-card__body) { padding: 8px; }
</style>






