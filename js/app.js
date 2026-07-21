// ===== State =====
let allData = null;
let historyData = [];
let translations = {};
let currentMode = 'category';
let currentCat = 'dev';
let currentDimension = 'fastest_growth';
let currentRoleDimension = 'recommended';
let currentSubcat = 'all';
let currentDate = 'latest';
let searchQuery = '';

const contentBlocklist = [
  'politics','political','government','election','president','congress','senate','protest','activism','activist','censorship',
  'china','taiwan','hong kong','xinjiang','tibet','uyghur','ccp','996.icu','war','military','weapon','terror','nazi',
  'porn','adult','nsfw','sex','hentai','hanime','政治','政党','政府','选举','总统','国会','抗议','示威','维权','审查',
  '中国','台湾','香港','新疆','西藏','中共','996','战争','军事','武器','恐怖','纳粹','色情','成人','黄色','本子','里番'
];
const blockedRepos = new Set(['996icu/996.icu']);

const roleSubcats = {
  dev: {
    label: '开发者关注点',
    items: [
      { id: 'ai-coding', name: 'AI 编程', hints: ['ai', 'agent', '智能体', 'llm', 'grok', 'deepseek', 'code model', '编程智能体'] },
      { id: 'framework', name: '框架与工程化', hints: ['framework', '框架', 'engine', '平台', 'sdk', 'gateway', 'connector'] },
      { id: 'docs-learning', name: '文档与学习', hints: ['wiki', 'docs', 'documentation', '文档', '算法', 'course', 'freecodecamp', 'learn'] },
      { id: 'automation', name: '自动化与效率', hints: ['cli', 'terminal', '工具', 'automation', '自动', 'workflow', 'slides'] }
    ]
  },
  design: {
    label: '设计师关注点',
    items: [
      { id: 'visual', name: '视觉生成', hints: ['font', '字体', 'visual', 'image', 'b-roll', '3d', 'scroll', 'video'] },
      { id: 'ui', name: '界面体验', hints: ['ui', 'gui', 'skin', 'theme', '界面', '交互', 'design'] },
      { id: 'content', name: '内容排版', hints: ['markdown', 'readme', '公众号', '排版', 'content', 'awesome'] },
      { id: 'inspiration', name: '灵感资源', hints: ['awesome', 'roadmap', 'taxonomy', 'system design', '资源', '合集'] }
    ]
  },
  product: {
    label: '产品运营关注点',
    items: [
      { id: 'growth', name: '增长与获客', hints: ['growth', 'marketing', '运营', '用户', 'analytics', 'viewer'] },
      { id: 'assistant', name: 'AI 助手', hints: ['ai', 'assistant', '助手', 'agent', 'cue'] },
      { id: 'workflow', name: '工作流效率', hints: ['workflow', 'management', 'product', '效率', '自动', 'docs'] },
      { id: 'business', name: '商业化与内容', hints: ['business', '商业', 'content', '内容', 'selfhosted', '社区'] }
    ]
  },
  test: {
    label: '测试安全关注点',
    items: [
      { id: 'security', name: '安全研究', hints: ['security', '漏洞', 'exploit', 'poc', 'red team', '红队', 'vpn'] },
      { id: 'testing', name: '测试与质量', hints: ['test', 'qa', 'quality', '测试', '验证', 'benchmark'] },
      { id: 'privacy', name: '隐私与网络', hints: ['privacy', '匿名', 'tor', 'vpn', 'tunnel', 'aether'] },
      { id: 'learning', name: '安全学习', hints: ['book', '学习', 'course', 'interview', 'kernel', 'programming'] }
    ]
  }
};

async function init() {
  await Promise.all([loadData(), loadTranslations(), loadHistory()]);
  setupFilters();
  renderLangPills();
  renderDateList();
  render();
  updateTime();
  setupTheme();
}

async function loadTranslations() {
  try {
    const resp = await fetch('data/translations_v2.json?t=' + Date.now());
    if (resp.ok) translations = await resp.json();
  } catch(e) { console.warn('翻译加载失败:', e); }
}

async function loadData() {
  const resp = await fetch('data/combined.json?t=' + Date.now());
  if (!resp.ok) throw new Error('数据加载失败');
  allData = await resp.json();
}

async function loadHistory() {
  try {
    const resp = await fetch('data/history.json?t=' + Date.now());
    if (resp.ok) historyData = await resp.json();
  } catch(e) { historyData = []; }
}

