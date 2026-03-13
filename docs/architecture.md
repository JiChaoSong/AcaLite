# AcaLite 系统架构设计（MVP）

> 目标：围绕「本地部署、隐私优先、轻量可扩展」设计一人公司可落地的技术架构，支撑 6 个月 MVP。

## 1. 设计原则

1. **本地优先（Local-first）**：文献文件、向量索引、用户配置默认本地存储。
2. **可替换（Provider-agnostic）**：模型、向量库、解析引擎均通过适配层解耦。
3. **轻量单体 + 模块化**：MVP 采用模块化单体，降低部署复杂度；后续可按模块拆分微服务。
4. **隐私与合规优先**：不默认上传用户文献到公有云；云 API 调用由用户显式配置并可审计。
5. **开源友好**：插件化扩展点优先暴露在解析、模型、引用格式、导出能力。

---

## 2. 功能到模块映射

### 2.1 本地文献管理与导入

- **Document Ingestion 模块**
  - PDF 批量导入、去重（文件哈希）
  - 元数据提取（标题、作者、年份、DOI）
  - 文档切分与索引任务入队
- **Library 模块**
  - 文献目录、标签、文件夹、关键词分类
  - 预览状态与基础标注（高亮/笔记锚点）

### 2.2 AI 文献智能解读

- **LLM Service 模块**
  - 统一接入本地模型（Ollama/vLLM）与云模型（OpenAI 兼容接口）
  - Prompt 模板：摘要、方法、贡献、局限、结论、翻译
- **Knowledge Extractor 模块**
  - 结构化抽取：研究问题、方法、实验、结果
  - 简易思维导图数据输出（节点/边 JSON）

### 2.3 本地检索与引用生成

- **Retrieval 模块（RAG）**
  - 混合检索：关键词（BM25）+ 向量检索
  - 结果重排与引用片段定位
- **Citation 模块**
  - 支持 APA / MLA / GB/T 7714
  - 参考文献列表导出（Markdown / BibTeX）

---

## 3. 总体架构（MVP）

```text
+--------------------+          +--------------------------------+
|   Vue Frontend     | <------> |        FastAPI Backend         |
| - 文献库/检索/解读  |   HTTP   | - Auth(本地) / API / RBAC(简化) |
+--------------------+          +--------------------------------+
                                          |         |          |
                                          |         |          |
                                          v         v          v
                                 +-------------+ +--------+ +----------------+
                                 | PostgreSQL  | | Redis  | | Object Storage |
                                 | 元数据/标注   | | 队列/缓存 | | 本地文件系统     |
                                 +-------------+ +--------+ +----------------+
                                          |
                                          v
                                  +------------------+
                                  | Vector Index     |
                                  | pgvector/Qdrant  |
                                  +------------------+
                                          |
                                          v
                     +----------------------------------------------+
                     | Model Gateway                               |
                     | - Local: Ollama/vLLM                        |
                     | - Cloud: OpenAI-compatible API              |
                     +----------------------------------------------+
```

> 单机部署建议：`docker compose` 一键启动（api/web/postgres/redis）。

---

## 4. 技术选型建议

- **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus（或 Naive UI）
- **后端**：Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy
- **任务队列**：Celery / RQ（二选一，MVP 推荐 RQ 更轻量）
- **数据库**：PostgreSQL（统一管理业务数据）
- **向量检索**：
  - MVP：`pgvector`（减少组件数量）
  - 扩展：Qdrant（检索规模上来后独立）
- **文档解析**：PyMuPDF + pdfplumber（双引擎兜底）
- **模型接入**：
  - 本地推理：Ollama（简化部署）
  - 云推理：OpenAI-compatible adapter
- **部署**：Docker Compose（MVP），K8s（后期私有化企业版）

---

## 5. 关键数据模型（简版）

- `documents`
  - `id`, `title`, `authors`, `year`, `doi`, `file_path`, `file_hash`, `created_at`
- `document_chunks`
  - `id`, `document_id`, `chunk_index`, `content`, `embedding`, `page_no`
- `annotations`
  - `id`, `document_id`, `user_id`, `anchor`, `content`, `type`, `created_at`
- `ai_reports`
  - `id`, `document_id`, `summary`, `methods`, `findings`, `limitations`, `mindmap_json`
- `citations`
  - `id`, `document_id`, `style`, `formatted_text`, `bibtex`

---

## 6. 核心流程设计

### 6.1 导入与索引流程

1. 用户上传 PDF（本地或拖拽）。
2. 计算哈希并检查重复。
3. 解析元数据与全文文本。
4. 文本切分（按段落/Token）。
5. 生成向量并入库（pgvector/Qdrant）。
6. 更新检索可用状态。

### 6.2 AI 解读流程

1. 用户在文献详情点击“智能解读”。
2. 后端检索关键片段 + 元数据。
3. 调用 LLM 生成结构化结果。
4. 落库 `ai_reports`，前端展示摘要/方法/结论/翻译。
5. 可选导出 Markdown 报告。

### 6.3 引用生成流程

1. 用户选择文献或检索结果。
2. 解析元数据缺失项（可手工修正）。
3. 按引用格式模板渲染。
4. 导出参考文献列表/BibTeX。

---

## 7. API 分层设计（示例）

- `/api/v1/documents`
  - `POST /import`, `GET /`, `GET /{id}`, `DELETE /{id}`
- `/api/v1/retrieval`
  - `POST /search`（关键词/自然语言）
- `/api/v1/ai`
  - `POST /summarize/{document_id}`
  - `POST /translate/{document_id}`
- `/api/v1/citations`
  - `POST /generate`, `GET /styles`
- `/api/v1/annotations`
  - `POST /`, `GET /document/{id}`

---

## 8. 安全与隐私设计

- 默认关闭云模型调用；首次启用需用户确认。
- API Key 本地加密存储（系统密钥 + 环境变量）。
- 文献与索引数据可配置目录；支持一键本地备份。
- 审计日志记录模型调用时间、模型名、Token 用量（不记录原文全文）。

---

## 9. 6 个月落地计划（架构视角）

- **M1-M2（基础底座）**
  - 文献导入、元数据解析、数据库模型、基础检索
- **M3-M4（AI 核心）**
  - LLM 网关、结构化解读、翻译、思维导图 JSON
- **M5（写作支持）**
  - 引用格式引擎、BibTeX/Markdown 导出
- **M6（发布与开源）**
  - Docker Compose、文档、示例数据、插件接口草案

---

## 10. 后续演进路线（开源生态）

1. 插件系统：解析器、模型供应商、导出器可插拔。
2. 多人协作：小组空间、评论、权限（B 端种子用户）。
3. 企业私有化：LDAP/SSO、审计增强、离线模型包。
