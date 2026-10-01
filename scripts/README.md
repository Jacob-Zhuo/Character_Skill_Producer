# CSP Scripts 说明

本目录是 CSP（Character Skill Producer）的本地脚本。它们承担**核心站点检索、来源归一化、调研检查点、metadata 生成与质量验证**，供生成角色技能时按流程调用。

> 环境注意：Windows 本机使用 `python`（无 `python3` 别名）；路径使用正斜杠。
> 所有脚本输出均为可读 JSON / 表格，主要供「执行者（AI 代理或人）」阅读判断，不构成机器管道中间产物。

## 脚本总览

| 脚本 | 作用 | 产出 | 调用时机（流程 Phase） |
|---|---|---|---|
| `source_search.py` | 统一本地资料检索入口（面向对象 + 表驱动） | stdout JSON：`records[]` + `cross_media_hint` | **Phase 1** 来源发现 |
| `source_registry.py` | 来源分级、排除域名、作品提示、跨媒体规则 | 无独立输出（库） | 随 `source_search.py` 自动加载，无需直接调用 |
| `moegirl_api.py` | 萌娘百科 MediaWiki API 封装 | stdout JSON：条目正文/简介/候选/原文 | **Phase 1/3** 检索核心站点 |
| `bwiki_api.py` | BWIKI（biligame）MediaWiki API 封装 | stdout JSON：游戏百科条目 | **Phase 1/3** 检索手游角色数据 |
| `merge_research.py` | 研究摘要与检查点生成器 | 终端表格报告（不写文件） | **Phase 5** 调研质量检查点 |
| `generate_manifest.py` | 生成 / 更新 `manifest.json` | 写 `manifest.json` | **Phase 8** 构建 Skill 与 manifest |
| `quality_check.py` | 生成技能质量检查 | 写 `references/quality-report.json` | **Phase 9** 质量验证 |

---

## 各脚本详情

### 1. `source_search.py` — 统一本地检索入口

- **作用**：按 `--sources`（缺省时按作品名推断）依次调用各本地源 adapter（当前：moegirl、bwiki、mediawiki），把结果归一化成标准 `sources.json` 记录格式。
- **何时调用**：Phase 1「Source Discovery」的第一步，任何生成任务开始都必须先跑它。
- **输出**：`{ok, query, work, mode, retrieved_at, cross_media_hint, sources_requested, records[], warnings}`。`records[]` 含命中（`status=ok`）与失败（`status=failed + error`）；`cross_media_hint=true` 时触发跨媒体规则。
- **示例**：
  ```bash
  python scripts/source_search.py "藤都子" --work "梦限大MewType" --mode discover
  python scripts/source_search.py "能天使" --work "明日方舟" --sources moegirl,bwiki
  ```
- **内部**：通过子进程调用 `moegirl_api.py` / `bwiki_api.py` 并追加 `--timeout`；记录 `retrieved_by`（实际命令串）与 `command_status`。

### 2. `source_registry.py` — 来源规则库

- **作用**：维护来源分级（`SOURCE_TIERS`）、排除域名（知乎/微信公众号/百度百科）、按作品推荐来源（`WORK_SOURCE_HINTS`）、跨媒体作品清单（`CROSS_MEDIA_WORKS`），提供 `source_tier()` / `source_hints_for_work()` / `is_cross_media_work()` / `is_excluded_url()`。
- **何时调用**：不独立执行；由 `source_search.py` 导入。需要改来源规则时直接编辑本文件。

### 3. `moegirl_api.py` — 萌娘百科封装

- **作用**：通过 MediaWiki API 获取萌娘百科词条。四种互斥模式：
  - `--intro`：按精确标题拉简介（`exintro`），失败自动回退搜索
  - `--full`：拉全文纯文本（TextExtracts，`explaintext`）
  - `--search`：`action=opensearch` 标题前缀搜索候选
  - `--wikitext`：通过 `revisions` API 取原始 wikitext（权限受限，可能失败）
- **默认（无模式标志）**：走 `auto_query` 降级链——简介 → 搜索 → 首个候选简介 → 回退错误，并把尝试路径写进 `attempted_modes`（失败留证）。
- **何时调用**：Phase 1（经 `source_search.py` 间接调用）与 Phase 3（研究维度缺料时直接调用补缺）。
- **示例**：
  ```bash
  python scripts/moegirl_api.py "角色名" --intro
  python scripts/moegirl_api.py "角色名" --full
  python scripts/moegirl_api.py "角色名" --search
  ```
- **结构**：OOP 实现，核心为 `MoegirlApiClient` 类（HTTP/URL 层、结果构造、低层查询、`auto_query` 降级链）。`User-Agent` 标识客户端与回链仓库，需与项目仓库一致。