function activeSnapshot() {
  if (currentDate === 'latest') return allData;
  const snap = historyData.find(x => x.date === currentDate);
  return snap || allData;
}

function updateTime() {
  const el = document.getElementById('updatedTime');
  if (!el || !allData) return;
  const dateText = currentDate === 'latest' ? '最新数据' : currentDate;
  el.textContent = `${dateText} · 更新于 ${formatDate(new Date(activeSnapshot().generated_at || allData.generated_at))}`;
}

function formatDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${y}年${m}月${day}日 ${h}:${min}`;
}

function setupTheme() {
  const stored = localStorage.getItem('theme');
  if (stored === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
  document.getElementById('themeToggle').addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    document.documentElement.toggleAttribute('data-theme', !isDark);
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
  });
}

function getLangColor(lang) {
  const colors = {'JavaScript':'lang-js','TypeScript':'lang-ts','Python':'lang-py','Rust':'lang-rs','C':'lang-c','C++':'lang-cpp','Go':'lang-go','Shell':'lang-sh','Java':'lang-java','HTML':'lang-html','CSS':'lang-css'};
  return colors[lang] || '';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = String(str || '');
  return div.innerHTML;
}

function escapeAttr(str) {
  return String(str || '').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function formatNum(n) {
  n = Number(n || 0);
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return n.toString();
}

function hasBlockedTerm(text, term) {
  const lower = String(term).toLowerCase();
  if (/^[a-z0-9_. -]+$/.test(lower)) {
    return new RegExp(`(^|[^a-z0-9])${lower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^a-z0-9]|$)`).test(text);
  }
  return text.includes(lower);
}

function isSafeRepo(r) {
  const name = String(r?.name || '').toLowerCase();
  if (blockedRepos.has(name)) return false;
  const text = [r?.name, r?.owner, r?.description, r?.cn_name, r?.cn_desc, r?.purpose, r?.value, r?.category_reason, ...(r?.topics || [])].filter(Boolean).join(' ').toLowerCase();
  return !contentBlocklist.some(term => hasBlockedTerm(text, term));
}

function allReposFromSnapshot(snap = activeSnapshot()) {
  const repos = [];
  Object.values(snap?.categories || {}).forEach(cat => repos.push(...(cat.repos || [])));
  Object.values(snap?.dimensions || {}).forEach(dim => repos.push(...(dim.repos || [])));
  return repos;
}

function findRepo(name) {
  return allReposFromSnapshot().find(r => r.name === name) || null;
}

function availableDates() {
  return [...new Set(historyData.map(x => x.date).filter(Boolean))].sort().reverse();
}

function latestHistoryDate() {
  return availableDates()[0] || 'latest';
}

function dateLabel(value) {
  return value === 'latest' ? '最新推荐' : value;
}

function setCurrentDate(value) {
  currentDate = value;
  renderDateList();
  render();
  updateTime();
}

function snapshotForDate(date) {
  if (date === 'latest') return allData;
  return historyData.find(x => x.date === date) || allData;
}

function uniqueRepoCount(snap) {
  const names = new Set();
  allReposFromSnapshot(snap).forEach(repo => { if (repo?.name) names.add(repo.name); });
  return names.size;
}

function groupDatesByMonth(dates) {
  return dates.reduce((groups, date) => {
    const month = date.slice(0, 7);
    if (!groups[month]) groups[month] = [];
    groups[month].push(date);
    return groups;
  }, {});
}

function renderDateList() {
  const list = document.getElementById('dateList');
  if (!list) return;
  const dates = availableDates();
  const activeDate = currentDate === 'latest' ? latestHistoryDate() : currentDate;
  const groups = groupDatesByMonth(dates);
  list.innerHTML = Object.entries(groups).map(([month, monthDates]) => {
    const total = monthDates.reduce((sum, d) => sum + uniqueRepoCount(snapshotForDate(d)), 0);
    const rows = monthDates.map(d => {
      const day = d.slice(8, 10);
      const isActive = d === activeDate;
      const count = uniqueRepoCount(snapshotForDate(d));
      return `<button class="date-item ${isActive ? 'active' : ''}" data-date="${escapeAttr(d)}" type="button"><span>${escapeHtml(day)}</span><strong>${formatNum(count)}</strong></button>`;
    }).join('');
    return `<div class="date-month"><div class="date-month-head"><span>⌄ ${escapeHtml(month)}</span><strong>${formatNum(total)}</strong></div>${rows}</div>`;
  }).join('');
}

function renderLangPills() {
  const container = document.getElementById('langPills');
  if (!container) return;
  if (currentMode !== 'category') {
    container.innerHTML = '<button class="lang-pill active" data-lang="all">全部项目</button>';
    return;
  }
  const config = roleSubcats[currentCat] || roleSubcats.dev;
  const buttons = [`<button class="lang-pill active" data-lang="all">全部关注点</button>`];
  config.items.forEach(item => buttons.push(`<button class="lang-pill" data-lang="${escapeAttr(item.id)}">${escapeHtml(item.name)}</button>`));
  container.innerHTML = buttons.join('');
}


function subcatName(id, cat = currentCat) {
  const match = (roleSubcats[cat]?.items || []).find(item => item.id === id);
  return match?.name || id || '';
}

function repoMatchesSubcat(repo, subcatId) {
  if (subcatId === 'all') return true;
  if (repo.sub_category === subcatId) return true;
  const item = (roleSubcats[currentCat]?.items || []).find(x => x.id === subcatId);
  if (!item) return true;
  const haystack = [repo.name, repo.owner, repo.description, repo.cn_name, repo.cn_desc, repo.purpose, repo.value, repo.category_reason, ...(repo.topics || [])].filter(Boolean).join(' ').toLowerCase();
  return item.hints.some(hint => haystack.includes(String(hint).toLowerCase()));
}

function clearSearchInput() {
  searchQuery = '';
  const input = document.getElementById('searchInput');
  if (input) input.value = '';
}

function setupFilters() {
  // 一级分类固定为角色；增长最快/标星最多改到每个角色内部。

  document.querySelectorAll('.category-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.category-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCat = btn.dataset.cat;
      currentSubcat = 'all';
      currentRoleDimension = 'recommended';
      document.querySelectorAll('.role-dimension-tab').forEach(b => b.classList.toggle('active', b.dataset.roleDimension === currentRoleDimension));
      clearSearchInput();
      renderLangPills();
      render();
    });
  });

  document.querySelectorAll('.role-dimension-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.role-dimension-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentRoleDimension = btn.dataset.roleDimension;
      clearSearchInput();
      render();
    });
  });

  const langContainer = document.getElementById('langPills');
  langContainer.addEventListener('click', (e) => {
    const pill = e.target.closest('.lang-pill');
    if (!pill) return;
    const subcat = pill.dataset.lang;
    currentSubcat = subcat === 'all' ? 'all' : (currentSubcat === subcat ? 'all' : subcat);
    langContainer.querySelectorAll('.lang-pill').forEach(p => p.classList.remove('active'));
    const active = langContainer.querySelector(`[data-lang="${CSS.escape(currentSubcat)}"]`) || langContainer.querySelector('[data-lang="all"]');
    if (active) active.classList.add('active');
    render();
  });

  const searchInput = document.getElementById('searchInput');
  let searchTimeout;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      searchQuery = e.target.value.trim().toLowerCase();
      render();
    }, 200);
  });

  const dateList = document.getElementById('dateList');
  if (dateList) {
    dateList.addEventListener('click', e => {
      const item = e.target.closest('.date-item');
      if (!item) return;
      setCurrentDate(item.dataset.date);
    });
  }

  const contactBtn = document.getElementById('contactBtn');
  if (contactBtn) contactBtn.addEventListener('click', showContactModal);
  document.getElementById('refreshBtn').addEventListener('click', () => location.reload());
}

function activeCollection() {
  const snap = activeSnapshot();
  const cat = snap?.categories?.[currentCat] || allData?.categories?.[currentCat];
  return cat ? { ...cat, type: 'category' } : null;
}

function roleDimensionName(id = currentRoleDimension) {
  return { recommended: '默认推荐', fastest_growth: '增长最快', top_stars: '标星最多' }[id] || '默认推荐';
}

function repoAgeDays(repo) {
  const created = new Date((repo.created_at || '1970-01-01') + 'T00:00:00Z');
  const days = Math.max(1, Math.round((Date.now() - created.getTime()) / 86400000));
  return Number.isFinite(days) ? days : 9999;
}

function sortReposByRoleDimension(repos) {
  const list = [...repos];
  if (currentRoleDimension === 'top_stars') return list.sort((a, b) => (b.stars || 0) - (a.stars || 0));
  if (currentRoleDimension === 'fastest_growth') {
    return list.sort((a, b) => {
      const ag = a.growth_score ?? a.star_gain ?? ((a.stars || 0) / repoAgeDays(a));
      const bg = b.growth_score ?? b.star_gain ?? ((b.stars || 0) / repoAgeDays(b));
      return bg - ag || (b.stars || 0) - (a.stars || 0);
    });
  }
  return list;
}

function searchableText(r) {
  return [r.name, r.owner, r.description, r.language, r.cn_name, r.cn_desc, r.purpose, r.value, r.category_reason, ...(r.topics || [])]
    .filter(Boolean).join(' ').toLowerCase();
}

function render() {
  const collection = activeCollection();
  if (!collection) return;
  let repos = [...(collection.repos || [])].filter(isSafeRepo);

  const descEl = document.getElementById('catDesc');
  if (descEl) descEl.textContent = collection.desc || '';
  const audienceEl = document.getElementById('catAudience');
  if (audienceEl) {
    const audience = collection.audience || '';
    audienceEl.textContent = audience ? audience.replace(/^适合/, '适合').slice(0, 52) + (audience.length > 52 ? '…' : '') : '';
  }

  if (currentSubcat !== 'all') repos = repos.filter(r => repoMatchesSubcat(r, currentSubcat));
  repos = sortReposByRoleDimension(repos);
  if (searchQuery) repos = repos.filter(r => searchableText(r).includes(searchQuery));

  const activeSubcatName = currentSubcat === 'all' ? '全部关注点' : ((roleSubcats[currentCat]?.items || []).find(x => x.id === currentSubcat)?.name || '当前关注点');
  const statsEl = document.getElementById('statsSummary');
  if (statsEl) statsEl.innerHTML = `<span>${escapeHtml(dateLabel(currentDate === 'latest' ? latestHistoryDate() : currentDate))} · ${escapeHtml(collection.title || '')} · ${escapeHtml(activeSubcatName)} · ${escapeHtml(roleDimensionName())}</span><strong>${repos.length} / ${collection.repos.length} 个项目</strong>`;

  const grid = document.getElementById('cardMasonry');
  const empty = document.getElementById('emptyState');
  if (repos.length === 0) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  grid.innerHTML = repos.map(r => renderCard(r)).join('');
}

function renderCard(r) {
  const displayName = r.cn_name || r.name.split('/')[1] || r.name;
  const cnDesc = r.cn_desc || r.description || '暂无描述';
  const avatarUrl = r.avatar_url || '';
  const langColor = getLangColor(r.language);
  const initial = displayName.charAt(0).toUpperCase();
  const growth = r.star_gain !== undefined && r.star_gain !== null ? `+${formatNum(r.star_gain)}` : '';
  const growthMeta = growth ? `<span class="card-rank-growth">${growth}</span>` : `<span class="card-rank-growth muted">${Math.round((r.stars || 0) / repoAgeDays(r))}/天</span>`;
  const valueText = r.value || r.purpose || r.category_reason || '适合收藏、试跑或二次开发。';
  return `
    <div class="project-card" onclick="showModal('${escapeAttr(r.name)}')">
      <div class="card-top">
        ${avatarUrl ? `<img class="card-avatar" src="${avatarUrl}" alt="" loading="lazy" onerror="this.outerHTML='<div class=\\'card-avatar-placeholder\\'>${initial}</div>'">` : `<div class="card-avatar-placeholder">${initial}</div>`}
        <div class="card-info">
          <div class="card-title-row"><a class="card-title card-title-link" href="${r.url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${escapeHtml(displayName)}</a></div>
          <span class="card-owner">@${escapeHtml(r.owner)}</span>
        </div>
        <div class="card-rank"><strong>${formatNum(r.stars)}</strong><span>Stars</span>${growthMeta}</div>
      </div>
      <div class="card-desc">${escapeHtml(cnDesc)}</div>
      <div class="card-value">${escapeHtml(valueText)}</div>
      <div class="card-tags"><span class="tag-lang"><span class="dot ${langColor}"></span>${escapeHtml(r.language)}</span>${r.sub_category ? `<span class="tag-lang tag-subcat">${escapeHtml(subcatName(r.sub_category, r.parent_category || currentCat))}</span>` : ''}</div>
      <div class="card-footer">
        <div class="card-stats"><span class="card-stat">Forks ${formatNum(r.forks)}</span><span class="card-stat">Created ${escapeHtml(r.created_at)}</span><span class="card-stat">Updated ${escapeHtml(r.updated_at || '')}</span></div>
        <span class="card-arrow">›</span>
      </div>
    </div>`;
}

function showContactModal() {
  const html = `
    <div class="modal-overlay" onclick="if(event.target===this)this.remove()">
      <div class="contact-panel">
        <div class="contact-panel-header"><h2>联系我们</h2><button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button></div>
        <div class="contact-panel-body">
          <p>如需项目收录、广告合作、网站发布或功能建议，可以通过以下方式联系。</p>
          <div class="contact-items"><div class="contact-item"><span>邮箱</span><a href="mailto:1484247834@qq.com">1484247834@qq.com</a></div><div class="contact-item"><span>QQ</span><strong>1484247834</strong></div></div>
          <button class="btn-secondary contact-copy" onclick="copyContactInfo()">复制联系方式</button>
        </div>
      </div>
    </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
}

