"""写作用角色卡 · 场景写作脚本

用生成的角色卡（character-card.md）驱动写作 AI，以作者/叙述者视角写场景、对白、内心戏，
并支持场景/剧本设计与 OOC 审稿。角色卡放 System 层，一次加载、多种用法。

依赖（未安装时先 pip install）：
    langchain-core langchain-openai openai

用法（先确认 test/api_config.json 已配置）：
    python test/write_scene.py <card_dir_or_card_md> "写一段：排练结束后……"
    python test/write_scene.py <card_dir> --mode design "设计一场戏：……"
    python test/write_scene.py <card_dir> --mode review --draft draft.txt "审这段草稿"

模式：
    write   即时写作：直接写场景/对白/内心戏
    design  场景/剧本设计：先出方案，再用「反 OOC 检查清单」核对
    review  OOC 审稿：把草稿与角色卡逐条比对，指出偏离点与改法
"""

import argparse
import json
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

MODE_GUIDE = {
    "write": (
        "写涉及角色的场景/对白/内心戏时，先查阅对应章节（行为规范、对白写作规范、"
        "内心戏写作规范、社会认知、决策逻辑、知识边界）再落笔。"
    ),
    "design": (
        "设计剧情/场景/剧本时，先按「场景与剧情设计规范」出方案（场景三问：目标/障碍/取舍），"
        "再用「反 OOC 检查清单」逐条核对；任何一条不过就回改设计，不要为剧情迁就角色。"
    ),
    "review": (
        "把作者给出的草稿与角色卡逐条比对，输出 OOC 检查结论：第几条违反、依据卡里哪一节、"
        "建议怎么改。不要直接重写全文，除非作者要求。"
    ),
}


def load_config():
    config_path = Path(__file__).parent / "api_config.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def load_card(card_path_or_dir):
    path = Path(card_path_or_dir)
    if path.is_dir():
        path = path / "character-card.md"
    if not path.exists():
        raise FileNotFoundError(f"角色卡不存在: {path}")
    return path.read_text(encoding="utf-8"), path


def build_system_prompt(card, mode):
    return f"""你是写作 AI，以作者/叙述者的身份创作，角色是笔下的对象，不是让你扮演的角色。
下面是一张写作用角色卡，是你写作前必须查阅的参考规范：

- 行为规范 → 决定角色在这个情境里做什么、不做什么、先注意什么
- 对白写作规范 → 决定角色怎么说：句式、节奏、口癖、称谓、情绪泄露
- 内心戏写作规范 → 决定角色怎么想、读者能看到多少
- 社会认知 → 决定角色如何解读他人动机
- 决策逻辑 → 决定价值冲突时角色保什么、牺牲什么
- 知识边界 → 决定角色知道什么、不知道什么，不能写成上帝视角

{MODE_GUIDE[mode]}

写作视角强制规则：第三人称有限视角，跟随角色；对白必须符合语言 DNA；内心戏是角色的思维、
不是作者的评论；行为推断可追溯；不编造新设定。正文里不要出现「本卡」「资料更新至」等元说明。
停止引用触发：作者说「停止引用这张卡」「切换叙述者」「不用管角色卡」时，恢复普通作者模式。

【角色卡全文】
{card}
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="用写作用角色卡驱动写作 AI")
    parser.add_argument("card", help="角色卡目录或 character-card.md 路径")
    parser.add_argument("prompt", help="写作 / 设计要求")
    parser.add_argument("--mode", choices=MODE_GUIDE.keys(), default="write")
    parser.add_argument("--draft", help="review 模式用：待审稿的草稿文件路径")
    args = parser.parse_args(argv)

    config = load_config()
    card, card_path = load_card(args.card)

    prompt = args.prompt
    if args.mode == "review":
        if not args.draft:
            raise SystemExit("review 模式需要 --draft 指定草稿文件")
        prompt += "\n\n【草稿】\n" + Path(args.draft).read_text(encoding="utf-8")

    llm = ChatOpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"],
        model=config["model"],
        temperature=config.get("temperature", 0.8),
    )

    print(f"[{args.mode}] 引用角色卡: {card_path}")
    resp = llm.invoke(
        [
            SystemMessage(content=build_system_prompt(card, args.mode)),
            HumanMessage(content=prompt),
        ]
    )
    print(resp.content)