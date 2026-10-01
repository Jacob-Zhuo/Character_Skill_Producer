# AGENTS.md

本文件为 opencode（以及兼容 AGENTS.md 约定的其他 AI 编码代理）提供在此代码仓库中工作的指导。

## 项目简介

CSP（Character Skill Producer，角色技能生成器）是一款开源的 Agent Skills 风格**元技能**，用于将动漫、漫画和游戏中的虚构角色转化为可执行的角色行为技能。

用户提供角色名和作品名后，CSP 会检索资料、交叉核对证据、提炼行为模式、执行质量检查，最后生成可运行的 `SKILL.md`。文件会记录研究日期、资料范围和更新方式。CSP 适用于角色聊天、同人创作、场景与对话原型，也面向未来的互动小说和角色驱动型游戏工作流。

CSP 不会生成静态角色卡，也不用于提炼现实人物。项目聚焦二次元角色，并生成可执行的行为指令：角色在不同情境下会如何回应，而不只是罗列性格标签或剧情设定。

## 必读：根目录 SKILL.md

**本仓库根目录的 `SKILL.md` 是 CSP 元技能的唯一权威流程定义，是每次任务的起点。** 它定义了生成、更新和交付角色技能必须遵循的完整流程（Phase 0–9）、目录结构、metadata 字段、质量标准和品味守则。

执行任何与 CSP 相关的任务（生成、蒸馏、制作、更新、检查角色 Skill）时，必须遵守以下规则：

1. **任务开始时，必须先完整读取根目录 `SKILL.md` 全文**，再开始任何检索、建目录或写文件动作。不要凭本文件或记忆中的流程执行。
2. 生成任务必须依次遵循 `SKILL.md` 中「执行流程」的 Phase 0–9，不可跳步、不可自定义替代流程。
3. 组装最终 `SKILL.md` 时，必须读取 `references/skill-template.md` 作为模板；行为蒸馏必须参考 `references/distillation-framework.md`。
4. 交付前必须运行 `scripts/quality_check.py`，且所有检查项通过后才可声称完成。
5. 本文件（AGENTS.md）只提供仓库级约定（环境、命令、架构、写作规范）；**流程细节以根目录 `SKILL.md` 为准，两者冲突时以 `SKILL.md` 为准。**

## 平台说明

- Shell 环境为 Windows 上的 bash（Git Bash / MSYS）。请使用 Unix 风格语法，例如 `/dev/null`，路径使用正斜杠。
- 当前机器没有 `python3` 命令别名。运行本地命令时请使用 `python`，即使文档或脚本头部写的是 `python3`。
- `package.json` 目前只声明了 `docx` 依赖；CSP 本身没有 Node 构建或测试脚本。
- 本仓库没有 Cursor 规则或 Copilot 指令文件；本文件即 opencode 的规则入口。

## 命令

```bash
# 如果本地工具需要依赖，请安装
npm install

# 通过仓库的搜索入口查找本地资料
python scripts/source_search.py "高松灯" --work "BanG Dream! It's MyGO!!!!!" --mode discover
python scripts/source_search.py "能天使" --work "明日方舟" --sources moegirl

# 通过 MediaWiki API 获取萌娘百科词条
python scripts/moegirl_api.py "角色名"              # 自动：简介 → 搜索 → 回退
python scripts/moegirl_api.py "角色名" --intro      # 提取已知词条的简介
python scripts/moegirl_api.py "角色名" --search     # 搜索候选词条标题
python scripts/moegirl_api.py "角色名" --full       # 提取完整纯文本
python scripts/moegirl_api.py "角色名" --wikitext   # 回退到原始维基文本

# 汇总生成的技能目录中 references/research/ 下的研究结果
python scripts/merge_research.py <skill_directory>

# 为生成的技能目录生成或更新清单元数据
python scripts/generate_manifest.py <skill_directory>

# 检查生成的角色技能目录或 SKILL.md 的质量
python scripts/quality_check.py <skill_directory>
python scripts/quality_check.py <path/to/SKILL.md>

# 通过 BWIKI MediaWiki API 获取游戏百科词条
python scripts/bwiki_api.py "角色名" --game 明日方舟
```

本仓库没有构建步骤、代码检查命令或常规测试套件。最接近验证工具的是 `quality_check.py`、`merge_research.py` 和 `generate_manifest.py`：它们分别用于检查生成的角色技能、汇总研究完整度，以及生成元数据。

`quality_check.py` 会写入或更新 `references/quality-report.json`。当超过一项检查未通过时，它会以非零状态码退出。因此，交付生成的技能前，应运行此命令。

## 架构

### 源文件与可安装技能

根目录中的文件是 CSP 开发时的规范源文件：

| 文件 | 用途 |
|---|---|
| `SKILL.md` | CSP 元技能的主体及流程说明 |
| `references/skill-template.md` | 组装生成的角色技能时使用的模板 |
| `references/distillation-framework.md` | 将研究资料转化为可执行行为模式的方法 |
| `references/source-output-schema.md` | `sources.json`、`manifest.json` 和 `quality-report.json` 的预期结构 |
| `scripts/source_search.py` | 统一的本地资料搜索入口 |
| `scripts/source_registry.py` | 资料来源分级、排除域名、作品提示和跨媒体作品规则 |
| `scripts/moegirl_api.py` | 萌娘百科 MediaWiki API 封装 |
| `scripts/bwiki_api.py` | BWIKI（biligame）MediaWiki API 封装 |
| `scripts/merge_research.py` | 研究摘要与检查点生成器 |
| `scripts/generate_manifest.py` | 清单生成与更新工具 |
| `scripts/quality_check.py` | 生成的角色技能质量检查工具 |

