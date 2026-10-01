#!/usr/bin/env python3
"""Fetch public Moegirlpedia entries through the MediaWiki API (OOP)."""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


class MoegirlApiClient:
    """Moegirlpedia MediaWiki API 客户端。

    封装三层能力：
    1. HTTP/URL 层：HTTPS GET 请求、页面 URL 构造（request_json / build_page_url）；
    2. 低层查询：extract 简介/全文、opensearch 标题搜索、revisions 原文 wikitext；
    3. 高层降级链：auto_query（简介 → 搜索 → 回退），并统一产出结果/错误 dict。

    所有查询方法返回 (result_dict, raw_data)，result_dict 的键结构与
    source_search.py 解析来源记录的期望保持一致（mode / attempted_modes /
    candidates / warnings / fallbacks 等），失败也以 failed 记录形式返回。
    """

    API_URL = "https://zh.moegirl.org.cn/api.php"
    PAGE_BASE_URL = "https://zh.moegirl.org.cn/"
    USER_AGENT = "CharacterSkillProducer/1.0 (+https://github.com/Jacob-Zhuo/Character_Skill_Producer)"

    def __init__(self, api_url=None, page_base_url=None, user_agent=None):
        self.api_url = api_url or self.API_URL
        self.page_base_url = page_base_url or self.PAGE_BASE_URL
        self.user_agent = user_agent or self.USER_AGENT

    # ---------- HTTP / URL 层 ----------

    def build_page_url(self, title):
        return self.page_base_url + urllib.parse.quote(title.replace(" ", "_"))

    def request_json(self, params, timeout):
        """向 MediaWiki API 发起 HTTPS GET 请求并返回解析后的 JSON。

        使用标准库 urllib（无第三方依赖）：把参数拼到 api.php 上，带 User-Agent
        发 GET 请求，读取 UTF-8 响应后用 json 解析成 dict/list。
        """
        url = self.api_url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    # ---------- 结果 / 错误构造 ----------

    def fallback_error(self, query, error, message, attempted_modes):
        """构造失败记录，附带可执行的替代方案提示（供上层写入 sources.json）。"""
        return {
            "ok": False,
            "source": "moegirl_mediawiki_api",
            "query": query,
            "error": error,
            "message": message,
            "attempted_modes": attempted_modes,
            "fallbacks": [
                "retry with --search to find candidate page titles",
                "retry with --full or --wikitext if extracts are incomplete",
                "use WebSearch/WebFetch only as a fallback and record Moegirl API failure",
                "cross-check with Wikipedia, Fandom Wiki, Bangumi, AniDB, or official sources",
            ],
        }

    def _normalize_query_response(self, data, query, mode):
        """归一化 action=query 的响应。

        处理标题归一化（normalized）、重定向（redirects）、页面缺失（missing）
        三种情况；命中则构造统一的结果 dict，未命中返回 None。
        """
        query_data = data.get("query", {})
        pages = query_data.get("pages", {})
        if not pages:
            return None

        page = next(iter(pages.values()))
        if page.get("missing") is not None or str(page.get("pageid", "")) == "-1":
            return None

        resolved_title = page.get("title", query)
        extract = page.get("extract", "") or ""
        warnings = []
        if not extract.strip():
            warnings.append("empty extract; try --search, --full, or --wikitext")

        normalized = query_data.get("normalized", [])
        redirects = query_data.get("redirects", [])

        return {
            "ok": bool(extract.strip()),
            "source": "moegirl_mediawiki_api",
            "mode": mode,
            "query": query,
            "query_title": query,
            "resolved_title": resolved_title,
            "pageid": page.get("pageid"),
            "page_url": self.build_page_url(resolved_title),
            "extract": extract,
            "extract_chars": len(extract),
            "candidates": [],
            "normalized": normalized,
            "redirected": redirects,
            "warnings": warnings,
        }

    # ---------- 低层查询 ----------

    def query_extract(self, title, intro, timeout):
        """按精确标题拉取页面纯文本摘要（TextExtracts）。

        非全文检索：titles 做标题归一化 + 页面表等值匹配 + 重定向跟随。
        intro=True 时加 exintro 只取导言段。
        """
        params = {
            "action": "query",
            "prop": "extracts",
            "titles": title,
            "format": "json",
            "explaintext": "1",
            "redirects": "1",
            "origin": "*",
        }
        if intro:
            params["exintro"] = "1"

        data = self.request_json(params, timeout)
        result = self._normalize_query_response(data, title, "intro" if intro else "full")
        return result, data

    def search_titles(self, query, timeout):
        """通过 MediaWiki opensearch 接口做标题前缀搜索。

        原理：action=opensearch 按「标题前缀/近似」匹配页面标题（含重定向建议），
        不是全文内容检索。limit 限制候选数，namespace=0 限定主命名空间（文章页）。
        返回的是 JSON 数组 [query, [标题…], [描述…], [URL…]]，下标 1/2/3 分别为
        标题、描述、URL 列表，按位取回拼成 candidates。
        """
        params = {
            "action": "opensearch",
            "search": query,
            "limit": "10",
            "namespace": "0",
            "format": "json",
            "origin": "*",
        }
        data = self.request_json(params, timeout)
        titles = data[1] if len(data) > 1 else []
        descriptions = data[2] if len(data) > 2 else []
        urls = data[3] if len(data) > 3 else []
        candidates = []
        for index, title in enumerate(titles):
            candidates.append(
                {
                    "title": title,
                    "description": descriptions[index] if index < len(descriptions) else "",
                    "url": urls[index] if index < len(urls) else self.build_page_url(title),
                }
            )

        return {
            "ok": bool(candidates),
            "source": "moegirl_mediawiki_api",
            "mode": "search",
            "query": query,
            "query_title": query,
            "resolved_title": candidates[0]["title"] if candidates else None,
            "pageid": None,
            "page_url": candidates[0]["url"] if candidates else None,
            "extract": candidates[0]["description"] if candidates else "",
            "extract_chars": len(candidates[0]["description"]) if candidates else 0,
            "candidates": candidates,
            "error": None if candidates else "no_candidates",
            "message": None if candidates else "No search candidates returned",
            "warnings": [] if candidates else ["no search candidates returned"],
            "fallbacks": [] if candidates else [
                "retry with the Chinese title, Japanese title, alias, or series name plus character name",
                "use --intro if the exact page title is known",
                "cross-check with Wikipedia, Fandom Wiki, Bangumi, AniDB, or official sources",
            ],
        }, data

    def query_wikitext(self, title, timeout):
        """通过 revisions API 获取原始 wikitext。

        权限受限或页面缺失时返回 None/错误记录，由调用方降级处理。
        """
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
            "redirects": "1",
            "origin": "*",
        }
        data = self.request_json(params, timeout)
        if "error" in data:
            error = data["error"]
            return self.fallback_error(title, error.get("code", "api_error"), error.get("info", "MediaWiki API error"), ["wikitext"]), data

        query_data = data.get("query", {})
        pages = query_data.get("pages", {})
        if not pages:
            return None, data

        page = next(iter(pages.values()))
        if page.get("missing") is not None or str(page.get("pageid", "")) == "-1":
            return None, data

        resolved_title = page.get("title", title)
        revisions = page.get("revisions", [])
        content = ""
        if revisions:
            slots = revisions[0].get("slots", {})
            main_slot = slots.get("main", {})
            content = main_slot.get("*", "") or main_slot.get("content", "") or ""

        return {
            "ok": bool(content.strip()),
            "source": "moegirl_mediawiki_api",
            "mode": "wikitext",
            "query": title,
            "query_title": title,
            "resolved_title": resolved_title,
            "pageid": page.get("pageid"),
            "page_url": self.build_page_url(resolved_title),
            "extract": content,
            "extract_chars": len(content),
            "candidates": [],
            "warnings": [] if content.strip() else ["empty wikitext"],
        }, data

    # ---------- 高层降级链 ----------

    def auto_query(self, query, timeout):
        """默认自动查询：简介 → 搜索 → 回退的降级链。

        当调用未指定 --intro/--full/--search/--wikitext 时使用。按代价从低到高依次尝试，
        尽量返回「可用的词条信息」而非直接报错；每尝试一步都累积到 attempted，
        供上层写入 sources.json，实现失败留证。
        """
        attempted = []

        # 第 1 步：把查询词当精确标题直接拉简介（exintro），命中即返回
        attempted.append("intro")
        intro_result, _ = self.query_extract(query, True, timeout)
        if intro_result and intro_result.get("ok"):
            return intro_result

        # 第 2 步：精确简介失败，改用搜索接口找候选标题
        attempted.append("search")
        search_result, _ = self.search_titles(query, timeout)
        if search_result.get("ok"):
            # 第 3 步：拿第一个候选标题再试简介
            first_title = search_result["candidates"][0]["title"]
            attempted.append("intro:first_search_candidate")
            candidate_result, _ = self.query_extract(first_title, True, timeout)
            if candidate_result and candidate_result.get("ok"):
                # 候选命中：附上候选列表与尝试路径，便于上层追踪
                candidate_result["candidates"] = search_result["candidates"]
                candidate_result["attempted_modes"] = attempted
                return candidate_result
            # 第 4 步：候选简介也失败，退回纯搜索结果（只有候选标题，供上层让用户选择）
            search_result["attempted_modes"] = attempted
            return search_result

        # 第 5 步：搜索也失败，返回缺页错误兜底
        return self.fallback_error(query, "missing_page", "No extract or search candidates returned", attempted)


