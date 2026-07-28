# 考试质量分析系统 — Docker 一键部署教程

> 适用场景：局域网内多台电脑同时访问、多人并发使用
> 系统要求：目标机器已安装 Docker 和 Docker Compose

---

## 一、准备工作

### 1.1 复制项目到服务器

将项目文件夹 考试质量分析系统 复制到服务器上，或直接在服务器上拉取 Git 仓库。

### 1.2 修改安全配置（首次部署必须做）

编辑 docker-compose.yml，修改以下两项：

**① 数据库密码**
找到 postgres 服务的环境变量，将密码改为自己的：
`yaml
POSTGRES_PASSWORD: 改成你的强密码
`

**② JWT 密钥**
找到 backend 服务的环境变量，将 SECRET_KEY 改为随机字符串：
`yaml
SECRET_KEY: 生成一个随机字符串，例如 openssl rand -hex 32
`

### 1.3 （可选）配置 AI 对话

如需使用 AI 分析功能，设置以下环境变量（三种方式任选一种）：

**方式一：命令行传参（推荐）**
`ash
export LLM_ENABLED=true
export LLM_API_KEY=sk-your-key-here
export LLM_API_BASE=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
`

**方式二：修改 backend/.env 文件**
`ini
LLM_ENABLED=true
LLM_API_KEY=sk-your-key-here
LLM_API_BASE=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
`

**方式三：直接编辑 docker-compose.yml**
`yaml
LLM_ENABLED: "true"
LLM_API_KEY: sk-your-key-here
`

> 不需要 AI 功能则跳过此步（LLM_ENABLED 默认 false）

---

## 二、一键部署

在项目根目录（docker-compose.yml 所在目录）打开终端，执行：

`ash
docker-compose up -d --build
`

首次执行会构建镜像，耗时约 5-10 分钟（取决于网络速度）。输出类似：

`
Building backend
...
Building frontend
...
Creating exam_postgres ...
Creating exam_backend  ...
Creating exam_frontend ...
`

### 验证部署

`ash
# 查看容器状态（三个容器都应该是 Up 状态）
docker-compose ps

# 查看日志
docker-compose logs -f

# 测试 API 是否正常
curl http://localhost:8000/health
# 返回: {"status":"ok"}
`

### 初始化数据

首次部署后数据库是空的，需要执行种子数据脚本：

`ash
# 进入后端容器
docker exec -it exam_backend sh

# 在容器内执行种子数据
python -m app.utils.seed

# 退出容器
exit
`

种子脚本会自动创建：
- 管理员账号：dmin / dmin123
- 示例数据：高一年级、高二年级、语文/数学/英语等科目

---

## 三、访问系统

打开浏览器访问 http://服务器IP（如本机部署则访问 http://localhost）

默认登录：
- 用户名：dmin
- 密码：dmin123

> 局域网其他电脑也可以用 http://服务器IP 直接访问

---

## 四、架构说明

部署后的系统架构如下：

`
                                  ┌─────────────────┐
                                  │   PostgreSQL    │
                                  │   (examdb)      │
                                  └────────┬────────┘
                                           │
用户浏览器 ──→ Nginx (:80) ──→ FastAPI (:8000)
                  │                │
                  │  /api/*        │  查询分析
                  │                │
           ┌──────┴──────┐         │
           │  静态文件    │         │
           │ (Vue 构建)   │         │
           └─────────────┘         │
                                   │
                    ┌──────────────┴─┐
                    │  AI 大模型 API │
                    │  (DeepSeek等)  │
                    └────────────────┘
`

每个组件的职责：

| 服务 | 镜像 | 说明 |
|------|------|------|
| **frontend** (nginx:alpine) | 前端 | 托管 Vue 构建产物，反向代理 /api 到后端 |
| **backend** (python:3.11-slim) | FastAPI | 业务逻辑、数据分析、报告生成 |
| **postgres** (postgres:15) | 数据库 | 所有数据的持久化存储 |

---

## 五、常用运维命令

### 启动 / 停止 / 重启
`ash
docker-compose start      # 启动（不重新创建）
docker-compose stop       # 停止
docker-compose restart    # 重启
docker-compose down       # 停止并删除容器（数据不会丢失）
`

### 查看日志
`ash
docker-compose logs -f           # 所有服务的日志
docker-compose logs -f backend   # 只看后端日志
`

### 更新部署（修改代码后）
`ash
docker-compose up -d --build     # 重新构建并启动
`

### 数据备份
`ash
# 导出 PostgreSQL 数据
docker exec exam_postgres pg_dump -U examuser examdb > backup_日期.sql

# 恢复数据
cat backup.sql | docker exec -i exam_postgres psql -U examuser examdb
`

---

## 六、常见问题

### 端口冲突（80 或 5432 被占用）
修改 docker-compose.yml 中的端口映射：
`yaml
ports:
  - "8080:80"     # 将前端端口改为 8080
  - "5433:5432"   # 将数据库端口改为 5433
`

### 如何让前端能通过 IP 直连后端开发服务器
在 rontend/.env 中添加：
`
VITE_API_BASE=http://你的IP:8000
`

### 如何只用 Docker 跑后端（前端用本地开发）
`ash
docker-compose up -d postgres backend
# 然后在本机运行前端：cd frontend && npm run dev
`

### 生产环境去掉热加载卷挂载
编辑 docker-compose.yml，删除 backend 的 volumes 配置（保留数据不丢失）：
`yaml
  backend:
    # 删除下面这行
    # volumes:
    #   - ./backend:/app
`

---

## 七、安全 Checklist（上线前必查）

- [ ] SECRET_KEY 已改为随机字符串（不在用 change-this-to-...）
- [ ] 数据库密码 POSTGRES_PASSWORD 已改为强密码
- [ ] 默认管理员 admin/Admin@ChangeMe2026 首次登录已修改密码
- [ ] DEBUG: "false"（已默认设为 false）
- [ ] 不需要 AI 时 LLM_ENABLED 保持 false
- [ ] 服务器防火墙已配置，非必要端口不对外开放（参考 `docker/防火墙配置指南.md`）
