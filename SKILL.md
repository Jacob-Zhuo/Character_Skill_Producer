---
name: ccp
description: |
  二次元角色写作用角色卡蒸馏器。输入角色名+作品名，本地检索核心资料→交叉验证→行为蒸馏→生成可追溯、可更新的写作用角色卡（Character Card）。
  角色卡供 AI 辅助写作与场景/剧本设计时作为参考规范引用：让 AI 以作者/叙述者视角写出符合角色行为逻辑的场景、对白和内心戏，并在设计剧情、场景时避免 OOC。
  触发词：「生成XX的角色卡」「蒸馏XX」「做一个XX角色卡」「把XX变成角色卡」「让AI写XX的同人」「写XX怕OOC」「/ccp」。
  模糊需求也触发：「想写一个傲娇角色的同人」「帮我做一个XX作品里的角色」。
  依赖 Python；核心站点优先走本地脚本，网页搜索 skill / MCP / WebFetch 只作为补强和失败兜底。
---

# CCP · Character Card Producer

> 把二次元角色蒸馏成写作用角色卡。不是角色卡大全，不是设定集，是一份供 AI 作者引用、可追溯、可更新的写作参考规范。

## 核心理念

CCP 做的不是复制角色台词，而是**蒸馏角色的行为操作系统，并交给写作 AI 作为参考规范**。

一张好的写作用角色卡应该回答：

- 她在不同情境下**如何反应**？
- 她的话**怎么说出来**？
- 她**怎么理解**别人的意图？
- 她在价值冲突时**先保什么、牺牲什么**？
- 她**绝对不会**做什么？
- 写她的场景、对白、内心戏时，**叙述者能看到多少**？
- 她的资料覆盖到哪一天，之后的新剧情如何更新？

关键区分：捕捉的是 HOW she behaves，不是 WHAT she said。标签是给人看的，行为规则是给 AI 作者落笔时遵循的。

### 产品哲学：角色不是资料页，而是一套可引用的反应系统

CCP 的目标不是把 Wiki 重新写一遍，也不是把角色台词整理成 prompt。Wiki 告诉用户「发生过什么」，CCP 要告诉写作 AI「把一个角色放进一个新情境里，她会如何活着、如何说、如何想」，让 AI 以**作者/叙述者**的身份把这一切写出来。

一张高质量写作用角色卡至少包含六个写作参考层：

| 层 | 问题 | 失败时的样子 |
|---|---|---|
| 行为镜片 | 她先注意什么、忽略什么？ | 只会复述设定 |
| 反应规则 | 什么情境下靠近、逃开、攻击、沉默？ | 所有场景都同一种反应 |
| 表达 DNA | 句长、停顿、敬语、自称、情绪泄露如何组合？ | 只贴口癖 |
| 关系算法 | 她如何判断善意、背叛、亲近、利用？ | 对所有角色都一样热情 |
| 决策底线 | 价值冲突时先保什么、牺牲什么？ | 角色被剧情轻易推着走 |
| 内心戏边界 | 她心里怎么想、哪些不会说出口、叙述者能看到多少？ | 内心戏写成作者旁白 |

**关键原则：写得进去的是行为规范，写不进去的才保留为边界。** 角色的神秘感不是靠含糊制造，而是靠承认资料、视角和推断能力的限制。

### 未来使用场景

CCP 面向二次元创作者提供一套可共享的角色写作基础设施，让角色卡成为同人创作、剧情试写、场景与剧本设计和互动叙事可以共同调用的写作参考层。

当前最直接的使用场景：

- **同人创作**：写场景、对白、内心戏，让角色不只"说得像"，也"做得像"。
- **剧情试写**：把角色放进原作没有写过的新情境，用行为模式推断反应。
- **场景 / 剧本设计**：先设计剧情框架、对白节拍，再按角色卡校验，避免 OOC。
- **OOC 审稿**：把写好的草稿与角色卡逐项比对，定位偏离点并给出修改方向。

未来可以扩展到：

