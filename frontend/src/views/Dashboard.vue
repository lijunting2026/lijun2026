<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { analysisApi } from "@/api"
import type { DashboardData, RecentExam, SubjectStat, ClassRanking } from "@/types"

import { ElMessage } from "element-plus"
import ChartBar from "@/components/ChartBar.vue"
import ChartLine from "@/components/ChartLine.vue"
import ChartRadar from "@/components/ChartRadar.vue"
import ChartPie from "@/components/ChartPie.vue"

const router = useRouter()
const loading = ref(true)
const dashboard = ref<DashboardData | null>(null)

const chartExamTrend = computed(() => {
  const exams = dashboard.value?.recent_exams || []
  if (!exams.length) return {}
  return {
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: exams.map((e: any) => e.exam_name), axisLabel: { rotate: 10, fontSize: 11 } },
    yAxis: { type: "value", name: "得分率(%)", max: 100 },
    series: [{
      type: "line", data: exams.map((e: any) => e.avg_rate), smooth: true,
      areaStyle: { color: "rgba(64,158,255,0.15)" },
      lineStyle: { color: "#409EFF", width: 3 },
      itemStyle: { color: "#409EFF" },
      label: { show: true, formatter: (p: any) => p.value + "%" },
    }],
  }
})

const chartSubjectBar = computed(() => {
  const subjects = dashboard.value?.subject_stats || []
  if (!subjects.length) return {}
  return {
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: subjects.map((s: any) => s.subject_name) },
    yAxis: { type: "value", name: "平均分" },
    series: [{
      type: "bar", data: subjects.map((s: any) => s.avg_score),
      itemStyle: {
        color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "#409EFF" }, { offset: 1, color: "#79BBFF" }] },
        borderRadius: [6, 6, 0, 0],
      },
      label: { show: true, position: "top", formatter: (p: any) => p.value.toFixed(1) },
    }],
  }
})

const chartRadarOption = computed(() => {
  const subjects = dashboard.value?.subject_stats || []
  if (!subjects.length) return {}
  return {
    tooltip: { trigger: "item" },
    radar: {
      indicator: subjects.map((s: any) => ({ name: s.subject_name, max: 100 })),
      radius: "60%",
    },
    series: [{
      type: "radar",
      data: [{
        value: subjects.map((s: any) => s.full_score ? Math.round(s.avg_score / s.full_score * 100) : 0),
        name: "得分率",
        areaStyle: { color: "rgba(64,158,255,0.2)" },
        lineStyle: { color: "#409EFF" },
        itemStyle: { color: "#409EFF" },
      }],
    }],
  }
})

const chartClassRank = computed(() => {
  const classRank = dashboard.value?.class_ranking || []
  if (!classRank.length || !classRank[0].classes?.length) return {}
  const allClasses = classRank.flatMap((g: any) => g.classes || [])
  return {
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: allClasses.map((c: any) => c.class_name), axisLabel: { rotate: 20, fontSize: 10 } },
    yAxis: { type: "value", name: "得分率(%)", max: 100 },
    series: [{
      type: "bar", data: allClasses.map((c: any) => c.avg_rate),
      itemStyle: {
        color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "#67C23A" }, { offset: 1, color: "#B3E19D" }] },
        borderRadius: [6, 6, 0, 0],
      },
      label: { show: true, position: "top", formatter: (p: any) => p.value + "%" },
    }],
  }
})

const chartExamType = computed(() => {
  const examTypes = dashboard.value?.exam_type_stats || {}
  const typeLabels: Record<string, string> = { monthly: "月考", midterm: "期中", "final": "期末" }
  const typeColors = ["#409EFF", "#67C23A", "#E6A23C"]
  const typeData = Object.entries(examTypes)
    .filter(([_, v]) => (v as number) > 0)
    .map(([k, v], i) => ({ name: typeLabels[k] || k, value: v as number, itemStyle: { color: typeColors[i] } }))
  if (!typeData.length) return {}
  return {
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    legend: { bottom: "0%", orient: "horizontal" },
    series: [{
      type: "pie", radius: ["40%", "65%"], center: ["50%", "45%"],
      avoidLabelOverlap: false,
      label: { show: true, formatter: "{b}\n{d}%" },
      emphasis: { label: { show: true, fontSize: "16", fontWeight: "bold" } },
      data: typeData,
    }],
  }
})

