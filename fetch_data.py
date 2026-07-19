#!/usr/bin/env python3
"""
GitHubDailyFinder - 数据拉取脚本
每日定时拉取GitHub高星开源项目，输出JSON缓存
"""
import urllib.request
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'repos.json')

LANG_COLORS = {
    'JavaScript': '#f1e05a', 'Python': '#3572A5', 'TypeScript': '#2b7489',
    'Rust': '#dea584', 'Go': '#00ADD8', 'Java': '#b07219',
    'C': '#555555', 'C++': '#f34b7d', 'Ruby': '#701516',
    'Swift': '#F05138', 'Kotlin': '#A97BFF', 'Vue': '#41b883',
    'HTML': '#e34c26', 'CSS': '#563d7c', 'Shell': '#89e051',
    'PHP': '#4F5D95', 'Dart': '#00B4AB', 'Lua': '#000080',
    'Scala': '#c22d40', 'R': '#198CE7', 'Zig': '#ec915c',
}

def fetch_repos(query, per_page=30):
    """从GitHub Search API获取仓库列表"""
    url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc&per_page={per_page}"
    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHubDailyFinder/1.0'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        return data.get('items', [])
    except Exception as e:
        print(f"  ❌ 请求失败: {e}", file=sys.stderr)
        return []

def parse_repo(raw):
    """解析单个仓库数据"""
    stars = raw.get('stargazers_count', 0)
    forks = raw.get('forks_count', 0)
    lang = raw.get('language') or 'Unknown'
    return {
        'name': raw['full_name'],
        'owner': raw['owner']['login'],
        'avatar_url': raw['owner']['avatar_url'],
        'description': raw.get('description') or '暂无描述',
        'url': raw['html_url'],
        'language': lang,
        'stars': stars,
        'forks': forks,
        'topics': raw.get('topics', [])[:5],
        'created_at': raw['created_at'][:10],
        'updated_at': raw['updated_at'][:10],
        'color': LANG_COLORS.get(lang, '#8b949e'),
    }

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    print(f"🔄 拉取时间: {today}")
    print(f"📁 输出文件: {OUTPUT_FILE}")
    print()

    data = {
        'generated_at': datetime.now().isoformat(),
        'categories': {}
    }

    # 1. 今日高星
    print("📅 拉取今日新增高星项目...")
    repos = fetch_repos(f"created:{today} stars:>5", per_page=30)
    data['categories']['today'] = {
        'title': '今日新星',
        'subtitle': f'{today} 创建的热门项目',
        'repos': [parse_repo(r) for r in repos[:20]]
    }
    print(f"  ✅ 找到 {len(data['categories']['today']['repos'])} 个项目")

    # 2. 本周高星
    print("📅 拉取本周新增高星项目...")
    repos = fetch_repos(f"created:>{week_ago} stars:>50", per_page=30)
    data['categories']['week'] = {
        'title': '本周热门',
        'subtitle': f'{week_ago} 至今创建的热门项目',
        'repos': [parse_repo(r) for r in repos[:20]]
    }
    print(f"  ✅ 找到 {len(data['categories']['week']['repos'])} 个项目")

    # 3. 本月高星
    print("📅 拉取本月新增高星项目...")
    repos = fetch_repos(f"created:>{month_ago} stars:>200", per_page=30)
    data['categories']['month'] = {
        'title': '本月精选',
        'subtitle': f'{month_ago} 至今创建的热门项目',
        'repos': [parse_repo(r) for r in repos[:20]]
    }
    print(f"  ✅ 找到 {len(data['categories']['month']['repos'])} 个项目")

    # 4. 总榜精选（经典项目）
    print("🏆 拉取总榜精选项目...")
    repos = fetch_repos("stars:>10000 pushed:>2025-01-01", per_page=30)
    data['categories']['featured'] = {
        'title': '精选经典',
        'subtitle': '持续活跃的高星项目',
        'repos': [parse_repo(r) for r in repos[:20]]
    }
    print(f"  ✅ 找到 {len(data['categories']['featured']['repos'])} 个项目")

    # 5. 按语言分类
    print("🌐 拉取各语言热门项目...")
    lang_queries = {
        'javascript': 'stars:>1000 language:javascript',
        'python': 'stars:>1000 language:python',
        'rust': 'stars:>500 language:rust',
        'go': 'stars:>1000 language:go',
        'typescript': 'stars:>1000 language:typescript',
    }
    data['languages'] = {}
    for key, q in lang_queries.items():
        repos = fetch_repos(q, per_page=10)
        data['languages'][key] = {
            'repos': [parse_repo(r) for r in repos[:10]]
        }
        print(f"  ✅ {key}: {len(data['languages'][key]['repos'])} 个项目")

    # 保存JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(v['repos']) for v in data['categories'].values())
    print(f"\n✅ 完成! 共 {total} 个项目, 已保存到 {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
