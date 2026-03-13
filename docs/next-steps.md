# AcaLite 下一步执行计划（从架构到实现）

> 目标：回答“下一步应该做什么”，将架构文档转为可执行任务，优先实现可演示的 MVP 骨架。

## 0. 优先级原则

- **P0（必须）**：2 周内做出可运行闭环（导入 PDF -> 检索 -> AI 摘要 -> 引用导出）。
- **P1（应该）**：提升可用性与稳定性（错误处理、任务状态、基础设置页）。
- **P2（可选）**：增强体验（思维导图可视化、更多格式导出）。

---

## 1. 第一阶段（未来 7 天）：项目底座搭建

### 1.1 仓库结构（P0）

建议建立以下目录：

```text
AcaLite/
  backend/
    app/
      api/
      core/
      models/
      services/
      workers/
    tests/
  frontend/
    src/
      views/
      components/
      stores/
  deploy/
    docker-compose.yml
  docs/
```

### 1.2 基础工程能力（P0）

- 后端：初始化 FastAPI、SQLAlchemy、Alembic、基础健康检查接口。
- 前端：初始化 Vue3 + Vite + TS，完成路由与基础布局（文献库页、检索页、设置页占位）。
- 部署：提供 `docker compose up` 启动 `postgres + redis + api + web`。

### 1.3 数据库第一版（P0）

先落 4 张核心表：
- `documents`
- `document_chunks`
- `ai_reports`
- `citations`

> 先不做复杂权限模型，单用户模式优先。

---

## 2. 第二阶段（第 2 周）：最小业务闭环

### 2.1 文献导入与索引（P0）

- `POST /api/v1/documents/import`
- 流程：上传 PDF -> 计算 hash -> 保存文件 -> 提取文本 -> chunk -> 入库。
- 首版可先只支持单文件导入，再扩展批量。

### 2.2 本地检索（P0）

- `POST /api/v1/retrieval/search`
- 先实现关键词检索（SQL + tsvector/BM25 近似），再接向量检索。
- 返回字段至少包含：文献标题、命中片段、页码。

### 2.3 AI 摘要（P0）

- `POST /api/v1/ai/summarize/{document_id}`
- 默认走本地模型适配器（如 Ollama），并提供 OpenAI 兼容适配接口。
- 输出统一 JSON：`summary/method/findings/limitations`。

### 2.4 引用生成（P0）

- `POST /api/v1/citations/generate`
- 先落地 APA + GB/T 7714 两种样式；MLA 放到 P1。
- 支持复制文本与导出 `.bib`。

---

## 3. 第三阶段（第 3-4 周）：可发布 Alpha

### 3.1 稳定性与可观测性（P1）

- 增加任务状态表/轮询接口（解析中、完成、失败）。
- 增加错误码规范与统一异常响应。
- 增加最小审计日志（模型调用次数、耗时、token）。

### 3.2 配置与隐私（P1）

- 设置页支持：模型供应商切换、本地模型地址、API Key 管理。
- 默认禁用云模型，用户显式启用后才可调用。

### 3.3 体验打磨（P1）

- 文献列表筛选（按年份/标签）。
- 检索结果可一键“生成摘要”和“生成引用”。

---

## 4. 建议立即创建的 Issues（可直接复制）

1. `feat(backend): initialize FastAPI project scaffold`
2. `feat(deploy): add docker-compose for local-first stack`
3. `feat(ingest): implement PDF import and hashing`
4. `feat(search): implement keyword retrieval API`
5. `feat(ai): implement summarize endpoint with model adapter`
6. `feat(citation): implement APA and GB/T citation generator`
7. `feat(frontend): add document library and search pages`
8. `chore(observability): add minimal audit/event logging`

---

## 5. 本周“最小交付目标”（Definition of Done）

满足以下 5 条即可进入下一阶段：

- 能通过 Web 页面上传 1 篇 PDF。
- 能在检索页搜到该文献的命中片段。
- 能点击按钮生成结构化摘要。
- 能导出至少 1 种格式的参考文献。
- 新人按 README + deploy 文档可在 15 分钟内跑起来。

---

## 6. 决策建议（避免一人项目失焦）

- **先闭环再优化**：先把功能串起来，不在首周追求最优检索质量。
- **单机优先**：所有能力先支持单机 docker，减少运维复杂度。
- **接口先行**：前后端并行时先锁定 API 契约，减少返工。
- **每周可演示**：每周至少有一个“可点击演示”的增量。
