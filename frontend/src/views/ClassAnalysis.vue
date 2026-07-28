<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue"
import { schoolApi, analysisApi } from "@/api"
import type { ClassInfo } from "@/types"
import { ElMessage } from "element-plus"
import AIChatDialog from "@/components/AIChatDialog.vue"

const classes = ref<ClassInfo[]>([])
const selectedClassId = ref("")
const classData = ref<any>(null)
const loading = ref(false)
const aiChatVisible = ref(false)

const chartExamTrend = ref<any>({})
const chartSubjectBar = ref<any>({})

async function loadClasses() {
  const res = await schoolApi.listClasses()
  classes.value = res.data
}

async function exportClassData() {
  if (!classData.value) return
  const token = localStorage.getItem("token") || ""
  const res = await fetch("/api/v1/analysis/class/" + selectedClassId.value + "/export", {
    headers: { Authorization: "Bearer " + token }
  })
  if (!res.ok) { ElMessage.error("导出失败"); return }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a"); a.href = url
  a.download = classData.value.class_name + "_班级分析.xlsx"; a.click()
  URL.revokeObjectURL(url)
  ElMessage.success("导出成功")
}

async function exportClassWord() {
  if (!selectedClassId.value) return
  await downloadBlob("/api/v1/report/word/class/" + selectedClassId.value, classData.value?.class_name + "_班级分析报告.docx")
}

async function exportClassPdf() {
  if (!selectedClassId.value) return
  await downloadBlob("/api/v1/report/pdf/class/" + selectedClassId.value, classData.value?.class_name + "_班级分析报告.pdf")
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

async function analyzeClass() {
  if (!selectedClassId.value) return
  loading.value = true
  try {
    const res = await analysisApi.getClassAnalysis(selectedClassId.value)
    classData.value = res.data
    buildCharts()
  } catch {
    ElMessage.error("获取班级分析数据失败")
  } finally {
    loading.value = false
  }
}

function buildCharts() {
  if (!classData.value) return

  const exams = classData.value.exam_summary || []
  if (exams.length > 0) {
    chartExamTrend.value = {
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
      xAxis: { type: "category", data: exams.map((e: any) => e.exam_name) },
      yAxis: { type: "value", name: "平均得分率(%)", max: 100 },
      series: [{
        type: "line",
        data: exams.map((e: any) => e.avg_rate),
        smooth: true,
        areaStyle: { color: "rgba(64,158,255,0.15)" },
        lineStyle: { color: "#409EFF", width: 3 },
        itemStyle: { color: "#409EFF" },
        label: { show: true, formatter: (p: any) => p.value + "%" },
      }],
    }
  }

  const subjects = classData.value.subject_stats || []
  if (subjects.length > 0) {
    chartSubjectBar.value = {
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
      xAxis: { type: "category", data: subjects.map((s: any) => s.subject_name) },
      yAxis: { type: "value", name: "平均分" },
      series: [{
        type: "bar",
        data: subjects.map((s: any) => s.avg_score),
        itemStyle: { color: "#409EFF", borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: "top", formatter: (p: any) => p.value.toFixed(1) },
      }],
    }
  }

  nextTick(() => window.dispatchEvent(new Event("resize")))
}

onMounted(loadClasses)
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-weight: 600">班级数据分析</span>
          <div style="display: flex; gap: 8px">
            <el-select v-model="selectedClassId" placeholder="选择班级" filterable style="width: 220px" @change="analyzeClass">
              <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button type="primary" :disabled="!selectedClassId" :loading="loading" @click="analyzeClass">分析</el-button>
            <el-button v-if="classData" type="success" @click="exportClassData">Excel</el-button>
            <el-button v-if="classData" type="primary" @click="exportClassWord">Word</el-button>
            <el-button v-if="classData" type="danger" @click="exportClassPdf">PDF</el-button>
          </div>
        </div>
      </template>

      <template v-if="classData">
        <el-descriptions title="班级概况" :column="4" border style="margin-bottom: 16px">
          <el-descriptions-item label="班级">{{ classData.class_name }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ classData.grade_name }}</el-descriptions-item>
          <el-descriptions-item label="学生人数">{{ classData.student_count }}</el-descriptions-item>
          <el-descriptions-item label="考试次数">{{ classData.exam_count }}</el-descriptions-item>
        </el-descriptions>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">考试成绩趋势</span></template>
              <v-chart v-if="chartExamTrend.series" :option="chartExamTrend" autoresize style="height: 320px" />
              <el-empty v-else description="暂无趋势数据" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">各科平均分</span></template>
              <v-chart v-if="chartSubjectBar.series" :option="chartSubjectBar" autoresize style="height: 320px" />
              <el-empty v-else description="暂无数据" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="24">
            <el-card shadow="hover">
              <template #header><span style="font-weight: 600">各科详细统计</span></template>
              <el-table :data="classData.subject_stats" stripe border>
                <el-table-column prop="subject_name" label="科目" />
                <el-table-column prop="avg_score" label="平均分" width="100" />
                <el-table-column prop="max_score" label="最高分" width="100" />
                <el-table-column prop="min_score" label="最低分" width="100" />
                <el-table-column prop="count" label="样本数" width="100" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="24">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px">
                  <span style="font-weight: 600; color: #F56C6C">需关注学生</span>
                  <el-tag type="danger" size="small">综合得分率最低</el-tag>
                </div>
              </template>
              <el-table :data="classData.risk_students" stripe>
                <el-table-column prop="student_no" label="学号" width="150" />
                <el-table-column prop="student_name" label="姓名" width="120" />
                <el-table-column prop="avg_rate" label="综合得分率" width="120">
                  <template #default="{ row }">{{ row.avg_rate }}%</template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="24">
            <el-card shadow="hover">
              <template #header><span style="font-weight: 600">学生成绩一览</span></template>
              <el-table :data="classData.student_list" stripe border max-height="500" size="small">
                <el-table-column prop="student_no" label="学号" width="130" />
                <el-table-column prop="student_name" label="姓名" width="100" />
                <el-table-column prop="avg_rate" label="综合得分率" width="120">
                  <template #default="{ row }">
                    <el-tag :type="row.avg_rate >= 80 ? 'success' : row.avg_rate >= 60 ? 'warning' : 'danger'" size="small">
                      {{ row.avg_rate }}%
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <el-empty v-else description="请先选择一个班级" />
    </el-card>
  </div>
  <!-- AI Chat Button -->
  <el-button
    v-if="selectedClassId"
    type="warning"
    size="large"
    style="position: fixed; bottom: 30px; right: 30px; z-index: 1000; border-radius: 50%; width: 56px; height: 56px; font-size: 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.2)"
    @click="aiChatVisible = true"
  >
    <el-icon><ChatDotSquare /></el-icon>
  </el-button>

  <AIChatDialog v-model:visible="aiChatVisible" context-type="exam" :context-id="selectedClassId" :context-label="classData?.class_name" />
</template>

<style scoped>
.chart-card { margin-bottom: 0; }
.chart-card :deep(.el-card__body) { padding: 8px; }
</style>

