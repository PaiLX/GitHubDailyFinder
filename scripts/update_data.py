#!/usr/bin/env python3
"""
Daily data updater for GitHub Daily Finder.

Runs in GitHub Actions or locally:
1. Fetches GitHub repositories with GitHub Search API.
2. Classifies each repo into role-based parent/sub categories.
3. Optionally calls an OpenAI-compatible API for Chinese naming, purpose, value, and category refinement.
4. Writes static JSON files consumed by the frontend.

Required for higher GitHub API limits:
- GITHUB_TOKEN or GH_DATA_TOKEN

Optional for AI classification:
- AI_API_KEY
- AI_BASE_URL, default: https://api.openai.com/v1
- AI_MODEL, default: gpt-4o-mini
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
COMBINED_PATH = DATA_DIR / "combined.json"
TRANSLATIONS_PATH = DATA_DIR / "translations_v2.json"
REPORT_PATH = DATA_DIR / "update_report.json"

GITHUB_TOKEN = os.getenv("GH_DATA_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
AI_API_KEY = os.getenv("AI_API_KEY") or ""
AI_BASE_URL = (os.getenv("AI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
AI_MODEL = os.getenv("AI_MODEL") or "gpt-4o-mini"

PARENT_CATEGORIES = {
    "dev": {
        "title": "开发工具",
        "desc": "面向程序员和软件工程师的高效开发工具链。涵盖 AI 编程助手、代码框架、开发平台、构建工具等。",
        "audience": "适合全栈开发者、后端工程师、前端工程师、DevOps 工程师及所有写代码的人。",
        "queries": [
            "AI coding agent stars:>50 pushed:>2025-01-01",
            "developer tools CLI framework stars:>100 pushed:>2025-01-01",
            "documentation codebase agent stars:>50 pushed:>2025-01-01",
            "programming tools automation stars:>100 pushed:>2025-01-01",
        ],
        "subcats": {
            "ai-coding": ["ai", "agent", "llm", "coding", "code", "grok", "deepseek", "智能体"],
            "framework": ["framework", "sdk", "engine", "gateway", "connector", "platform", "框架", "平台"],
            "docs-learning": ["docs", "wiki", "documentation", "learn", "course", "algorithm", "文档", "学习"],
            "automation": ["cli", "terminal", "workflow", "automation", "tool", "自动化", "效率"],
        },
    },
    "design": {
        "title": "设计创意",
        "desc": "为设计师和创意工作者精选的工具和资源。包括字体生成、视觉设计、交互设计、动效工具等。",
        "audience": "适合 UI/UX 设计师、平面设计师、插画师、动效设计师及所有从事创意工作的人。",
        "queries": [
            "design tool visual generator stars:>50 pushed:>2025-01-01",
            "font generation UI design stars:>20 pushed:>2025-01-01",
            "animation creative video tool stars:>50 pushed:>2025-01-01",
            "awesome design system UI stars:>500 pushed:>2025-01-01",
        ],
        "subcats": {
            "visual": ["font", "visual", "image", "video", "3d", "生成", "视觉", "字体"],
            "ui": ["ui", "gui", "theme", "skin", "interface", "界面", "交互"],
            "content": ["markdown", "readme", "content", "layout", "排版", "内容"],
            "inspiration": ["awesome", "roadmap", "taxonomy", "resource", "资源", "灵感"],
        },
    },
    "product": {
        "title": "产品运营",
        "desc": "产品经理和创业者必备的工具集。涵盖项目管理、用户增长、数据分析、内容运营、商业化工具等。",
        "audience": "适合产品经理、创业者、运营人员、市场人员和所有想把产品做出去的人。",
        "queries": [
            "product management analytics growth stars:>50 pushed:>2025-01-01",
            "AI assistant productivity workflow stars:>50 pushed:>2025-01-01",
            "self hosted business content tool stars:>100 pushed:>2025-01-01",
            "open source marketing analytics dashboard stars:>50 pushed:>2025-01-01",
        ],
        "subcats": {
            "growth": ["growth", "marketing", "analytics", "dashboard", "用户", "增长", "运营"],
            "assistant": ["ai", "assistant", "agent", "助手", "智能体"],
            "workflow": ["workflow", "productivity", "management", "docs", "效率", "管理"],
            "business": ["business", "content", "selfhosted", "commerce", "商业", "内容"],
        },
    },
    "test": {
        "title": "测试安全",
        "desc": "软件测试、安全审计、渗透测试工具和实践。涵盖漏洞检测、代码质量、安全研究等。",
        "audience": "适合 QA 测试工程师、安全研究员、渗透测试人员、运维人员和关注代码质量的开发者。",
        "queries": [
            "security vulnerability exploit PoC stars:>50 pushed:>2025-01-01",
            "testing QA code quality tool stars:>50 pushed:>2025-01-01",
            "privacy network vpn tunnel stars:>50 pushed:>2025-01-01",
            "security learning computer science interview stars:>500 pushed:>2025-01-01",
        ],
        "subcats": {
            "security": ["security", "vulnerability", "exploit", "poc", "red team", "安全", "漏洞"],
            "testing": ["test", "qa", "quality", "benchmark", "测试", "质量"],
            "privacy": ["privacy", "vpn", "tor", "tunnel", "network", "隐私", "匿名"],
            "learning": ["book", "learn", "course", "interview", "kernel", "学习", "面试"],
        },
    },
}

SUBCAT_NAMES = {
    "ai-coding": "AI 编程",
    "framework": "框架与工程化",
    "docs-learning": "文档与学习",
    "automation": "自动化与效率",
    "visual": "视觉生成",
    "ui": "界面体验",
    "content": "内容排版",
    "inspiration": "灵感资源",
    "growth": "增长与获客",
    "assistant": "AI 助手",
    "workflow": "工作流效率",
    "business": "商业化与内容",
    "security": "安全研究",
    "testing": "测试与质量",
    "privacy": "隐私与网络",
    "learning": "安全学习",
}

LANG_COLORS = {
    "JavaScript": "#f7df1e", "TypeScript": "#3178c6", "Python": "#3572a5",
    "Rust": "#dea584", "Go": "#00add8", "Shell": "#89e051", "C": "#555555",
    "C++": "#f34b7d", "HTML": "#e34f26", "CSS": "#563d7c", "Java": "#b07219",
}

# Content safety filter: keep the public site focused on technical/product/design tools.
# Exclude repos/descriptions/topics that are political, activist, adult, hate, violent, or otherwise unsuitable for ad-supported public distribution.
BLOCKLIST_TERMS = [
    "politics", "political", "government", "election", "president", "congress", "senate",
    "communism", "capitalism", "socialism", "protest", "activism", "activist", "censorship",
    "china", "taiwan", "hong kong", "xinjiang", "tibet", "uyghur", "ccp", "996.icu",
    "war", "military", "weapon", "weapons", "gun", "terror", "terrorism", "nazi",
    "porn", "adult", "nsfw", "sex", "hentai", "hanime",
    "政治", "政党", "政府", "选举", "总统", "国会", "抗议", "示威", "维权", "审查",
    "中国", "台湾", "香港", "新疆", "西藏", "中共", "996", "战争", "军事", "武器",
    "恐怖", "纳粹", "色情", "成人", "黄色", "本子", "里番",
]

BLOCKLIST_REPOS = {
    "996icu/996.icu",
}


def repo_safety_text(repo: dict) -> str:
    return " ".join(str(x) for x in [
        repo.get("name", ""), repo.get("owner", ""), repo.get("description", ""),
        repo.get("cn_name", ""), repo.get("cn_desc", ""), repo.get("purpose", ""), repo.get("value", ""),
        *(repo.get("topics") or [])
    ]).lower()


def contains_blocked_term(text: str, term: str) -> bool:
    term_l = term.lower()
    # Latin words use word boundaries to avoid false positives like "war" in "software".
    if re.fullmatch(r"[a-z0-9_. -]+", term_l):
        pattern = r"(?<![a-z0-9])" + re.escape(term_l) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return term_l in text


def is_safe_repo(repo: dict) -> bool:
    name = str(repo.get("name", "")).lower()
    if name in BLOCKLIST_REPOS:
        return False
    text = repo_safety_text(repo)
    return not any(contains_blocked_term(text, term) for term in BLOCKLIST_TERMS)


def http_json(url: str, headers: dict | None = None, timeout: int = 25, method: str = "GET", body: bytes | None = None):
    final_headers = {"User-Agent": "GitHubDailyFinder/2.0", "Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN and "api.github.com" in url:
        final_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    if headers:
        final_headers.update(headers)
    req = urllib.request.Request(url, headers=final_headers, method=method, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_search(query: str, per_page: int = 20) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": per_page})
    url = f"https://api.github.com/search/repositories?{params}"
    try:
        data = http_json(url)
        return data.get("items", [])
    except Exception as exc:
        print(f"WARN search failed: {query}: {exc}")
        return []


def parse_repo(raw: dict) -> dict:
    lang = raw.get("language") or "Unknown"
    return {
        "name": raw.get("full_name", ""),
        "owner": raw.get("owner", {}).get("login", ""),
        "avatar_url": raw.get("owner", {}).get("avatar_url", ""),
        "description": raw.get("description") or "",
        "url": raw.get("html_url", ""),
        "language": lang,
        "stars": raw.get("stargazers_count", 0),
        "forks": raw.get("forks_count", 0),
        "topics": raw.get("topics", [])[:12],
        "created_at": (raw.get("created_at") or "")[:10],
        "updated_at": (raw.get("updated_at") or "")[:10],
        "color": LANG_COLORS.get(lang, "#8b949e"),
    }


def score_repo(repo: dict, cat_id: str) -> tuple[int, str]:
    hay = " ".join(str(x) for x in [repo.get("name"), repo.get("description"), repo.get("language"), *(repo.get("topics") or [])]).lower()
    subcats = PARENT_CATEGORIES[cat_id]["subcats"]
    best_sub, best = next(iter(subcats)), -1
    for sub, hints in subcats.items():
        score = sum(1 for h in hints if h.lower() in hay)
        if score > best:
            best_sub, best = sub, score
    star_score = min(int(repo.get("stars", 0) / 100), 1000)
    freshness = 0
    try:
        updated = datetime.fromisoformat((repo.get("updated_at") or "1970-01-01") + "T00:00:00+00:00")
        freshness = max(0, 180 - (datetime.now(timezone.utc) - updated).days)
    except Exception:
        pass
    return star_score + freshness + best * 50, best_sub


def fallback_translation(repo: dict, cat_id: str, sub_id: str) -> dict:
    repo_short = repo.get("name", "").split("/")[-1]
    desc = repo.get("description") or "优质开源项目，适合进一步研究和试用。"
    cat_title = PARENT_CATEGORIES[cat_id]["title"]
    sub_name = SUBCAT_NAMES.get(sub_id, "关注点")
    return {
        "cn_name": repo_short,
        "cn_desc": desc if contains_cjk(desc) else f"{repo_short}：{desc[:90]}",
        "purpose": f"用于{cat_title}场景下的{sub_name}需求，帮助用户快速验证项目能力。",
        "value": "可通过 README、Releases 或示例快速判断可用性，适合收藏、试跑或二次开发。",
        "parent_category": cat_id,
        "sub_category": sub_id,
        "category_reason": "基于仓库名称、描述、语言和 topics 的规则分类。",
    }


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def ai_enrich_batch(repos: list[dict], cat_id: str, sub_map: dict[str, str]) -> dict[str, dict]:
    if not AI_API_KEY:
        return {}
    compact = []
    for r in repos:
        compact.append({
            "repo": r["name"],
            "description": r.get("description", ""),
            "language": r.get("language", "Unknown"),
            "topics": r.get("topics", []),
            "suggested_parent": cat_id,
            "suggested_sub": sub_map.get(r["name"]),
        })
    prompt = {
        "task": "Classify and localize GitHub repos for a Chinese GitHub discovery website. Return strict JSON only.",
        "parent_categories": {k: v["title"] for k, v in PARENT_CATEGORIES.items()},
        "sub_category_names": SUBCAT_NAMES,
        "repos": compact,
        "output_schema": {
            "owner/repo": {
                "cn_name": "简洁中文名或保留英文品牌名",
                "cn_desc": "一句中文描述，不超过45字",
                "purpose": "项目作用，说明它解决什么问题",
                "value": "核心价值，说明为什么值得关注",
                "parent_category": "dev/design/product/test",
                "sub_category": "one sub id",
                "category_reason": "一句话分类原因"
            }
        }
    }
    body = json.dumps({
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "You output valid JSON only. No markdown."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ],
        "temperature": 0.2,
    }, ensure_ascii=False).encode("utf-8")
    try:
        data = http_json(
            f"{AI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
            method="POST",
            body=body,
            timeout=60,
        )
        content = data["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```json\s*|\s*```$", "", content, flags=re.S)
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        print(f"WARN AI enrich failed for {cat_id}: {exc}")
        return {}


def load_existing_translations() -> dict:
    if TRANSLATIONS_PATH.exists():
        try:
            return json.loads(TRANSLATIONS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def build_category(cat_id: str, existing_translations: dict) -> tuple[dict, dict]:
    seen = set()
    candidates = []
    for query in PARENT_CATEGORIES[cat_id]["queries"]:
        for raw in fetch_search(query, per_page=20):
            repo = parse_repo(raw)
            if not repo["name"] or repo["name"] in seen:
                continue
            if not is_safe_repo(repo):
                print(f"SKIP unsafe repo: {repo['name']}")
                continue
            seen.add(repo["name"])
            score, sub = score_repo(repo, cat_id)
            repo["sub_category"] = sub
            repo["score"] = score
            candidates.append(repo)
        time.sleep(0.8)
    candidates.sort(key=lambda r: (r.get("score", 0), r.get("stars", 0)), reverse=True)
    selected = candidates[:20]
    sub_map = {r["name"]: r.get("sub_category", "") for r in selected}
    ai_data = ai_enrich_batch(selected, cat_id, sub_map)
    translations_delta = {}
    enriched_repos = []
    for repo in selected:
        name = repo["name"]
        sub_id = sub_map.get(name) or score_repo(repo, cat_id)[1]
        t = existing_translations.get(name) or ai_data.get(name) or fallback_translation(repo, cat_id, sub_id)
        t.setdefault("parent_category", cat_id)
        t.setdefault("sub_category", sub_id)
        t.setdefault("category_reason", "规则分类")
        enriched = {k: v for k, v in repo.items() if k != "score"}
        enriched.update({
            "cn_name": t.get("cn_name", ""),
            "cn_desc": t.get("cn_desc", ""),
            "purpose": t.get("purpose", ""),
            "value": t.get("value", ""),
            "parent_category": t.get("parent_category", cat_id),
            "sub_category": t.get("sub_category", sub_id),
            "category_reason": t.get("category_reason", ""),
        })
        if not is_safe_repo(enriched):
            print(f"SKIP unsafe enriched repo: {name}")
            continue
        translations_delta[name] = t
        enriched_repos.append(enriched)
    meta = PARENT_CATEGORIES[cat_id]
    return {
        "id": cat_id,
        "title": meta["title"],
        "desc": meta["desc"],
        "audience": meta["audience"],
        "repos": enriched_repos,
    }, translations_delta


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_existing_translations()
    combined = {"generated_at": datetime.now().isoformat(), "categories": {}}
    all_translations = dict(existing)
    report = {"generated_at": combined["generated_at"], "categories": {}, "ai_enabled": bool(AI_API_KEY)}
    for cat_id in PARENT_CATEGORIES:
        print(f"Updating category: {cat_id}")
        cat_data, trans_delta = build_category(cat_id, existing)
        combined["categories"][cat_id] = cat_data
        all_translations.update(trans_delta)
        report["categories"][cat_id] = {
            "title": cat_data["title"],
            "count": len(cat_data["repos"]),
            "sub_counts": {},
        }
        for repo in cat_data["repos"]:
            sub = repo.get("sub_category", "unknown")
            report["categories"][cat_id]["sub_counts"][sub] = report["categories"][cat_id]["sub_counts"].get(sub, 0) + 1
    COMBINED_PATH.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    TRANSLATIONS_PATH.write_text(json.dumps(all_translations, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Updated data files:")
    print(f"- {COMBINED_PATH}")
    print(f"- {TRANSLATIONS_PATH}")
    print(f"- {REPORT_PATH}")


if __name__ == "__main__":
    main()
