import { createRouter, createWebHashHistory } from "vue-router"
import { useAuthStore } from "@/stores"
import MainLayout from "@/layout/MainLayout.vue"

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/Login.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    component: MainLayout,
    redirect: "/dashboard",
    meta: { requiresAuth: true },
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: () => import("@/views/Dashboard.vue"),
        meta: { title: "首页" },
      },
      {
        path: "students-group",
        component: () => import("@/components/TabGroup.vue"),
        redirect: "/students-group/schools",
        meta: { title: "学生与班级管理" },
        props: {
          tabs: [
            { label: "年级班级", route: "/students-group/schools" },
            { label: "学生管理", route: "/students-group/students" },
          ],
        },
        children: [
          {
            path: "schools",
            component: () => import("@/views/Schools.vue"),
            meta: { title: "年级班级" },
          },
          {
            path: "students",
            component: () => import("@/views/Students.vue"),
            meta: { title: "学生管理" },
          },
        ],
      },
      {
        path: "exam-group",
        component: () => import("@/components/TabGroup.vue"),
        redirect: "/exam-group/subjects",
        meta: { title: "考试与科目管理" },
        props: {
          tabs: [
            { label: "科目管理", route: "/exam-group/subjects" },
            { label: "考试管理", route: "/exam-group/exams" },
            { label: "成绩管理", route: "/exam-group/scores" },
          ],
        },
        children: [
          {
            path: "subjects",
            component: () => import("@/views/Subjects.vue"),
            meta: { title: "科目管理" },
          },
          {
            path: "exams",
            component: () => import("@/views/Exams.vue"),
            meta: { title: "考试管理" },
          },
          {
            path: "scores",
            component: () => import("@/views/Scores.vue"),
            meta: { title: "成绩管理" },
          },

        ],

      },
      {
        path: "analysis-group",
        component: () => import("@/components/TabGroup.vue"),
        redirect: "/analysis-group/analysis",
        meta: { title: "数据分析与跟踪" },
        props: {
          tabs: [
            { label: "年级分析", route: "/analysis-group/analysis" },
            { label: "班级分析", route: "/analysis-group/class-analysis" },
            { label: "个体分析", route: "/analysis-group/student-tracking" },
          ],
        },
        children: [
          {
            path: "analysis",
            component: () => import("@/views/Analysis.vue"),
            meta: { title: "数据分析" },
          },
          {
            path: "student-tracking",
            component: () => import("@/views/StudentTracking.vue"),
            meta: { title: "学情跟踪" },
          },
          {
            path: "class-analysis",
            component: () => import("@/views/ClassAnalysis.vue"),
            meta: { title: "班级分析" },
          },
        ],
      },
      {
        path: "scores/entry", 
        component: () => import("@/views/ScoreEntry.vue"), 
        meta: { title: "录入成绩" }, 
      },
      { 
        path: "users",
        name: "UserManagement",
        component: () => import("@/views/UserManagement.vue"),
        meta: { title: "用户管理", adminOnly: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth !== false && !auth.isLoggedIn) {
    next("/login")
  } else if (to.path === "/login" && auth.isLoggedIn) {
    next("/dashboard")
  } else {
    next()
  }
})

export default router