生成的角色技能归档在 `output/<slug>/` 下（如 `output/fuji-miyako/`）。`output/` 已加入 Git 忽略列表，**不纳入版本控制**，用于存放每次生成的角色技能产物。本地安装技能时，可整体复制该目录到 opencode 的项目级技能目录 `.opencode/skills/<slug>/` 或全局 `~/.config/opencode/skills/<slug>/`，也可通过 `skills.paths` 配置扫描其他位置。`.claude/` 已加入 Git 忽略列表，不应作为源文件处理。注意区分：`examples/csp/` 是 CSP 元技能自身的可安装副本（跟随 Git 跟踪），与 `output/` 中的角色技能产物不同。

### 生成的技能目录结构

每个生成的角色技能都使用独立目录：

```text
<character-slug>/
├── SKILL.md
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

复制整个目录即可安装或分享角色技能。

### CSP 元技能流程

用户要求生成角色技能时，CSP 按以下流程执行：

1. **确认需求**：确认角色名、作品名、可选的侧重点，以及用户是否有官方本地资料。
2. **查找本地资料**：先运行 `scripts/source_search.py` 和站点适配脚本，再使用外部网页搜索。外部搜索用于补充，默认不作为第一步。
3. **建立目录和来源索引**：创建技能目录、`references/research/`，并创建 `references/sources.json`，记录获取日期、资料来源级别、失败情况和可选的内容哈希。
4. **开展五条研究线**：分别研究设定与世界观、性格、表达方式、人际关系和关键场景，避免某个维度挤占其他维度。
5. **检查跨媒体覆盖**：对于跨作品系列，使用 `06-media-coverage.md` 记录已覆盖和未覆盖的媒体内容。
6. **检查研究质量**：使用 `merge_research.py` 或同等方式，汇报来源数量、主要发现、矛盾和缺失维度。
7. **提炼行为**：提取行为规律、表达特点、社会认知、决策逻辑、硬性约束、矛盾点和信息诚实边界。每条主要行为模式都应回答：在什么情境下，角色会做什么，原因是什么。
8. **组装技能**：根据提炼结果填写 `references/skill-template.md`。
9. **生成元数据并检查质量**：生成 `manifest.json`，运行 `quality_check.py`，并更新 `references/quality-report.json`。

## 资料来源与研究规则

CSP 的内容必须有资料依据。优先使用用户提供的官方材料，再查找公开资料：

| 优先级 | 资料来源 |
|---|---|
| 最高 | 用户提供的官方书籍、访谈、BD 特典、字幕、截图、文字记录 |
| 高 | 官方网站、官方角色简介、官方剧情文本、萌娘百科、维基百科、系列作品的 Fandom Wiki |
| 中 | Bangumi、AniDB、游戏剧情、优质 Bilibili 专栏、Anime News Network、Bestdori、BWIKI |
| 低 | 粉丝讨论或社区解读，必须明确标为推测 |
| 排除 | 知乎、微信公众号、百度百科 |

重要说法至少使用两个独立来源。保留来源之间的矛盾，不要强行统一。如果公开资料不足，要明确标出缺口，不要编造角色行为。

查询萌娘百科时，先使用 `scripts/moegirl_api.py` 或 `scripts/source_search.py`，再尝试直接获取页面。研究文件和来源文件应记录使用的命令、解析后的标题、页面 URL、获取日期，以及 API 失败情况。

## 研究日期与更新

每个生成的技能都必须在 `manifest.json` 和 `references/sources.json` 中记录研究时间和覆盖范围，包括获取日期、研究完成日期、已覆盖媒体、未覆盖内容，以及最近核查的资料日期等字段。

当用户指出更新的官方设定与技能内容冲突时，角色应说明资料边界，不要自行编造更新。建议使用以下中文表述：

```text
我的资料更新至 YYYY-MM-DD，可能没有覆盖之后发布的内容。如果你有最新版 CSP，或可以提供新剧情 / 新资料链接，我可以帮你更新这个 Skill；这可能会消耗一些 Token。
```

更新旧技能时，应先读取现有的 `manifest.json` 和 `sources.json`，重新核查主要来源，只重新提炼受影响的维度，并更新研究日期和质量报告。

## 跨媒体系列

`SKILL.md` 专门设有跨作品或跨乐队角色的处理流程，适用于 BanG Dream!、Love Live!、Project Sekai 和《少女☆歌剧》等系列。

对于这类角色：

- 设定和人际关系研究应覆盖角色参与的所有相关作品，而不只是某一季动画。
- 游戏和衍生作品资料，如 Garupa 卡牌剧情、Bestdori 活动脚本和区域对话，可作为中等优先级证据，尤其适合研究日常行为。
- 信息诚实边界应说明已覆盖和未覆盖的媒体。
- `06-media-coverage.md` 应记录跨媒体覆盖情况、未覆盖内容和时间线边界。

不要把这一流程当作“范围蔓延”而删除或简化。对于行为依赖跨媒体背景的角色，这些规则很有必要。

## 技能写作规范

- CSP 元技能正文和生成的角色技能使用中文。PRD 或规划文档也使用中文。
- 适当保留日文、英文名称和经典台词。
- 描写角色在具体情境下的行为，不要只使用“傲娇”等分类标签。
- 保留矛盾和成长变化；它们是行为线索，不是错误。
- 每条主要行为模式都应回答：在什么情境下，角色会做什么，原因是什么。
- 生成的角色扮演指令应像自然对话，不要写成文章或演示文稿大纲。角色口吻中应避免过度使用粗体、用破折号连接的句子，以及僵硬的三段式