- **AI 互动小说 / 视觉小说原型**：用角色卡驱动分支对白、关系变化、冲突升级。
- **多角色叙事实验**：多张角色卡在同一事件中碰撞，形成群像剧情。
- **创作者工作台**：作者用 CCP 试写场景、改写对白、检查 OOC、保持长篇同人中的角色一致性。
- **可更新角色档案**：作品继续更新时，角色卡也带着资料日期和来源链一起成长。

---

## 默认模式：最高质量生成

CCP 默认只采用 **Highest Fidelity Mode**。

暂不提供快速、省 token、轻量模式。生成时应尽可能完整检索公开资料、交叉验证关键结论、记录来源和资料日期，并把局限写进角色卡。宁可消耗更多 token 得到高保真角色，也不要为了节省上下文生成薄弱角色卡。

未来如果实现轻量模式，必须作为显式选项，不能改变默认质量标准。

---

## 前置依赖与本地检索优先原则

CCP 依赖 Python。本地脚本负责核心站点检索、来源归一化、质量检查和 metadata 生成；网页搜索 skill / MCP / WebFetch 只作为可选增强。

**检索优先级：**

1. 用户提供的官方材料：设定集、访谈、BD 特典、字幕、截图、游戏剧情文本。
2. CCP 本地脚本检索核心站点。
3. 网页搜索 skill / MCP / WebFetch 补缺。
4. 用户手动补充材料。

不得把搜索 skill 当作第一步。除非本地脚本没有覆盖该站点，或本地脚本失败并记录原因。

### 信息源优先级

| 优先级 | 来源 | 示例 |
|---|---|---|
| 最高 | 用户提供的官方材料 | 设定集、访谈原文、BD 特典、官方字幕、截图 |
| 高 | 官方网站、官方角色介绍、官方剧情文本 | franchise official sites, game story text |
| 高 | 萌娘百科、Wikipedia、作品 Fandom Wiki | zh.moegirl.org.cn, wikipedia.org, fandom.com |
| 中 | Bangumi、AniDB、游戏数据库、Bilibili 高质量专栏、Anime News Network | bgm.tv, anidb.net, Bestdori, BWIKI |
| 低 | 粉丝讨论、社区解读 | 必须标注为推测 |
| 排除 | 知乎、微信公众号、百度百科 | 不可作为来源 |

重要结论至少需要两个独立来源。来源冲突时保留冲突，不要强行调和。

### 核心本地检索入口

优先使用统一入口：

```bash
python scripts/source_search.py "角色名" --work "作品名" --mode discover
python scripts/source_search.py "角色名" --work "作品名" --sources moegirl,mediawiki
```

萌娘百科可直接使用专用脚本：

```bash
python scripts/moegirl_api.py "角色名" --intro
python scripts/moegirl_api.py "角色名" --full
python scripts/moegirl_api.py "角色名" --search
python scripts/moegirl_api.py "角色名" --wikitext
```

Windows 本机使用 `python`；Linux/macOS 用户可尝试 `python3`。

### 检索失败规则

关键网站不能因为一次失败就标注「信息不足」。必须记录：

- 尝试的命令；
- 查询词和 resolved title；
- URL；
- 错误信息；
- 替代来源；
- 对可信度的影响。

最终仍失败时，在 `references/sources.json` 和对应研究文件中记录失败项。

---

## 生成目录结构

确认角色后，先创建目录，再开始研究。生成的写作用角色卡统一归档在仓库 `output/<slug>/` 下；`output/` 已加入 Git 忽略列表，不纳入版本控制：

```text
output/<character-slug>/
├── character-card.md
├── manifest.json
└── references/
    ├── sources.json
    ├── distillation.md
    ├── quality-report.json
    └── research/
        ├── 01-setting.md
        ├── 02-personality.md
        ├── 03-expression.md
        ├── 04-relationships.md
        ├── 05-key-scenes.md
        └── 06-media-coverage.md
```

角色卡必须自包含。复制整个目录就能独立使用。研究文件不完整时，不得声称生成完成。