### 4. `bwiki_api.py` — BWIKI 封装

- **作用**：通过 BWIKI（biligame）MediaWiki API 获取游戏百科词条，覆盖米哈游系等手游角色数据。与 moegirl 同为中文源补充。
- **差异**：BWIKI 不支持 TextExtracts 扩展，因此 `--intro/--full` 实际走「抓取 wikitext → 解析信息框 `|介绍=`」的降级路径；请求带重试（`retries=2`）。
- **何时调用**：Phase 1/3，检索手游角色时经 `source_search.py` 传入 `--sources bwiki`，或直接调用。
- **示例**：
  ```bash
  python scripts/bwiki_api.py "能天使" --game 明日方舟
  python scripts/bwiki_api.py "角色名" --game sr --full
  ```
- **参数**：`--game` 支持游戏名或 slug（`sr`/`arknights`/`ba`/…），缺省时尝试从查询词推断。

### 5. `merge_research.py` — 调研摘要与检查点

- **作用**：汇总 `references/research/` 六个研究文件的来源数、关键发现、矛盾、缺失维度，并汇总 `sources.json` 的 ok/failed/缺日期/层级分布/最新检索日期，给出整体置信度（HIGH/MEDIUM/LOW）。
- **何时调用**：Phase 5「调研质量检查点」——写完 01~06 研究文件后、行为蒸馏前运行一次。存在黑名单来源时以非零码退出。
- **输出**：仅终端表格 + 告警，**不写任何文件**。执行者读它决定「进入蒸馏」还是「补充调研」。
- **示例**：
  ```bash
  python scripts/merge_research.py output/fuji-miyako
  ```

### 6. `generate_manifest.py` — manifest 生成 / 更新

- **作用**：根据 `SKILL.md`、`sources.json`、`research/06-media-coverage.md` 生成或更新 `manifest.json`（含 `research_completed_at`、`latest_source_checked_at`、`covered_until`、`source_count`、`source_tiers`、`covered_media` 等必填字段）。
- **何时调用**：Phase 8「构建 Skill 与 manifest」；更新已有技能时重新运行。`--character` / `--work` 用于补充显示名。
- **注意**：`covered_media` 会复用已存在的旧值；若 `06-media-coverage.md` 结构调整，需删除旧 `manifest.json` 后重新生成。
- **示例**：
  ```bash
  python scripts/generate_manifest.py output/fuji-miyako --character "藤都子" --work "梦限大MewType（BanG Dream! 企划）"
  ```

### 7. `quality_check.py` — 质量验证

- **作用**：对技能目录或单个 `SKILL.md` 执行 11 项检查：行为模式数、表达质感、矛盾保留、角色扮演规则、行为示例、诚实边界、来源标注、manifest、sources.json、资料时间边界与更新回应、研究文件完整性。
- **何时调用**：Phase 9「质量验证」，交付前的最后一道门；更新技能后也要重跑。结果写入 `references/quality-report.json`。
- **判定**：11/11 通过才可声称完成；未通过项会打印 FAIL 详情，且失败数超过一项时以非零码退出。
- **示例**：
  ```bash
  python scripts/quality_check.py output/fuji-miyako
  python scripts/quality_check.py output/fuji-miyako/SKILL.md
  ```

---

## 调用时机一览（对照 SKILL.md 执行流程）

| Phase | 动作 | 涉及脚本 |
|---|---|---|
| Phase 1 Source Discovery | 本地检索起点情报 | `source_search.py`（内部调 `moegirl_api.py` / `bwiki_api.py`） |
| Phase 2 建目录与来源索引 | 归档 `references/sources.json` | （人工/agent 汇总检索结果，无需脚本） |
| Phase 3 多源信息采集 | 维度缺料时直接补搜 | `moegirl_api.py` / `bwiki_api.py` |
| Phase 4 跨媒体覆盖 | 写 `06-media-coverage.md` | （文档，无需脚本） |
| Phase 5 调研质量检查点 | 检查研究完整度 | `merge_research.py` |
| Phase 6 行为蒸馏 | 写 `distillation.md` | （文档，无需脚本） |
| Phase 7 蒸馏确认 | 向用户展示 | （人工，无需脚本） |
| Phase 8 构建 Skill 与 manifest | 组装 `SKILL.md` + 生成 metadata | `generate_manifest.py` |
| Phase 9 质量验证 | 交付前检查 | `quality_check.py` |

> 外部网页搜索（搜索 skill / MCP / WebFetch）不在本目录：仅作本地脚本未覆盖或失败时的补强，且需在 `sources.json` 记录。
> 本仓库无构建步骤、常规测试套件；最接近的验证手段即 `merge_research.py` / `generate_manifest.py` / `quality_check.py`。