async function loadDashboard() {
  try {
    const res = await analysisApi.dashboard()
    dashboard.value = res.data
  } catch {
    ElMessage.error("获取仪表盘数据失败")
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="dashboard">
<el-skeleton :loading="loading" animated>
      <template #template>
        <el-row :gutter="16" style="margin-bottom: 16px">
          <el-col :xs="12" :sm="8" :md="4" v-for="i in 6" :key="i">
            <el-card shadow="hover" class="kpi-card">
              <el-skeleton-item variant="text" style="width: 60%; margin: 0 auto" />
              <el-skeleton-item variant="text" style="width: 40%; margin: 4px auto" />
            </el-card>
          </el-col>
        </el-row>
      </template>
      <template #default>
    <!-- KPI Cards -->
    <el-row :gutter="16" v-if="dashboard">
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card" @click="go('/students-group/schools')">
          <div class="kpi-value" style="color: #409EFF">{{ dashboard.stats.grades }}</div>
          <div class="kpi-label">年级</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card" @click="go('/students-group/schools')">
          <div class="kpi-value" style="color: #67C23A">{{ dashboard.stats.classes }}</div>
          <div class="kpi-label">班级</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card" @click="go('/exam-group/subjects')">
          <div class="kpi-value" style="color: #E6A23C">{{ dashboard.stats.subjects }}</div>
          <div class="kpi-label">科目</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card" @click="go('/students-group/students')">
          <div class="kpi-value" style="color: #F56C6C">{{ dashboard.stats.students }}</div>
          <div class="kpi-label">学生</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card" @click="go('/exam-group/exams')">
          <div class="kpi-value" style="color: #909399">{{ dashboard.stats.exams }}</div>
          <div class="kpi-label">考试</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card" @click="go('/scores')">
          <div class="kpi-value" style="color: #409EFF">{{ dashboard.stats.scores }}</div>
          <div class="kpi-label">成绩记录</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Trend Alert -->
    <el-row :gutter="16" style="margin-top: 16px" v-if="dashboard?.trend">
      <el-col :span="24">
        <el-alert
          :title="'整体趋势: ' + dashboard.trend.description"
          :type="dashboard.trend.direction === 'up' ? 'success' : dashboard.trend.direction === 'down' ? 'warning' : 'info'"
          :description="'共 ' + dashboard.stats.exams + ' 场考试，' + dashboard.stats.scores + ' 条成绩记录'"
          show-icon
          :closable="false"
        />
      </el-col>
    </el-row>

    <!-- Charts Row 1 -->
    <el-row :gutter="16" style="margin-top: 16px" v-if="dashboard">
      <el-col :xs="24" :sm="24" :md="14">
        <el-card shadow="hover" class="chart-card">
          <template #header><span style="font-weight: 600">考试成绩趋势</span></template>
          <v-chart v-if="chartExamTrend.series" :option="chartExamTrend" autoresize style="height: 340px" />
          <el-empty v-else description="暂无考试数据" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="10">
        <el-card shadow="hover" class="chart-card">
          <template #header><span style="font-weight: 600">各科得分率雷达</span></template>
          <ChartRadar v-if="chartRadarOption.series" :option="chartRadarOption" />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row 2 -->
    <el-row :gutter="16" style="margin-top: 16px" v-if="dashboard">
      <el-col :xs="24" :sm="24" :md="14">
        <el-card shadow="hover" class="chart-card">
          <template #header><span style="font-weight: 600">各科平均分</span></template>
          <ChartBar v-if="chartSubjectBar.series" :option="chartSubjectBar" />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="10">
        <el-card shadow="hover" class="chart-card">
          <template #header><span style="font-weight: 600">班级排名</span></template>
          <ChartBar v-if="chartClassRank.series" :option="chartClassRank" />
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Regression Alerts -->
    <el-row :gutter="16" style="margin-top: 16px" v-if="dashboard?.regression_alerts?.length">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header><div style="display: flex; align-items: center; gap: 8px"><span style="font-weight: 600; color: #F56C6C">成绩退步预警</span><el-tag size="small" type="danger">需重点关注</el-tag></div></template>
          <div v-for="alert in dashboard.regression_alerts" :key="alert.exam_name" class="alert-item">
            <span>{{ alert.exam_name }}</span>
            <el-tag :type="alert.level === 'danger' ? 'danger' : 'warning'" size="small">{{ alert.desc }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Alerts -->
    <el-row :gutter="16" style="margin-top: 16px" v-if="dashboard?.subject_alerts?.length || dashboard?.risk_students?.length">
      <el-col :xs="24" :sm="24" :md="12" v-if="dashboard?.subject_alerts?.length">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px">
              <span style="font-weight: 600; color: #E6A23C">科目预警</span>
              <el-tag size="small" type="warning">需关注科目</el-tag>
            </div>
          </template>
          <div v-for="alert in dashboard.subject_alerts" :key="alert.subject_name" class="alert-item">
            <span>{{ alert.subject_name }}</span>
            <el-tag :type="alert.level === 'danger' ? 'danger' : 'warning'" size="small">
              平均{{ alert.avg_score }}分 - {{ alert.desc }}
            </el-tag>
          </div>
          <el-empty v-if="!dashboard.subject_alerts.length" description="暂无科目预警" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12" v-if="dashboard?.risk_students?.length">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px">
              <span style="font-weight: 600; color: #F56C6C">需关注学生</span>
              <el-tag size="small" type="danger">综合得分率最低</el-tag>
            </div>
          </template>
          <div v-for="s in dashboard.risk_students" :key="s.student_no" class="alert-item">
            <span>{{ s.student_name }} ({{ s.student_no }})</span>
            <el-tag :type="s.avg_rate < 50 ? 'danger' : 'warning'" size="small">{{ s.avg_rate }}%</el-tag>
          </div>
          <el-empty v-if="!dashboard.risk_students.length" description="暂无风险学生" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent exams table -->
    <el-card shadow="hover" style="margin-top: 16px" v-if="dashboard?.recent_exams?.length">
      <template #header><span style="font-weight: 600">最近考试</span></template>
      <el-table :data="dashboard.recent_exams" stripe>
        <el-table-column prop="exam_name" label="考试名称" min-width="200" />
        <el-table-column prop="exam_date" label="日期" width="120" />
        <el-table-column prop="student_count" label="参考人数" width="100" />
        <el-table-column prop="avg_rate" label="平均得分率" width="120">
          <template #default="{ row }">
            <el-tag :type="row.avg_rate >= 70 ? 'success' : row.avg_rate >= 55 ? 'warning' : 'danger'" size="small">
              {{ row.avg_rate }}%
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Quick actions -->
    <el-card shadow="hover" style="margin-top: 16px" v-if="dashboard">
      <template #header><span style="font-weight: 600">快捷操作</span></template>
      <div style="display: flex; gap: 12px; flex-wrap: wrap">
        <el-button type="primary" @click="go('/exam-group/exams')" round>创建考试</el-button>
        <el-button type="success" @click="go('/students-group/students')" round>管理学生</el-button>
        <el-button type="warning" @click="go('/exam-group/scores')" round>录入成绩</el-button>
        <el-button type="primary" @click="go('/analysis-group/analysis')" round>年级分析</el-button>
        <el-button type="primary" @click="go('/analysis-group/class-analysis')" round>班级分析</el-button>
      </div>
    </el-card>
      </template>
    </el-skeleton>
  </div>
</template>

<style scoped>
.dashboard {
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.kpi-card {
  cursor: pointer;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 8px;
}
.kpi-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
.kpi-value {
  font-size: 32px;
  font-weight: 700;
}
.kpi-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
.chart-card {
  margin-bottom: 0;
}
.chart-card :deep(.el-card__body) {
  padding: 8px;
}
.alert-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.alert-item:last-child {
  border-bottom: none;
}
</style>