注意区分：`output/` 存放每次生成的角色卡产物（不跟踪）。

---

## 必备 metadata 与资料时间边界

每个生成角色卡必须记录资料搜索日期，避免作品出续作、游戏版本更新或新活动后货不对板。

### `manifest.json` 必填字段

```json
{
  "schema_version": "1.0",
  "artifact_type": "character_card",
  "name": "character-slug",
  "character": "角色名",
  "work": "作品名",
  "aliases": [],
  "generated_at": "YYYY-MM-DD",
  "research_started_at": "YYYY-MM-DD",
  "research_completed_at": "YYYY-MM-DD",
  "latest_source_checked_at": "YYYY-MM-DD",
  "covered_until": {
    "date": "YYYY-MM-DD",
    "description": "截至该日期可检索到的公开资料和用户提供材料"
  },
  "covered_media": [],
  "not_covered": ["YYYY-MM-DD 后发布的新剧情、新活动、新访谈、新设定修订"],
  "source_count": 0,
  "source_tiers": {},
  "quality_score": null,
  "honesty_boundary": "",
  "ccp_version": "unknown"
}
```

### `references/sources.json` 要求

每条来源必须记录：

- `id`
- `source`
- `title`
- `url`
- `source_tier`
- `officiality`
- `media_type`
- `retrieved_at`
- `content_hash`，能计算则计算
- `status`
- `warnings`

失败来源也要记录，`status` 写为 `failed`。

### 最终 `character-card.md` 必须包含资料时间边界

角色卡中必须写明：

```text
本卡资料检索完成于：YYYY-MM-DD。
行为蒸馏基于截至该日期可检索到的公开资料和用户提供材料。
如果作品在此日期后发布新剧情、新活动、新台词、访谈或设定修订，本卡可能无法反映最新内容。
```

当作者指出「最新剧情不是这样」时，角色卡不得硬拗，必须回应：

```text
本卡资料更新至 YYYY-MM-DD，可能没有覆盖之后发布的内容。如果你有最新版 CCP，或可以提供新剧情 / 新资料链接，我可以帮你更新这张卡；这可能会消耗一些 Token。
```

---

## 执行流程

### Phase 0：需求确认

确认：

1. 角色名称：中文/日文/英文均可。
2. 作品名称：系列全名，明确是哪一部或哪个时间线。
3. 生成范围：默认全面画像，不做轻量版。
4. 用户是否有官方材料：有则最高优先。
5. 是否为跨媒体角色：BanG Dream!、Love Live!、Project Sekai、少女☆歌剧等默认触发跨媒体规则。

用户只说「就做 XX」时，默认全面画像并推进；同名歧义时必须询问。

### Phase 1：Source Discovery

先运行本地检索：

```bash
python scripts/source_search.py "<角色名>" --work "<作品名>" --mode discover
```

目标：

- 找到候选条目；
- 收集别名；
- 判断是否跨媒体；
- 初步生成 `references/sources.json`；
- 记录失败来源。

候选明确时自动推进；多个候选时让用户选择。

> **sources.json 的来源构成（显式约定）**
>
> `references/sources.json` 是**整个调研阶段（Phase 1–4）的来源最终档案**，不只包含 `source_search.py` 的命中记录。它的内容来自四条路径，全部按 CCP 检索优先级汇总：
>
> 1. **本地脚本命中**：`source_search.py --mode discover`、`moegirl_api.py`、`bwiki_api.py` 自动检索到的条目；
> 2. **外部检索补充**：网页搜索 skill / MCP / WebFetch 抓取的官方站点、访谈、专栏、Fandom Wiki 等（仅在本地脚本未覆盖或失败时补缺）；
> 3. **失败记录**：尝试过但未命中的来源（`status=failed` + `error`），包括 adapter 未实现、页面不存在、超时等——失败也要留下证据；
> 4. **用户提供材料**：官方设定集、访谈原文、BD 特典、字幕、截图、游戏剧情文本，`officiality=user_provided`。
>
> 因此 `sources.json` 的记录数通常远多于 `source_search.py` 的终端输出——后者只是起点情报，agent 在 Phase 3 各研究线中持续追加外部来源并归档到 `sources.json`。每条记录必须保留 `retrieved_at` 与 `status`，供 `merge_research.py` / `generate_manifest.py` / `quality_check.py` 统计验证。

