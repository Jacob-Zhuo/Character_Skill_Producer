# 未覆盖媒体补调研脚本设计文档

> 状态：待评审
> 目标：把「跨媒体角色补调研未覆盖媒体」这一人工步骤，提炼为可复用、可追踪、可恢复的 `coverage_research.py` 脚本。
> 触发背景：藤都子 Skill 的 `references/research/06-media-coverage.md`「未覆盖媒体/缺口」记录了游戏《交织的乐章》剧情文本、动画 BD 特典/逐集台词、47 都道府县巡演后续、中之人访谈等未覆盖项（另有「已覆盖但未细读」的广播、有声漫画）；`manifest.json.not_covered` 目前仅含默认资料边界提示语，不逐项列出。当前补调研靠人工判断，无工具支撑。

---

## 一、现状与问题

当前 CSP 调研链路（SKILL.md Phase 3–6）：

```text
source_search.py / moegirl_api.py / bwiki_api.py   ← 本地检索
      ↓
五条研究线 research/01~05
      ↓
06-media-coverage.md  ← 记录已覆盖/未覆盖媒体（人工维护）
      ↓
distillation.md → SKILL.md → generate_manifest.py → quality_check.py
```

**问题**：

1. `06-media-coverage.md` 的「未覆盖媒体」列表**只记录、不推动**——写完后没有人负责去补。
2. 跨媒体角色（BanG Dream! 等）必须覆盖相关作品，但**补调研的触发完全依赖 agent 自觉**，无强制检查。
3. `manifest.json.not_covered` 是静态快照，**没有「尝试补过、失败原因」的追踪记录**。
4. 现有的 `source_search.py` 是「按角色名检索」入口，**没有「按媒体类型补调研」的入口**（如：抓游戏剧情、抓广播节目词条、抓巡演活动页）。

## 二、设计目标

1. **一个命令补一项媒体**：`python scripts/coverage_research.py <skill_dir> --media "game_story"`，按媒体类型补齐该 Skill 的未覆盖项。
2. **自动分类**：从 `manifest.json.not_covered` 中识别媒体类型，映射到对应适配器。
3. **可追踪**：每次尝试（成功/失败）都写回 `sources.json`（`status=failed` 记录失败原因），并更新 `06-media-coverage.md` 与 `manifest.json.not_covered`。
4. **可恢复/幂等**：已覆盖的媒体跳过，失败的可重试；支持 `--media` 定向、`--only-uncovered` 只处理未覆盖项。
5. **不改变核心流程**：它是 Phase 4 的辅助工具，不替代五条研究线和蒸馏。

## 三、媒体类型 → 适配器映射

### 3.1 媒体类型枚举（参考 `source-output-schema.md` 的 `media_type`）

| media_type | 含义 | 示例 |
|---|---|---|
| `game_story` | 游戏主线/活动剧情 | 交织的乐章、Garupa 卡牌剧情 |
| `event_story` | 游戏活动剧情 | Bestdori 活动脚本 |
| `card_story` | 卡牌剧情 | Bestdori |
| `broadcast` | 广播/电台节目 | 梦限大MewType的「YUME∞MITA RADIO」 |
| `voice_drama` | 有声漫画/广播剧 | 《梦现妄想世界》《BIG MOUTH》 |
| `anime_spinoff` | 动画衍生 | 《元祖！BanG Dream Chan》 |
| `tour` | 巡演/线下活动 | 47都道府县制霸之旅 |
| `interview` | 访谈 | animatetimes 对谈 |
| `official_article` | 官方专栏/note | 都子 note 博客 |
| `manual` | 需人工提供（设定集/BD特典） | 用户官方材料 |

> 注：上表是对 `references/source-output-schema.md` 中 `media_type`（「可用值示例」，非穷举）的**扩展提案**；其中 `manual` 对应 schema 中用户提供材料的 `user_material`，实现时统一命名并回写 schema 文档。

### 3.2 适配器矩阵

| media_type | 首选适配器 | 兜底适配器 | 说明 |
|---|---|---|---|
| `game_story` | `source_search.py --sources bwiki` 或 Bestdori | `moegirl_api.py --full` | BWIKI 覆盖米哈游系；Bestdori 覆盖 BanG Dream!（Garupa/交织的乐章） |
| `event_story` | Bestdori | `moegirl_api.py --search` | 活动剧情 |
| `card_story` | Bestdori | — | 卡牌剧情 |
| `broadcast` | `moegirl_api.py --search/--full` | 官方站点 WebFetch | 广播节目词条 |
| `voice_drama` | `moegirl_api.py --search/--full` | 官方 note/YouTube | 有声漫画 |
| `anime_spinoff` | `moegirl_api.py --full` | 官方站点 | 衍生动画词条 |
| `tour` | 官方站点 WebFetch | `moegirl_api.py --search` | 巡演活动页 |
| `interview` | 官方站点/动画官网 | WebFetch | 访谈原文 |
| `official_article` | 官方 note/站点 | WebFetch | 专栏 |
| `manual` | **不可自动化** | — | 需用户提供，脚本只登记为 `requires_user_material` |