function copyContactInfo() {
  const text = '邮箱：1484247834@qq.com；QQ：1484247834';
  navigator.clipboard.writeText(text).then(() => {
    const btn = event.target;
    const orig = btn.textContent;
    btn.textContent = '已复制联系方式';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  });
}

function showModal(repoName) {
  const repo = findRepo(repoName);
  if (!repo) return;
  const displayName = repo.cn_name || repo.name.split('/')[1] || repo.name;
  const langColor = getLangColor(repo.language);
  const initial = displayName.charAt(0).toUpperCase();
  const growth = repo.star_gain !== undefined && repo.star_gain !== null ? `<span class="modal-stat">近次新增 ${repo.star_gain.toLocaleString()} Stars</span>` : '';
  let html = `
    <div class="modal-overlay" onclick="if(event.target===this)this.remove()"><div class="modal">
      <div class="modal-header">
        ${repo.avatar_url ? `<img class="modal-avatar" src="${repo.avatar_url}" alt="" onerror="this.outerHTML='<div class=\\'card-avatar-placeholder\\' style=\\'width:56px;height:56px;border-radius:12px;background:var(--bg-input);display:flex;align-items:center;justify-content:center;font-size:24px;color:var(--text-tertiary);border:2px solid var(--border)\\'>${initial}</div>'">` : `<div class="card-avatar-placeholder" style="width:56px;height:56px;border-radius:12px;background:var(--bg-input);display:flex;align-items:center;justify-content:center;font-size:24px;color:var(--text-tertiary);border:2px solid var(--border)">${initial}</div>`}
        <div class="modal-title-area"><div class="modal-title">${escapeHtml(displayName)}</div><div class="modal-cn-name">${escapeHtml(repo.name)}</div><div class="modal-owner">${escapeHtml(repo.owner)} · ${escapeHtml(repo.language)}</div></div>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
      </div><div class="modal-body">`;

  if (repo.cn_desc) html += `<div class="modal-section"><div class="modal-label">中文介绍</div><div class="modal-desc">${escapeHtml(repo.cn_desc)}</div></div>`;
  if (repo.purpose) html += `<div class="modal-section"><div class="modal-label">项目作用</div><div class="modal-desc">${escapeHtml(repo.purpose)}</div></div>`;
  if (repo.value) html += `<div class="modal-section"><div class="modal-label">核心价值</div><div class="modal-value">${escapeHtml(repo.value)}</div></div>`;
  if (repo.category_reason) html += `<div class="modal-section"><div class="modal-label">归类原因</div><div class="modal-desc">${escapeHtml(repo.category_reason)}</div></div>`;
  html += `<div class="modal-section"><div class="modal-label">项目数据</div><div class="modal-stats"><span class="modal-stat">Stars ${repo.stars.toLocaleString()}</span><span class="modal-stat">Forks ${repo.forks.toLocaleString()}</span>${growth}<span class="modal-stat">Created ${escapeHtml(repo.created_at)}</span><span class="modal-stat"><span class="dot ${langColor}" style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;"></span>${escapeHtml(repo.language)}</span></div></div>`;
  if (repo.topics && repo.topics.length > 0) html += `<div class="modal-section"><div class="modal-label">标签</div><div class="modal-tags">${repo.topics.slice(0, 8).map(t => `<span class="modal-tag">${escapeHtml(t)}</span>`).join('')}</div></div>`;
  html += `</div><div class="modal-actions"><a href="${repo.url}" target="_blank" rel="noopener" class="btn-primary" style="text-decoration:none;">前往 GitHub</a><button class="btn-secondary" onclick="copyLink('${escapeAttr(repo.url)}')">复制链接</button></div></div></div>`;
  document.body.insertAdjacentHTML('beforeend', html);
}

function copyLink(url) {
  navigator.clipboard.writeText(url).then(() => {
    const btn = event.target;
    const orig = btn.textContent;
    btn.textContent = '已复制 ✓';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  });
}

init();