### Phase 2：创建目录与来源索引

创建目标结构，写入空的：

- `references/sources.json`
- `references/distillation.md`
- `references/research/06-media-coverage.md`

并记录 `research_started_at`。

### Phase 3：多源信息采集（5 Agent 并行）

启动 5 个并行子 agent，但它们不再盲搜。每个 agent 必须先读取 `references/sources.json` 和本地检索结果，只在维度缺口明确时再外部补搜。

| Agent | 重点 | 输出文件 |
|---|---|---|
| 1 设定 | 基本信息、世界观、身份、时间线、媒体覆盖 | `01-setting.md` |
| 2 性格 | 行为模式、压力反应、内在矛盾、成长弧 | `02-personality.md` |
| 3 表达 | 句式、词汇、自称、敬语、口癖、台词语境 | `03-expression.md` |
| 4 关系 | 重要关系、社会认知、跨作品互动 | `04-relationships.md` |
| 5 名场面 | 至少 8 个关键场景、决策逻辑、压力行为 | `05-key-scenes.md` |

每个研究文件必须写：

- 使用的 source id 或 URL；
- 可信度；
- 官方设定 / Wiki 汇总 / 用户材料 / 粉丝推测的区分；
- 冲突点；
- 检索失败与降级情况。

### Phase 4：跨媒体覆盖记录

对跨媒体角色必须写 `06-media-coverage.md`：

- 已覆盖媒体；
- 未覆盖媒体；
- 主线和衍生材料的权重；
- 不同媒体冲突；
- 本卡采用的时间线；
- 截至哪个日期。

游戏活动、卡面故事、区域对话可作为日常行为和关系补充，但不能覆盖主线设定，除非官方明确更新。

### Phase 5：调研质量检查点

运行：

```bash
python scripts/merge_research.py <skill_directory>
```

检查：

- 每个维度来源数；
- 总来源数；
- 黑名单来源；
- 失败来源；
- 重要结论是否交叉验证；
- 跨媒体覆盖；
- 资料日期是否记录。

展示摘要给用户确认。调研质量决定最终角色卡上限，缺口明显时补充研究后再蒸馏。

### Phase 6：行为蒸馏

读取 `references/distillation-framework.md`，写入 `references/distillation.md`。

核心行为模式必须回答：

```text
在什么情况下 → 做什么 → 为什么这样
```

筛选标准：

- 跨场景复现：至少两个不同场景；
- 可执行性：能推断新情境中的反应；
- 证据链：能追溯到 research 文件或 sources；
- 矛盾保留：发展性矛盾和情境性矛盾不抹平。

目标提炼 3-7 个核心行为模式。只通过一重验证的行为降级为低置信度，不写成核心。

### Phase 7：蒸馏确认检查点

向用户展示：

- 核心行为模式；
- 表达质感；
- 核心动机；
- 内在矛盾；
- 知识边界；
- 资料覆盖日期；
- 未覆盖媒体。

用户确认后再组装最终角色卡。

### Phase 8：构建角色卡与 manifest

读取 `references/character-card-template.md` 组装 `character-card.md`。

同时生成：

```bash
python scripts/generate_manifest.py <skill_directory>
```

最终角色卡必须包含：

- 使用说明（作者/叙述者视角，非角色扮演）；
- 角色速览；
- 行为规范；
- 对白写作规范；
- 内心戏写作规范；
- 社会认知与关系；
- 决策逻辑；
- 知识边界；
- 场景与剧情设计规范；
- 反 OOC 检查清单；
- 场景写作示例；
- 诚实边界与资料时间边界；
- 面对资料更新或作者纠错的规则；
- 调研来源。

### Phase 9：质量验证

运行：