> 注意：`manual` 类型不是失败，是「设计上必须由用户提供」——脚本应把它从 `not_covered` 移入 `requires_user_material`，而不是标记失败。

## 四、CLI 设计

```bash
python scripts/coverage_research.py <skill_dir> [options]

# 查看该 Skill 的未覆盖媒体及自动分类结果（不改文件）
python scripts/coverage_research.py output/fuji-miyako --dry-run

# 只补某一类媒体
python scripts/coverage_research.py output/fuji-miyako --media game_story,broadcast

# 默认：只处理仍未覆盖的项，结果写回 sources.json / 06-media-coverage.md / manifest.json
python scripts/coverage_research.py output/fuji-miyako
```

参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `skill_dir` | 必填 | 生成的技能目录 |
| `--media` | 全部 | 逗号分隔的 media_type 过滤 |
| `--only-uncovered` | 默认开 | 跳过已覆盖项；`--no-only-uncovered` 强制重跑 |
| `--dry-run` | 关 | 只分析、输出计划，不写文件 |
| `--timeout` | 20 | 每个适配器超时 |
| `--adapter-extra` | 无 | 透传适配器参数（如 `bwiki --game`） |

## 五、数据流

```text
输入
├── manifest.json.not_covered[]          ← 未覆盖列表
├── references/sources.json[]            ← 已有来源（用于幂等去重）
└── references/research/06-media-coverage.md  ← 现状

处理
├── 1. classify_media_type(item)         ← 从文本识别 media_type（关键词+正则）
├── 2. build_adapter_plan(media_type)    ← 查适配器矩阵，生成命令
├── 3. check_already_covered(item)       ← 与 sources.json / 06 比对，跳过已覆盖
├── 4. run_adapter(plan)                 ← 执行 source_search.py / moegirl_api.py / WebFetch 等价调用
└── 5. record_result(record)             ← 成功或失败都写入

输出
├── sources.json[]                       ← append 新记录（status=ok/failed）
├── 06-media-coverage.md                 ← 更新「已覆盖媒体 / 未覆盖媒体」章节
├── manifest.json.not_covered            ← 移除已覆盖项；failed 项保留并标注 last_attempt
└── stdout 摘要                          ← 每个未覆盖项：类型 → 结果 → 来源 id
```

### 5.1 失败记录格式（追加到 sources.json）

```json
{
  "id": "coverage-broadcast-yumemita-radio",
  "source": "coverage_research",
  "title": null,
  "url": null,
  "query": "夢限大みゅーたいぷの「ゆめ∞みたラジオ」",
  "work": "梦限大MewType",
  "source_tier": "high",
  "officiality": "secondary",
  "media_type": "broadcast",
  "language": "ja",
  "retrieved_at": "2026-10-01",
  "status": "failed",
  "error": "not_found",
  "warnings": ["coverage_research: 广播节目无独立词条，需官方站点或用户提供收听记录"],
  "attempted_modes": ["moegirl_search", "web_fetch"]
}
```

## 六、与现有脚本的关系

| 现有脚本 | 关系 |
|---|---|
| `source_registry.py` | 新增 `MEDIA_TYPE_HINTS`、`MEDIA_ADAPTER_MATRIX` 常量；复用 `source_tier()` |
| `source_search.py` | 直接调用它作为适配器（`--sources moegirl/bwiki`）；新增 `--media` 语法可后续再加 |
| `moegirl_api.py` / `bwiki_api.py` | 通过 `run_python_script`（source_search 的既有机制）调用 |
| `merge_research.py` | 不变；补调研后重新跑它即可反映新来源 |
| `generate_manifest.py` | 不变；脚本自行更新 `not_covered` |
| `quality_check.py` | 新增一条检查：`not_covered` 中是否存在 `requires_user_material` 或「多次失败但无记录」的项（可选，见第九节） |

## 七、分类规则（classify_media_type）

基于 `not_covered` 文本与 `06-media-coverage.md` 标题的关键词映射：

