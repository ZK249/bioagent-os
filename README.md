# BioAgent-OS

面向生物信息学的多智能体系统。支持真实生物数据（NCBI/RCSB）的异步向量化处理、基于 LangGraph 的多 Agent 协作、以及 PubMed/Arxiv 文献自动检索与综述生成。

---

## 技术栈

| 层级 | 技术方案 |
|------|----------|
| 数据引擎 | Python asyncio, Biopython, Milvus (本地文件模式), BGE-M3 / DNABERT-2 |
| Agent 核心 | FastAPI, LangGraph, Redis, Milvus JSON 实体记忆 |
| 文献检索 | PubMed E-utilities, Arxiv API, DeepSeek/Kimi LLM |
| 部署 | 零 Docker，纯 Python，16GB 内存可运行 |

---

## 系统架构

BioAgent-OS 由三个独立模块自下而上堆叠：

**模块A（数据引擎层）**：负责生物数据的加载、预处理、向量化与存储。
- 输入：FASTA 序列、PDB 结构、文献文本、表达矩阵
- 处理：K-mer Tokenizer → 双模型向量化（BGE-M3 或 DNABERT-2）→ Milvus 本地文件模式
- 输出：可语义检索的向量知识库，供模块B调用

**模块B（Agent-Core 层）**：负责多智能体协作、记忆管理与用户交互。
- LangGraph 编排：Router → Research Agent / Data Analyst → Memory Agent
- 四层记忆：Redis 短期记忆、Milvus 长期记忆、Milvus JSON 实体记忆、Python 工作记忆
- LLM 客户端：支持 Kimi / DeepSeek / OpenAI / DashScope / Anthropic 配置化切换
- Web 服务：FastAPI 提供前端页面 + `/api/chat` + `/api/clear`

**模块C（Deep Research 层）**：负责文献检索与自动综述，作为模块B的扩展工具。
- 双源检索：PubMed（优先，稳定）+ Arxiv（超时自动降级）
- 自动综述：基于真实文献摘要，调用 LLM 生成结构化综述
- 集成方式：通过 `ToolRegistry` 注册表松耦合注册，ResearchAgent 通过名称调用

**数据流（一次完整请求）**：
1. 用户输入查询 → FastAPI 接收
2. Router Agent 路由 → Research Agent
3. Research Agent 提取关键词 → `ToolRegistry.call("deep_research")`
4. 模块C 检索 PubMed/Arxiv → 去重排序 → 返回 Top 论文 + 综述
5. Research Agent 基于真实文献让 LLM 生成最终回答
6. Memory Agent 写入四层记忆
7. 前端返回：左侧回复 + 右侧记忆面板实时更新

---

## 模块说明

### 模块A：数据引擎 (`modules/data_engine/`)

- **Loaders**: FASTA / PDB / 文献 / 表达矩阵加载
- **Vectorizers**: BGE-M3 (Dense 1024 + Sparse) + DNABERT-2 (Dense 768)
- **Storage**: Milvus 本地文件模式 (`data/milvus_demo.db`)，零 Docker
- **Search**: Hybrid Search (RRF 融合)，小数据量自动降级 Dense Search

**验证结果**：基于 NCBI 15 条 TP53 序列 + RCSB 5 个 PDB 结构，Top 5 检索全部命中 TP53。

### 模块B：Agent-Core (`modules/agent_core/`)

- **四层记忆**：Redis 短期记忆、Milvus 长期记忆、Milvus JSON 实体记忆、Python 工作记忆
- **多智能体**：BioResearcher / DataAnalyst，关键词路由
- **LLM 切换**：支持 Kimi / DeepSeek / OpenAI / DashScope / Anthropic（配置化切换）
- **Web UI**：FastAPI + 内嵌前端，实时展示四层记忆状态

### 模块C：Deep Research (`modules/deep_research/`)

- **多源检索**：PubMed（优先，国内稳定）+ Arxiv（超时自动降级）
- **自动综述**：基于检索到的真实文献，调用 LLM 生成结构化综述
- **集成方式**：通过 `ToolRegistry` 注册，ResearchAgent 自动识别检索意图并调用

---

## 快速开始

```bash
# 1. 进入项目
cd ~/projects/bioagent-os
source venv/bin/activate

# 2. 启动 Redis
sudo service redis-server start

# 3. 设置 LLM API Key（以 DeepSeek 为例）
export DEEPSEEK_API_KEY=sk-your-key

# 4. 启动 Web 服务
python scripts/run_web.py

# 5. 打开浏览器
# http://127.0.0.1:8000
```

### 单独运行模块C 演示

```bash
python scripts/deep_research_demo.py
```

---

## 项目结构

```
bioagent-os/
├── configs/
│   ├── data_engine.yaml              # 数据引擎配置
│   ├── data_engine_dnabert.yaml    # DNABERT-2 隔离配置
│   ├── agent_core.yaml             # Agent 配置（LLM provider 切换）
│   └── deep_research.yaml          # 文献检索配置
├── data/
│   ├── real/                        # 真实生物数据（NCBI FASTA / RCSB PDB）
│   ├── milvus_demo.db              # BGE-M3 向量库
│   └── milvus_dnabert.db          # DNABERT-2 向量库
├── models/
│   └── dnabert-2/                  # 本地 DNABERT-2 模型文件
├── modules/
│   ├── agent_core/
│   │   ├── agents/                  # Router / Research / Data / Memory
│   │   ├── memory/                  # 四层记忆实现
│   │   ├── tools/                   # 工具注册表 + 生物分析工具
│   │   ├── prompts/                 # 系统提示词（txt 文件）
│   │   ├── rag/                     # 向量检索封装
│   │   ├── web/                     # FastAPI 应用
│   │   ├── llm_client.py           # 多平台 LLM 客户端
│   │   ├── graph.py                # LangGraph 工作流
│   │   └── state.py                # Agent 状态定义
│   ├── data_engine/
│   │   ├── loaders/                 # FASTA / PDB / 文献 / 表达矩阵
│   │   ├── vectorizers/            # BGE-M3 / DNABERT-2
│   │   ├── milvus_platform/        # Milvus 管理 + Hybrid Search
│   │   ├── preprocessors/          # K-mer / 滑动窗口 / 结构处理
│   │   └── pipeline.py             # 异步摄入 Pipeline
│   ├── deep_research/
│   │   ├── searchers/              # PubMed / Arxiv 检索器
│   │   ├── processors/             # 去重 / 排序 / 格式化
│   │   ├── synthesizers/           # LLM 自动综述生成
│   │   ├── config.py               # 配置读取
│   │   └── pipeline.py            # 端到端 Pipeline
│   └── shared/
│       └── logger.py              # 日志工具
├── scripts/
│   ├── init_db.py                  # 初始化 BGE-M3 数据库
│   ├── init_db_dnabert.py         # 初始化 DNABERT-2 数据库
│   ├── download_real_data.py      # 下载 NCBI/RCSB 真实数据
│   ├── ingest_real_data.py        # 摄入真实数据（BGE-M3）
│   ├── ingest_dnabert_demo.py    # 摄入真实数据（DNABERT-2）
│   ├── agent_demo.py              # 模块B 命令行演示
│   ├── deep_research_demo.py     # 模块C 命令行演示
│   └── run_web.py                 # 启动 Web 服务
├── templates/
│   └── index.html                 # 前端页面（Agent 对话 + 记忆面板）
├── notebooks/
│   └── 01_data_engine_quickstart.ipynb  # 模块A 交互式文档
└── README.md                     
```

---