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
│   ├── agent_core.yaml         
│   ├── data_engine_dnabert.yaml         
│   ├── data_engine.yaml         
│   ├── deep_research.yaml          # 文献检索配置
│   └── system.yaml                 # 系统级配置
├── data/
│   ├── real/                        # 真实生物数据（NCBI FASTA / RCSB PDB）
│   ├── demo_expression.csv          # 模拟表达矩阵
│   ├── demo_sequences.fasta       # 模拟 FASTA 序列
│   ├── demo_structure_1.pdb       # 模拟 PDB 结构
│   ├── demo_structure_2.pdb
│   ├── demo_structure_3.pdb
│   └── milvus_demo.db             # Milvus 本地文件数据库
├── logs/                            # 运行日志
├── models/
│   ├── bge-m3/                      # BGE-M3 模型文件
│   └── dnabert-2/                   # DNABERT-2 模型文件
├── modules/
│   ├── init.py
│   ├── agent_core/
│   │   ├── agents/
│   │   │   └── router_agent.py    # 路由 Agent
│   │   ├── memory/
│   │   │   ├── init.py
│   │   │   ├── base.py            # 记忆抽象基类
│   │   │   ├── entity_memory.py   # 实体记忆（Milvus JSON）
│   │   │   ├── long_term.py       # 长期记忆（Milvus 向量）
│   │   │   ├── memory_manager.py  # 四层记忆统一管理器
│   │   │   ├── retriever.py       # 记忆检索器
│   │   │   ├── short_term.py      # 短期记忆（Redis）
│   │   │   └── working_memory.py  # 工作记忆（Python 状态机）
│   │   ├── prompts/
│   │   │   ├── bio_analysis.txt   # 生物分析系统提示
│   │   │   ├── graph_rag.txt      # 知识图谱提示
│   │   │   ├── memory_update.txt  # 记忆更新提示
│   │   │   └── router.txt         # 路由提示
│   │   ├── templates/
│   │   │   └── index.html         # Web 前端页面
│   │   ├── tools/
│   │   │   ├── init.py
│   │   │   ├── analysis_tool.py   # 生物分析工具
│   │   │   ├── base.py            # 工具抽象基类
│   │   │   ├── search_tool.py     # 文献检索工具（模块C 封装）
│   │   │   └── vector_store.py    # 向量检索封装
│   │   └── web/
│   │       ├── init.py
│   │       ├── app.py             # FastAPI 主应用
│   │       ├── graph.py           # LangGraph 工作流
│   │       ├── llm_client.py     # 多平台 LLM 客户端
│   │       └── state.py           # Agent 状态定义
│   ├── data_engine/
│   │   ├── init.py
│   │   ├── pipeline.py            # 异步数据摄入 Pipeline
│   │   ├── loaders/
│   │   │   ├── init.py
│   │   │   ├── base.py            # 加载器基类
│   │   │   ├── csv_loader.py      # 表达矩阵加载
│   │   │   ├── fasta_loader.py    # FASTA 序列加载
│   │   │   ├── pdb_loader.py      # PDB 结构加载
│   │   │   └── pdf_loader.py      # PDF 文献加载
│   │   ├── milvus_platform/
│   │   │   ├── init.py
│   │   │   ├── hybrid_retriever.py # Hybrid Search（Dense+Sparse）
│   │   │   ├── manager.py         # Milvus Collection 管理
│   │   │   └── schema.py          # 字段定义
│   │   ├── preprocessors/
│   │   │   ├── init.py
│   │   │   ├── sequence_processor.py  # K-mer / 滑动窗口
│   │   │   ├── structure_processor.py # 结构处理
│   │   │   └── text_processor.py      # 文本预处理
│   │   ├── synthesizers/
│   │   │   ├── init.py
│   │   │   ├── sequence_synthesizer.py
│   │   │   └── text_synthesizer.py
│   │   └── vectorizers/
│   │       ├── init.py
│   │       ├── base.py            # 向量化器基类
│   │       ├── bge_m3_vectorizer.py
│   │       └── dnabert_vectorizer.py
│   ├── deep_research/
│   │   ├── init.py
│   │   ├── config.py              # 配置读取
│   │   ├── pipeline.py            # 端到端 Deep Research Pipeline
│   │   ├── processors/
│   │   │   ├── init.py
│   │   │   └── paper_processor.py # 去重 / 排序 / 格式化
│   │   ├── searchers/
│   │   │   ├── init.py
│   │   │   ├── arxiv_searcher.py  # Arxiv API 检索
│   │   │   ├── base.py            # 检索器基类
│   │   │   └── pubmed_searcher.py # PubMed E-utilities 检索
│   │   └── synthesizers/
│   │       ├── init.py
│   │       └── review_generator.py # LLM 自动综述
│   └── shared/
│       ├── init.py
│       ├── exceptions.py            # 自定义异常
│       └── logger.py                # 日志工具
├── notebooks/
│   └── 01_data_engine_quickstart.ipynb  # 模块A 交互式文档
├── scripts/
│   ├── deep_research_demo.py      # 模块C 命令行演示
│   ├── download_real_data.py      # 下载 NCBI/RCSB 真实数据
│   ├── generate_test_data.py      # 生成模拟数据
│   ├── ingest_demo.py             # 模拟数据摄入（BGE-M3）
│   ├── ingest_dnabert_demo.py     # 模拟数据摄入（DNABERT-2）
│   ├── ingest_real_data.py        # 真实数据摄入（BGE-M3）
│   ├── init_db.py                 # 初始化 BGE-M3 数据库
│   ├── init_db_dnabert.py        # 初始化 DNABERT-2 数据库
│   └── run_web.py                 # 启动 Web 服务
├── venv/                            # Python 虚拟环境
├── README.md
└── requirements.txt                  
```

---