def parse_args():
    parser = argparse.ArgumentParser(description="通过 MediaWiki API 获取 Moegirlpedia 条目")
    parser.add_argument("query", help="Moegirlpedia 页面标题、角色名、别名或搜索词")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--intro", action="store_true", help="获取页面简介提取内容")
    mode.add_argument("--full", action="store_true", help="获取页面全文纯文本提取内容")
    mode.add_argument("--search", action="store_true", help="搜索候选页面标题")
    mode.add_argument("--wikitext", action="store_true", help="通过 revisions API 获取原始 wikitext")
    parser.add_argument("--raw", action="store_true", help="附带原始 API 响应内容")
    parser.add_argument("--timeout", type=int, default=20, help="请求超时时间（秒）")
    return parser.parse_args()


def emit_json(payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8"))


def main():
    args = parse_args()
    client = MoegirlApiClient()
    attempted_modes = []

    try:
        raw = None
        if args.search:
            attempted_modes.append("search")
            result, raw = client.search_titles(args.query, args.timeout)
        elif args.full:
            attempted_modes.append("full")
            result, raw = client.query_extract(args.query, False, args.timeout)
            if result is None:
                result = client.fallback_error(args.query, "missing_page", "Page title not found", attempted_modes)
        elif args.wikitext:
            attempted_modes.append("wikitext")
            result, raw = client.query_wikitext(args.query, args.timeout)
            if result is None:
                result = client.fallback_error(args.query, "missing_page", "Page title not found", attempted_modes)
        elif args.intro:
            attempted_modes.append("intro")
            result, raw = client.query_extract(args.query, True, args.timeout)
            if result is None or not result.get("ok"):
                attempted_modes.append("search")
                search_result, search_raw = client.search_titles(args.query, args.timeout)
                raw = {"extract_response": raw, "search_response": search_raw}
                if search_result.get("ok"):
                    search_result["attempted_modes"] = attempted_modes
                    result = search_result
                else:
                    result = client.fallback_error(args.query, "missing_page", "Page title not found and search returned no candidates", attempted_modes)
        else:
            result = client.auto_query(args.query, args.timeout)

        if args.raw:
            result["raw"] = raw

        emit_json(result)
        return 0 if result.get("ok") else 1
    except urllib.error.HTTPError as exc:
        result = client.fallback_error(args.query, "http_error", f"HTTP {exc.code}: {exc.reason}", attempted_modes)
    except urllib.error.URLError as exc:
        result = client.fallback_error(args.query, "url_error", str(exc.reason), attempted_modes)
    except TimeoutError as exc:
        result = client.fallback_error(args.query, "timeout", str(exc), attempted_modes)
    except json.JSONDecodeError as exc:
        result = client.fallback_error(args.query, "json_decode_error", str(exc), attempted_modes)

    emit_json(result)
    return 1


if __name__ == "__main__":
    sys.exit(main())