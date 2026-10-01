#!/usr/bin/env python3
"""Unified local source discovery entrypoint for CCP.

Object-oriented + table-driven design: each local source backend is a
SourceAdapter subclass registered in ADAPTER_REGISTRY. Adding a new source
only requires a new adapter class and a registry entry; the dispatch loop
and normalizer stay unchanged.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from source_registry import is_cross_media_work, is_excluded_url, source_hints_for_work, source_tier

ROOT = Path(__file__).resolve().parent
TODAY = date.today().isoformat()


class SourceAdapter:
    """Base adapter for one local source backend.

    Subclasses set source/script/media_type/language and implement
    discover(); normalize() turns a raw backend payload into a standard
    sources.json record.
    """

    source = None
    script = None
    media_type = "wiki"
    language = None

    @staticmethod
    def sha256_text(text):
        if not text:
            return None
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def run_python_script(script, args, timeout):
        cmd = [sys.executable, str(ROOT / script), *args, "--timeout", str(timeout)]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
            stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
            payload = json.loads(stdout) if stdout.strip() else {}
            payload["retrieved_by"] = " ".join(cmd)
            payload["command_status"] = proc.returncode
            if stderr.strip():
                payload.setdefault("warnings", []).append(stderr.strip())
            return payload
        except subprocess.TimeoutExpired as exc:
            return {
                "ok": False,
                "source": script,
                "status": "failed",
                "error": "timeout",
                "message": str(exc),
                "retrieved_by": " ".join(cmd),
            }
        except json.JSONDecodeError as exc:
            return {
                "ok": False,
                "source": script,
                "status": "failed",
                "error": "json_decode_error",
                "message": str(exc),
                "retrieved_by": " ".join(cmd),
            }

    def __init__(self, query, work, timeout):
        self.query = query
        self.work = work
        self.timeout = timeout

    def discover(self):
        raise NotImplementedError

    def normalize(self, raw):
        url = raw.get("page_url") or raw.get("url")
        excluded = is_excluded_url(url)
        extract = raw.get("extract", "") or ""
        status = "ok" if raw.get("ok") and not excluded else "failed"
        return {
            "id": f"{self.source}-{raw.get('resolved_title') or self.query}".replace(" ", "-"),
            "source": self.source,
            "title": raw.get("resolved_title"),
            "resolved_title": raw.get("resolved_title"),
            "url": url,
            "query": self.query,
            "work": self.work,
            "source_tier": "excluded" if excluded else source_tier(self.source),
            "officiality": "excluded" if excluded else "secondary",
            "media_type": self.media_type,
            "language": self.language,
            "retrieved_at": TODAY,
            "status": status,
            "warnings": raw.get("warnings", []),
            "attempted_modes": raw.get("attempted_modes") or [raw.get("mode")],
            "retrieved_by": raw.get("retrieved_by"),
            "pageid": raw.get("pageid"),
            "extract_chars": raw.get("extract_chars", len(extract)),
            "content_hash": SourceAdapter.sha256_text(extract),
            "error": raw.get("error"),
        }

    def failed_record(self, error, reason, warnings):
        return {
            "id": f"{self.source}-{self.query}".replace(" ", "-"),
            "source": self.source,
            "title": None,
            "url": None,
            "query": self.query,
            "work": self.work,
            "source_tier": source_tier(self.source),
            "officiality": "secondary",
            "media_type": self.media_type,
            "language": self.language,
            "retrieved_at": TODAY,
            "status": "failed",
            "error": error,
            "warnings": warnings,
            "attempted_modes": ["discover"],
        }


class MoegirlAdapter(SourceAdapter):
    source = "moegirl"
    script = "moegirl_api.py"
    media_type = "wiki"
    language = "zh"

    def discover(self):
        raw = SourceAdapter.run_python_script(self.script, [self.query], self.timeout)
        return self.normalize(raw)


class BwikiAdapter(SourceAdapter):
    source = "bwiki"
    script = "bwiki_api.py"
    media_type = "wiki"
    language = "zh"

    BWIKI_GAME_SLUGS = {
        "原神": "ys", "Genshin": "ys",
        "星穹铁道": "sr", "Star Rail": "sr",
        "明日方舟": "arknights", "Arknights": "arknights",
        "蔚蓝档案": "ba", "Blue Archive": "ba",
        "碧蓝航线": "blhx", "Azur Lane": "blhx",
        "崩坏3": "bh3", "Honkai Impact": "bh3",
        "鸣潮": "wutheringwaves", "Wuthering Waves": "wutheringwaves",
    }

    @staticmethod
    def resolve_bwiki_game(work):
        """Resolve a work name to a BWIKI game slug."""
        if not work:
            return None
        for name, slug in BwikiAdapter.BWIKI_GAME_SLUGS.items():
            if name.lower() in work.lower() or work.lower() in name.lower():
                return slug
        return None

    def discover(self):
        game = self.resolve_bwiki_game(self.work)
        if not game:
            return self.failed_record(
                error="unknown_game",
                reason=None,
                warnings=[
                    f"could not resolve BWIKI game slug from work '{self.work}'; "
                    "pass --sources bwiki with a known game name"
                ],
            )
        raw = SourceAdapter.run_python_script(self.script, [self.query, "--game", game], self.timeout)
        return self.normalize(raw)


class PlaceholderAdapter(SourceAdapter):
    """Fallback for sources without a real adapter yet.

    Records a failed entry explaining the gap instead of silently skipping.
    """

    media_type = "database"

    def __init__(self, source, query, work, timeout, reason="adapter_not_implemented"):
        super().__init__(query, work, timeout)
        self.source = source
        self.reason = reason
        if source in {"mediawiki", "fandom", "wikipedia", "bwiki"}:
            self.media_type = "wiki"

    def discover(self):
        return self.failed_record(
            error=self.reason,
            reason=None,
            warnings=[
                f"{self.source} adapter is not implemented yet; "
                "use search skill or user material as fallback and record results"
            ],
        )


class OfficialAdapter(PlaceholderAdapter):
    """Official material requires user-provided sources; never auto-fetched."""

    def __init__(self, query, work, timeout):
        super().__init__("official", query, work, timeout, reason="manual_or_official_material_required")


# Table-driven registry: source key → adapter class.
# Extend by adding a new adapter subclass and one entry here.
ADAPTER_REGISTRY = {
    "moegirl": MoegirlAdapter,
    "bwiki": BwikiAdapter,
    "official": OfficialAdapter,
}


def build_adapter(source, query, work, timeout):
    adapter_cls = ADAPTER_REGISTRY.get(source)
    if adapter_cls is None:
        return PlaceholderAdapter(source, query, work, timeout)
    return adapter_cls(query, work, timeout)


def parse_sources(value, work):
    if value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return source_hints_for_work(work)


def emit_json(payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Discover CCP character sources through local adapters")
    parser.add_argument("query", nargs="?", help="character name, alias, or page title")
    parser.add_argument("--work", default="", help="work/franchise name")
    parser.add_argument("--mode", default="discover", choices=["discover"], help="discovery mode")
    parser.add_argument("--sources", help="comma-separated source adapters, e.g. moegirl,mediawiki")
    parser.add_argument("--timeout", type=int, default=20, help="per-adapter timeout seconds")
    args = parser.parse_args(argv)

    if not args.query:
        parser.print_usage()
        print("source_search.py: error: the following arguments are required: query")
        return 2

    requested_sources = parse_sources(args.sources, args.work)
    records = [build_adapter(source, args.query, args.work, args.timeout).discover()
               for source in requested_sources]

    # 结果 JSON 是给「人 / agent」阅读的情报，而非机器管道的中间产物。
    # CCP 流程中，agent 读取本输出后据此判断：
    #   - records[] 里哪些来源命中（status=ok）、哪些失败（status=failed + error），据此决定是否进入 Phase 2；
    #   - cross_media_hint 是否为 True，决定是否触发跨媒体规则；
    #   - 随后把这些记录人工归档为 references/sources.json，供 merge_research.py /
    #     generate_manifest.py / quality_check.py 等下游脚本读取。
    result = {
        "ok": any(record.get("status") == "ok" for record in records),
        "query": args.query,
        "work": args.work,
        "mode": args.mode,
        "retrieved_at": TODAY,
        "cross_media_hint": is_cross_media_work(args.work),
        "sources_requested": requested_sources,
        "records": records,
        "warnings": [] if any(record.get("status") == "ok" for record in records) else ["no local adapter returned a successful source"],
    }

    # 以 UTF-8 可读 JSON 写出到 stdout（供人 / agent 阅读，不做自动化消费）。
    emit_json(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(["藤都子", "--work", "梦限大MewType", "--mode", "discover"]))