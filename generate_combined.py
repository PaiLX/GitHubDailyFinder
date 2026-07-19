#!/usr/bin/env python3
"""
合并 repos.json + translations + categories 生成最终数据
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data')

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    repos_data = load_json(os.path.join(DATA_DIR, 'repos.json'))
    translations = load_json(os.path.join(DATA_DIR, 'translations_v2.json'))
    
    # Build a lookup: name -> repo object
    repo_lookup = {}
    for cat_key, cat_val in repos_data['categories'].items():
        for r in cat_val['repos']:
            if r['name'] not in repo_lookup:
                repo_lookup[r['name']] = r
    
    # Build category mappings
    category_map = {
        'dev': '开发工具',
        'design': '设计创意', 
        'product': '产品运营',
        'test': '测试安全'
    }
    
    # Generate enriched data
    result = {
        'generated_at': repos_data['generated_at'],
        'categories': {}
    }
    
    for cat_id, cat_title in category_map.items():
        # Get repos for this category
        repos = []
        for name in repos_data['categories']['featured']['repos'] if cat_id == 'dev' else repos_data['categories']['month']['repos']:
            if len(repos) >= 20:
                break
            repo = repo_lookup.get(name['name'], {})
            if repo:
                t = translations.get(name['name'], {})
                enriched = {
                    'name': repo['name'],
                    'owner': repo.get('owner', name['name'].split('/')[0]),
                    'avatar_url': repo.get('avatar_url', ''),
                    'description': repo.get('description', '') or t.get('cn_desc', ''),
                    'url': repo.get('url', ''),
                    'language': repo.get('language', 'Unknown'),
                    'stars': repo.get('stars', 0),
                    'forks': repo.get('forks', 0),
                    'topics': repo.get('topics', []),
                    'created_at': repo.get('created_at', ''),
                    'cn_name': t.get('cn_name', ''),
                    'cn_desc': t.get('cn_desc', ''),
                    'purpose': t.get('purpose', ''),
                    'value': t.get('value', '')
                }
                repos.append(enriched)
        
        result['categories'][cat_id] = {
            'id': cat_id,
            'title': cat_title,
            'repos': repos[:20]
        }
    
    # Write output
    output_path = os.path.join(DATA_DIR, 'combined.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Generated combined.json with {len(result['categories'])} categories")
    for cat_id, cat_data in result['categories'].items():
        print(f"  {cat_data['title']}: {len(cat_data['repos'])} repos")

if __name__ == '__main__':
    main()