| 关键词（中/日/英） | media_type |
|---|---|
| 游戏 / 交织的乐章 / Garupa / 剧情 | `game_story` |
| 活动剧情 / 活动脚本 / event | `event_story` |
| 卡面剧情 / 卡牌 / card | `card_story` |
| 广播 / ラジオ / radio | `broadcast` |
| 有声漫画 / 音声 / ドラマ / drama | `voice_drama` |
| 动画衍生 / 元祖 / spinoff / chibi | `anime_spinoff` |
| 巡演 / 制霸 / tour / live | `tour` |
| 访谈 / 对谈 / interview | `interview` |
| note / 专栏 / 官方博客 / blog | `official_article` |
| 设定集 / BD特典 / 官方材料 / 字幕 / 截图 | `manual` |

未匹配 → 默认 `manual`（安全降级，避免自动检索未知媒体）。

## 八、幂等与更新策略

- **not_covered 结构约束**：当前 schema 中 `manifest.not_covered` 是**字符串列表**（如默认的资料边界提示语），写不下「带 `last_attempt_at` 的失败项」。实现脚本写入结构化失败项前，需先扩展该字段结构并同步 `references/source-output-schema.md`（例如改为 `[{item, media_type, last_attempt_at, status}]` 或拆出独立字段）。
- **已覆盖判定**：`sources.json` 中存在 `status=ok` 且 `media_type` 相同、`work` 相同，或 `06-media-coverage.md`「已覆盖媒体」表已含该条目 → 跳过。
- **失败重试**：失败项写入 `not_covered` 时附 `last_attempt_at`；`--force` 或超过 7 天可重试。
- **时间线边界**：每次补调研更新 `manifest.latest_source_checked_at` 与 `covered_until`，提示 SKILL.md 的资料日期需同步刷新。

## 九、可选增强（本期不做，仅记录）

1. `quality_check.py` 新增检查：跨媒体作品（`is_cross_media_work`）若 `not_covered` 非空且无 `requires_user_material`/`last_attempt_at` 记录，输出 warning。
2. 新增 Bestdori 适配器 `bestdori_api.py`（BanG Dream! 活动/卡面剧情），纳入适配器矩阵的兜底列。
3. `generate_manifest.py` 支持 `--sync-covered` 从 `06-media-coverage.md` 回写 `covered_media`。
4. WebFetch 桥接：由于本地脚本不覆盖官方站点/note，设计 `coverage_research.py --adapter web` 调用外部检索（搜索 skill / MCP），失败仍记录原因。

## 十、实施步骤

1. `source_registry.py`：新增 `MEDIA_TYPE_HINTS`、`MEDIA_ADAPTER_MATRIX`、`classify_media_type()`。
2. 新建 `scripts/coverage_research.py`：CLI + 分类 + 适配器执行 + 幂等 + 写回。
3. `AGENTS.md` / `SKILL.md`：在 Phase 4 后补充可选步骤「补调研未覆盖媒体」，登记命令。
4. 对藤都子 Skill 试跑：补 `game_story`（交织的乐章）、`broadcast`、`voice_drama`，更新 `06-media-coverage.md` 与 `manifest.json`。
5. 回归：`merge_research.py`、`generate_manifest.py`、`quality_check.py` 全绿。

## 十一、风险与决策点

| 风险/决策 | 说明 | 建议 |
|---|---|---|
| 自动化能补的有限 | 游戏剧情/广播/有声漫画的原文大多在付费或封闭平台 | 脚本负责「检索公开词条+登记缺口」，原文获取仍需用户提供或人工转录 |
| WebFetch 桥接 | 本地脚本无官方站点适配器 | 本期用 `manual` 或用户提供 URL；第 4 条增强再引入 web 桥接 |
| 误分类 | `not_covered` 文本五花八门 | 分类表只覆盖常见词；未匹配默认 `manual` 安全降级 |
| `not_covered` 与 SKILL.md 资料边界不一致 | 补调研后日期变化 | 每次写回后提示「建议同步 SKILL.md 资料时间边界」 |

---

## 附：本轮改动范围

- **新增**：`docs/coverage-research-design.md`（本文档）
- **待实现**（评审通过后）：`scripts/coverage_research.py`、`source_registry.py` 的 `MEDIA_TYPE_HINTS`/`MEDIA_ADAPTER_MATRIX`
- **待修改**：`AGENTS.md`（Phase 4 补调研命令）、`SKILL.md`（可选步骤）
- **不改**：`merge_research.py`、`generate_manifest.py`、`bwiki_api.py` 核心逻辑。
- **后续变更（不影响本设计）**：`moegirl_api.py` 已按面向对象重构为 `MoegirlApiClient`（CLI 参数、stdout JSON 结构、退出码均不变），`source_search.py` 的 `run_python_script` 调用方式仍兼容。