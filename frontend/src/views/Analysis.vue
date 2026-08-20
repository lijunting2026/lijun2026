<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue"
import { analysisApi, examApi, subjectApi, schoolApi } from "@/api"
import type { Exam, Subject, Grade, ExamAnalysis, SubjectStats, ScoreDistribution, LineStats, OnePointTable } from "@/types"
import { ElMessage } from "element-plus"
import AIChatDialog from "@/components/AIChatDialog.vue"
import ChartBar from "@/components/ChartBar.vue"
import ChartRadar from "@/components/ChartRadar.vue"
import { downloadBlob } from "@/utils/download"

const exams = ref<Exam[]>([])
const subjects = ref<Subject[]>([])
const grades = ref<Grade[]>([])
const filterGradeId = ref("")
const selectedExamId = ref("")
const analysis = ref<ExamAnalysis | null>(null)
const distributions = ref<Record<string, ScoreDistribution[]>>({})
const loading = ref(false)
const scoreMode = ref<"auto" | "raw" | "converted" | "both">("auto")
const lineStats = ref<LineStats | null>(null)
const onePoint = ref<OnePointTable | null>(null)

const scoreModeLabel = computed(() => {
  const map: Record<string, string> = { auto: "自动", raw: "原始分", converted: "赋分", both: "双轨" }
  return map[scoreMode.value] || scoreMode.value
})
const aiChatVisible = ref(false)
const showCharts = ref(false)
const kpData = ref<any[]>([])
const kpLoading = ref(false)

const chartAvgBar = computed(() => {
  if (!analysis.value) return {}
  const gs = analysis.value.grade_stats || []
  if (!gs.length) return {}
  return {
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: gs.map((s) => s.subject_name), axisLabel: { fontSize: 11 } },
    yAxis: { type: "value", name: "平均分" },
    series: [{
      type: "bar",
      data: gs.map((s) => s.avg_score),
      itemStyle: { color: "#409EFF", borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: "top", fontSize: 11, formatter: (p: any) => p.value.toFixed(1) },
    }],
  }
})

const chartPassRate = computed(() => {
  if (!analysis.value) return {}
  const gs = analysis.value.grade_stats || []
  if (!gs.length) return {}
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["及格率", "优秀率"], top: 0 },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: gs.map((s) => s.subject_name) },
    yAxis: { type: "value", name: "%", max: 100 },
    series: [
      { name: "及格率", type: "bar", data: gs.map((s) => s.pass_rate), itemStyle: { color: "#67C23A" } },
      { name: "优秀率", type: "bar", data: gs.map((s) => s.excellent_rate), itemStyle: { color: "#E6A23C" } },
    ],
  }
})

const chartRadarOption = computed(() => {
  if (!analysis.value) return {}
  const gs = analysis.value.grade_stats || []
  if (!gs.length) return {}
  return {
    tooltip: { trigger: "item" },
    radar: {
      indicator: gs.map((s) => ({ name: s.subject_name, max: 100 })),
      radius: "60%",
    },
    series: [{
      type: "radar",
      data: [{ value: gs.map((s) => s.avg_score_rate), name: "得分率", areaStyle: { color: "rgba(64,158,255,0.2)" }, lineStyle: { color: "#409EFF" }, itemStyle: { color: "#409EFF" } }],
    }],
  }
})

const chartDistribution = computed(() => {
  const firstSubj = Object.keys(distributions.value)[0]
  if (!firstSubj || !distributions.value[firstSubj]?.length) return {}
  const dist = distributions.value[firstSubj]
  return {
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: dist.map((d) => d.range_label), axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: "value", name: "人数" },
    series: [{
      type: "bar",
      data: dist.map((d) => d.count),
      itemStyle: { color: "#409EFF" },
      label: { show: true, position: "top", fontSize: 10 },
    }],
  }
})

const chartKpRadar = computed(() => {
  if (!kpData.value.length) return {}
  const items = kpData.value.slice(0, 12)
  return {
    tooltip: { trigger: "item" },
    radar: {
      indicator: items.map((k) => ({ name: k.knowledge_point_name, max: 100 })),
      radius: "55%",
      center: ["50%", "55%"],
    },
    series: [{
      type: "radar",
      data: [{
        value: items.map((k) => k.avg_mastery_rate),
        name: "掌握率",
        areaStyle: { color: "rgba(103,194,58,0.2)" },
        lineStyle: { color: "#67C23A", width: 2 },
        itemStyle: { color: "#67C23A" },
      }],
    }],
  }
})

