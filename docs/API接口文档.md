# API 接口文档

> 基础 URL: /api/v1
> 认证方式: Bearer Token（登录后获取）

---

## 一、认证管理 /auth

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 用户登录 |
| POST | /auth/change-password | 修改密码 |
| POST | /auth/register | 注册用户（需管理员） |
| GET | /auth/users | 用户列表（需管理员） |
| PUT | /auth/users/{id} | 编辑用户 |
| DELETE | /auth/users/{id} | 删除用户 |

## 二、学校管理 /schools

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /schools/grades | 年级列表 |
| POST | /schools/grades | 创建年级 |
| PUT | /schools/grades/{id} | 编辑年级 |
| DELETE | /schools/grades/{id} | 删除年级 |
| GET | /schools/classes | 班级列表 |
| POST | /schools/classes | 创建班级 |
| PUT | /schools/classes/{id} | 编辑班级 |
| DELETE | /schools/classes/{id} | 删除班级 |

## 三、科目管理 /subjects

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /subjects | 科目列表 |
| POST | /subjects | 创建科目 |
| PUT | /subjects/{id} | 编辑科目 |
| DELETE | /subjects/{id} | 删除科目 |

## 四、学生管理 /students

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /students | 学生列表 |
| POST | /students | 创建学生 |
| PUT | /students/{id} | 编辑学生 |
| DELETE | /students/{id} | 删除学生 |
| POST | /students/import | Excel批量导入 |
| POST | /students/{id}/transfer | 学生转班 |

## 五、考试管理 /exams

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /exams | 考试列表 |
| GET | /exams/{id} | 考试详情 |
| POST | /exams | 创建考试 |
| PUT | /exams/{id} | 编辑考试 |
| DELETE | /exams/{id} | 删除考试 |

## 六、成绩管理 /scores

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /scores | 成绩列表 |
| POST | /scores/batch | 批量录入 |
| POST | /scores/batch-delete | 批量删除 |
| GET | /scores/export-template | 下载导入模板 |
| POST | /scores/import | Excel导入 |
| GET | /scores/summary | 聚合统计 |

## 七、数据分析 /analysis

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /analysis/dashboard | 仪表盘 |
| GET | /analysis/exam/{id} | 考试分析 |
| GET | /analysis/class/{id} | 班级分析 |
| GET | /analysis/student/{id} | 学生学情 |
| GET | /analysis/student/{id}/advice | AI学习建议 |
| POST | /analysis/chat | AI对话 |

## 八、报告导出 /report

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /report/word/{exam_id} | Word报告 |
| GET | /report/pdf/{exam_id} | PDF报告 |
| GET | /report/ppt/{exam_id} | PPT报告 |

## 九、系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