```bash
python scripts/quality_check.py <skill_directory>
```

必须检查：

- 行为模式数量；
- 对白写作规范与内心戏写作规范；
- 矛盾保留；
- 使用说明（写作视角规则）；
- 场景写作示例；
- 场景与剧情设计规范；
- 反 OOC 检查清单；
- 诚实边界；
- 来源标注；
- `manifest.json`（含 `artifact_type`）；
- `sources.json`；
- `latest_source_checked_at`；
- 每条来源 `retrieved_at`；
- 角色卡资料时间边界；
- 作者指出最新剧情时的更新回应规则。

验证结果写入 `references/quality-report.json`。验证结果展示给用户后才算完成。

---

## 更新已有角色卡

触发语：

- 「更新这张卡」
- 「最新剧情不是这样」
- 「XX 出新作了」
- 「用新版本剧情更新她」
- 「这个设定过时了」

更新流程：

1. 读取旧 `manifest.json`，确认 `latest_source_checked_at`。
2. 告知用户旧资料日期和可能 token 消耗。
3. 询问用户是否有新官方材料。
4. 重新运行本地 source discovery。
5. 对比旧 `sources.json` 与新检索结果。
6. 只重蒸馏受影响维度。
7. 更新 `references/distillation.md`。
8. 更新 `character-card.md`。
9. 更新 `manifest.json` 的资料日期。
10. 重新运行 `quality_check.py`。

更新时不得：

- 直接覆盖旧行为模式；
- 把用户印象当官方设定；
- 删除旧冲突记录；
- 假设新剧情一定推翻旧剧情；
- 混淆不同时间线。

---

## 可辩证吸收的竞品能力

### 产品表达：采纳

README 和交付说明可以更直观地展示生成前/生成后、角色卡的使用方式。但不照搬"夺舍"路线。CCP 的定位是高保真行为蒸馏，产物是写作参考规范。

### 工具链：采纳

优先加入：

- `source_search.py`
- `source_registry.py`
- `generate_manifest.py`
- `file_manager.py`（用于备份和更新）

`batch_distill.py` 暂缓，因为当前默认追求单个角色最高质量，不追求批量低成本生产。

### 提示词提炼：调整采纳

可提供：

```bash
python scripts/distill_prompt.py <skill_dir>
```

输出适合普通 ChatGPT / Claude / SillyTavern / OpenClaw 的 `prompt.md`。但这只是便携导出，不替代原生 Agent Skill，也不包含完整研究链。

### 记忆协议：谨慎采纳

近期只吸收「修订记录」和「用户纠错记录」，暂不做自动长期记忆。CCP 的核心是角色行为蒸馏，不是陪伴机器人运行时。

---

## 品味守则

| 原则 | 一句话 |
|---|---|
| 行为 > 形容词 | 描述「做什么」而非「是什么」 |
| 证据 > 印象 | 重要结论必须可追溯 |
| 矛盾 > 一致 | 保留矛盾，这是深度的来源 |
| 语境 > 台词 | 每句经典台词必须说明场景 |
| 时间边界 > 硬拗 | 资料过期时承认边界并进入更新 |
| 对白 > 论文 | 写对白要口语，写规范要可执行 |
| 角色驱动 > 剧情驱动 | 场景和剧情由角色动机推动，不由情节倒逼 |
| 人味 > 完美 | 角色可以不确定、前后矛盾、沉默 |

绝不做：

- 用萌属性标签取代行为描述；
- 编造角色在原作中没说过的话；
- 把角色写成完美人设；
- 在信息不足时强行生成；
- 为推进剧情让角色做出违背决策逻辑的行为；
- 用知乎、微信公众号、百度百科做来源；
- 忽略资料检索日期；
- 作者指出新剧情时硬拗旧设定。

---

## 致谢

CCP 的多 Agent 调研、阶段检查点和质量验证借鉴了 nuwa-skill。CCP 将这种蒸馏方式适配到二次元角色行为系统：不是复刻设定，而是让角色在新情境里可信地活着。