const chartClassCompare = computed(() => {
  if (!analysis.value) return {}
  const classStats = analysis.value.class_stats || []
  const firstSubj = analysis.value.grade_stats?.[0]
  if (!classStats.length || !firstSubj) return {}
  return {
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: classStats.map((c) => c.class_name), axisLabel: { rotate: 20, fontSize: 10 } },
    yAxis: { type: "value", name: "平均分" },
    series: [{
      type: "bar",
      data: classStats.map((c) => {
        const st = c.stats.find((s) => s.subject_id === firstSubj.subject_id)
        return st ? st.avg_score : 0
      }),
      itemStyle: { color: "#409EFF", borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: "top", fontSize: 10, formatter: (p: any) => p.value.toFixed(1) },
    }],
  }
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

async function loadSubjects() {
  try {
    const res = await subjectApi.list()
    subjects.value = res.data as any
  } catch { /* ignore */ }
}

async function analyze() {
  if (!selectedExamId.value) return
  loading.value = true
  showCharts.value = false
  try {
    const res = await analysisApi.examAnalysis(selectedExamId.value, scoreMode.value)
    analysis.value = res.data
    try {
      const ls = await analysisApi.lineStats(selectedExamId.value, scoreMode.value)
      lineStats.value = ls.data
    } catch {
      lineStats.value = null
    }
    try {
      const op = await analysisApi.onePointTable(selectedExamId.value, scoreMode.value)
      onePoint.value = op.data
    } catch {
      onePoint.value = null
    }

    const distPromises = (res.data.grade_stats || []).slice(0, 3).map(async (gs: SubjectStats) => {
      const exam = exams.value.find((e) => e.id === selectedExamId.value)
      const es = exam?.exam_subjects.find((s) => s.subject_id === gs.subject_id)
      if (es) {
        try {
          const distRes = await analysisApi.scoreDistribution(es.id)
          distributions.value[gs.subject_id] = distRes.data.distributions
        } catch { /* ignore */ }
      }
    })
    await Promise.all(distPromises)
    // Load knowledge point analysis
    try {
      const kpRes = await analysisApi.getExamKnowledgeAnalysis(selectedExamId.value)
      kpData.value = kpRes.data?.knowledge_points || []
    } catch { /* ignore */ }
    showCharts.value = true
  } catch {
    ElMessage.error("获取分析数据失败")
  } finally {
    loading.value = false
  }
}

watch(scoreMode, () => {
  if (analysis.value && selectedExamId.value) {
    analyze()
  }
})

onMounted(() => {
  loadGrades()
  loadSubjects()
  loadExams()
})

async function exportAnalysis() {
  if (!selectedExamId.value) return
  await downloadBlob("/api/v1/analysis/export/" + selectedExamId.value, "分析结果.xlsx")
}

async function exportWord() {
  if (!selectedExamId.value) return
  await downloadBlob("/api/v1/report/word/" + selectedExamId.value, "分析报告.docx")
}

async function exportPdf() {
  if (!selectedExamId.value) return
  await downloadBlob("/api/v1/report/pdf/" + selectedExamId.value, "分析报告.pdf")
}

async function exportPpt() {
  if (!selectedExamId.value) return
  await downloadBlob("/api/v1/report/ppt/" + selectedExamId.value, "分析报告.pptx")
}



function onGradeChange() {
  loadExams()
  selectedExamId.value = ""
  analysis.value = null
  showCharts.value = false
}
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <span style="font-weight: 600">考试分析</span>
          <div style="display: flex; gap: 8px; align-items: center">
            <el-select v-model="filterGradeId" placeholder="筛选年级" clearable style="width: 130px" @change="onGradeChange">
              <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
            <el-select v-model="selectedExamId" placeholder="选择考试" filterable style="width: 240px">
              <el-option v-for="e in exams" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
            <el-radio-group v-model="scoreMode" size="small" :disabled="!selectedExamId">
              <el-radio-button label="auto">自动</el-radio-button>
              <el-radio-button label="raw">原始分</el-radio-button>
              <el-radio-button label="converted">赋分</el-radio-button>
              <el-radio-button label="both">双轨</el-radio-button>
            </el-radio-group>
            <el-button type="primary" :disabled="!selectedExamId" :loading="loading" @click="analyze">开始分析</el-button>
            <el-button v-if="analysis" type="success" @click="exportAnalysis">Excel</el-button>
              <el-button v-if="analysis" type="primary" @click="exportWord">Word</el-button>
              <el-button v-if="analysis" type="danger" @click="exportPdf">PDF</el-button>
              <el-button v-if="analysis" type="warning" @click="exportPpt">PPT</el-button>
          </div>
        </div>
      </template>

      <template v-if="showCharts && analysis">
        <!-- Charts row 1 -->
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">各科平均分</span></template>
              <ChartBar :option="chartAvgBar" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">及格率与优秀率</span></template>
              <ChartBar :option="chartPassRate" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Charts row 2 -->
        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="12">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">得分率雷达图</span></template>
              <ChartRadar :option="chartRadarOption" />
            </el-card>
          </el-col>
          <el-col :span="12" v-if="chartDistribution.xAxis?.data?.length">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">分数段分布</span></template>
              <ChartBar :option="chartDistribution" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Knowledge Points radar chart -->
        <el-row :gutter="16" style="margin-top: 16px" v-if="kpData.length">
          <el-col :span="24">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">知识点掌握雷达图</span></template>
              <ChartRadar :option="chartKpRadar" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Class comparison chart -->
        <el-row :gutter="16" style="margin-top: 16px" v-if="chartClassCompare.xAxis?.data?.length">
          <el-col :span="24">
            <el-card shadow="hover" class="chart-card">
              <template #header><span style="font-weight: 600">班级对比</span></template>
              <ChartBar :option="chartClassCompare" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Data tables -->
        <el-card shadow="hover" style="margin-top: 16px" v-if="lineStats && (lineStats.total_lines.length || lineStats.subject_lines.length || lineStats.dual_lines.length)">
          <template #header>
            <span style="font-weight: 600">上线统计（口径：{{ scoreModeLabel }}）</span>
            <span style="margin-left: 8px; color: #909399; font-size: 12px">参考人数 {{ lineStats.total_students }}</span>
          </template>
          <el-table v-if="lineStats.total_lines.length" :data="lineStats.total_lines" stripe border size="small">
            <el-table-column prop="line_name" label="总分线" />
            <el-table-column prop="score_value" label="分数线" width="90" />
            <el-table-column prop="source" label="来源" width="90" />
            <el-table-column prop="count" label="上线人数" width="90" />
            <el-table-column prop="rate" label="上线率" width="90">
              <template #default="{ row }">{{ row.rate }}%</template>
            </el-table-column>
            <el-table-column label="各班">
              <template #default="{ row }">
                <span v-for="c in row.classes" :key="c.class_id" style="margin-right: 10px">
                  {{ c.class_name }}: {{ c.count }}/{{ c.total }} ({{ c.rate }}%)
                </span>
              </template>
            </el-table-column>
          </el-table>
          <el-table v-if="lineStats.subject_lines.length" :data="lineStats.subject_lines" stripe border size="small" style="margin-top: 12px">
            <el-table-column prop="line_name" label="单科线" />
            <el-table-column prop="subject_name" label="科目" width="100" />
            <el-table-column prop="score_value" label="分数线" width="90" />
            <el-table-column prop="count" label="上线人数" width="90" />
            <el-table-column prop="rate" label="上线率" width="90">
              <template #default="{ row }">{{ row.rate }}%</template>
            </el-table-column>
            <el-table-column label="各班">
              <template #default="{ row }">
                <span v-for="c in row.classes" :key="c.class_id" style="margin-right: 10px">
                  {{ c.class_name }}: {{ c.count }}/{{ c.total }} ({{ c.rate }}%)
                </span>
              </template>
            </el-table-column>
          </el-table>
          <el-table v-if="lineStats.dual_lines.length" :data="lineStats.dual_lines" stripe border size="small" style="margin-top: 12px">
            <el-table-column prop="total_line_name" label="总分线" />
            <el-table-column prop="subject_line_name" label="单科线" />
            <el-table-column prop="subject_name" label="科目" width="100" />
            <el-table-column prop="count" label="双上线人数" width="100" />
            <el-table-column prop="rate" label="双上线率" width="100">
              <template #default="{ row }">{{ row.rate }}%</template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="hover" style="margin-top: 16px" v-if="onePoint && onePoint.items.length">
          <template #header>
            <span style="font-weight: 600">一分一段表（口径：{{ scoreModeLabel }}，{{ onePoint.total_students }} 人）</span>
          </template>
          <el-table :data="onePoint.items" stripe border size="small" max-height="360">
            <el-table-column prop="score" label="分数" width="90" />
            <el-table-column prop="count" label="人数" width="90" />
            <el-table-column prop="cumulative" label="累计人数" width="100" />
            <el-table-column prop="cumulative_rate" label="累计占比">
              <template #default="{ row }">{{ row.cumulative_rate }}%</template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="hover" style="margin-top: 16px">
          <template #header><span style="font-weight: 600">年级总体统计表</span></template>
          <el-table :data="analysis.grade_stats" stripe border>
            <el-table-column prop="subject_name" label="科目" />
            <el-table-column prop="avg_score" label="平均分" width="80" />
            <el-table-column prop="avg_score_rate" label="得分率" width="80">
              <template #default="{ row }">{{ row.avg_score_rate }}%</template>
            </el-table-column>
            <el-table-column prop="max_score" label="最高分" width="80" />
            <el-table-column prop="min_score" label="最低分" width="80" />
            <el-table-column prop="pass_rate" label="及格率" width="80">
              <template #default="{ row }">{{ row.pass_rate }}%</template>
            </el-table-column>
            <el-table-column prop="excellent_rate" label="优秀率" width="80">
              <template #default="{ row }">{{ row.excellent_rate }}%</template>
            </el-table-column>
            <el-table-column prop="std_dev" label="标准差" width="80" />
            <el-table-column v-if="analysis.score_mode === 'both'" prop="converted_avg_score" label="赋分平均" width="90" />
            <el-table-column v-if="analysis.score_mode === 'both'" prop="converted_avg_score_rate" label="赋分得分率" width="100">
              <template #default="{ row }">{{ row.converted_avg_score_rate }}%</template>
            </el-table-column>
            <el-table-column v-if="analysis.score_mode === 'both'" prop="converted_pass_rate" label="赋分及格率" width="100">
              <template #default="{ row }">{{ row.converted_pass_rate }}%</template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="hover" style="margin-top: 16px">
          <template #header><span style="font-weight: 600">各班统计</span></template>
          <el-table :data="analysis.class_stats" stripe border>
            <el-table-column prop="class_name" label="班级" />
            <el-table-column prop="student_count" label="人数" width="60" />
            <el-table-column label="各科平均分">
              <template #default="{ row }">
                <span v-for="s in row.stats" :key="s.subject_id" style="margin-right: 12px">
                  {{ s.subject_name }}: {{ s.avg_score }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="各科得分率">
              <template #default="{ row }">
                <span v-for="s in row.stats" :key="s.subject_id" style="margin-right: 12px">
                  {{ s.subject_name }}: {{ s.avg_score_rate }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>

      <el-empty v-else-if="!loading" description="请选择考试并点击开始分析" />
    </el-card>
  </div>

  <!-- AI Chat Button -->
  <el-button
    v-if="selectedExamId"
    type="warning"
    size="large"
    style="position: fixed; bottom: 30px; right: 30px; z-index: 1000; border-radius: 50%; width: 56px; height: 56px; font-size: 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.2)"
    @click="aiChatVisible = true"
  >
    <el-icon><ChatDotSquare /></el-icon>
  </el-button>

  <AIChatDialog v-model:visible="aiChatVisible" context-type="exam" :context-id="selectedExamId" :context-label="analysis?.exam_name" />
</template>

<style scoped>
.chart-card {
  margin-bottom: 0;
}
.chart-card :deep(.el-card__body) {
  padding: 8px;
}
</style>
