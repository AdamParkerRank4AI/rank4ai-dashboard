/**
 * Create-page API — adds a new page to a site via GitHub API.
 *
 * Supports JSON-driven routes (R4 blogs / questions / stats / weekly) in
 * Phase 1. Static .astro page creation is future work (needs templates).
 *
 * POST /api/create-page
 * Header: Authorization: Bearer <EDIT_SECRET>
 * Body:  { site, type, slug, title, metaTitle?, metaDesc?, bodyContent?, ..., dryRun? }
 *   site:     'rank4ai'
 *   type:     'blog' | 'question' | 'stat' | 'weekly'
 *   slug:     URL-safe slug, unique within the file
 *   title:    (blog/stat/weekly) page title  —OR—
 *   question: (question type) full question text
 *   metaTitle/metaDesc: optional overrides
 *   bodyContent: optional HTML string (blog/question)
 *   publishedAt: optional ISO date (blogs)
 *   author: optional (blogs)
 *
 * Validates schema + duplicate slug check. Commits the updated JSON file
 * and triggers the site's CF Pages deploy hook immediately.
 */

const SITE_REPOS = {
  'rank4ai': {
    owner: 'AdamParkerRank4AI',
    repo: 'rank4ai-preview',
    dataDir: 'src/data',
    deployHookId: 'fbb51eae-c449-412c-99f7-a01686b1ff32',
  },
};

const PAGE_TYPES = {
  blog: {
    file: 'blogs.json',
    urlPrefix: '/blog/',
    required: ['slug', 'title'],
    defaults: (body) => ({
      slug: body.slug,
      title: body.title,
      metaTitle: body.metaTitle || `${body.title} | Rank4AI`,
      metaDesc: body.metaDesc || '',
      primaryQuestion: body.primaryQuestion || body.title,
      directAnswer: body.directAnswer || '',
      bodyContent: body.bodyContent || `<p>${body.title}</p>`,
      cardExcerpt: body.cardExcerpt || body.metaDesc || '',
      author: body.author || 'Adam Parker',
      publishedAt: body.publishedAt || new Date().toISOString().slice(0, 10),
      updatedAt: body.updatedAt || new Date().toISOString().slice(0, 10),
      faqCount: body.faqCount || 0,
    }),
  },
  question: {
    file: 'questions.json',
    urlPrefix: '/learn/questions/',
    required: ['slug', 'question'],
    defaults: (body) => ({
      slug: body.slug,
      question: body.question,
      metaTitle: body.metaTitle || `${body.question.slice(0, 58).replace(/\?+$/, '')}? | Rank4AI`,
      metaDesc: body.metaDesc || '',
      category: body.category || 'general',
      signalCategory: body.signalCategory || '',
      conciseAnswer: body.conciseAnswer || '',
      fullAnswer: body.fullAnswer || '',
      updatedAt: body.updatedAt || new Date().toISOString().slice(0, 10),
    }),
  },
  stat: {
    file: 'stats.json',
    urlPrefix: '/research/stats/',
    required: ['slug', 'title'],
    defaults: (body) => ({
      slug: body.slug,
      title: body.title,
      statValue: body.statValue || '',
      source: body.source || '',
      publishedAt: body.publishedAt || new Date().toISOString().slice(0, 10),
    }),
  },
  weekly: {
    file: 'weekly.json',
    urlPrefix: '/research/weekly-intelligence/',
    required: ['slug', 'title'],
    defaults: (body) => ({
      slug: body.slug,
      title: body.title,
      metaTitle: body.metaTitle || `${body.title} | Rank4AI`,
      metaDesc: body.metaDesc || '',
      publishedAt: body.publishedAt || new Date().toISOString().slice(0, 10),
    }),
  },
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  });
}
function b64encode(str) { return btoa(unescape(encodeURIComponent(str))); }
function b64decode(str) { return decodeURIComponent(escape(atob(str))); }

async function ghGet({ owner, repo, path, token }) {
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=main`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'User-Agent': 'rank4ai-dashboard-create' },
  });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`GitHub GET ${path}: ${r.status}`);
  return await r.json();
}
async function ghPut({ owner, repo, path, content, sha, message, token }) {
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'Content-Type': 'application/json', 'User-Agent': 'rank4ai-dashboard-create' },
    body: JSON.stringify({
      message, content: b64encode(content), sha, branch: 'main',
      committer: { name: 'Rank4AI Dashboard', email: 'dashboard@rank4ai.co.uk' },
    }),
  });
  if (!r.ok) throw new Error(`GitHub PUT ${path}: ${r.status} ${await r.text()}`);
  return await r.json();
}
async function triggerDeployHook(hookId) {
  if (!hookId) return null;
  try {
    const r = await fetch(`https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/${hookId}`, { method: 'POST' });
    const d = await r.json();
    return d?.result?.id || null;
  } catch { return null; }
}

function sanitiseSlug(s) {
  return String(s || '')
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.EDIT_SECRET || !env.GITHUB_TOKEN) {
    return json({ ok: false, error: 'Server not configured (EDIT_SECRET + GITHUB_TOKEN required)' }, 500);
  }
  if ((request.headers.get('Authorization') || '') !== `Bearer ${env.EDIT_SECRET}`) {
    return json({ ok: false, error: 'Unauthorized' }, 401);
  }

  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: 'Invalid JSON' }, 400); }

  const { site, type, dryRun } = body;
  const repoConf = SITE_REPOS[site];
  if (!repoConf) return json({ ok: false, error: `Unknown site: ${site}` }, 400);
  const typeConf = PAGE_TYPES[type];
  if (!typeConf) return json({ ok: false, error: `Unknown page type: ${type}. Supported: ${Object.keys(PAGE_TYPES).join(', ')}` }, 400);

  // Normalise slug
  body.slug = sanitiseSlug(body.slug);
  if (!body.slug) return json({ ok: false, error: 'Slug required (derived from your input after URL-safe sanitisation)' }, 400);

  // Required fields
  for (const f of typeConf.required) {
    if (!body[f] || !String(body[f]).trim()) {
      return json({ ok: false, error: `Field required: ${f}` }, 400);
    }
  }

  const filePath = `${repoConf.dataDir}/${typeConf.file}`;
  const existing = await ghGet({ owner: repoConf.owner, repo: repoConf.repo, path: filePath, token: env.GITHUB_TOKEN });
  if (!existing) return json({ ok: false, error: `Data file not found: ${filePath}` }, 404);

  let data;
  try {
    data = JSON.parse(b64decode(existing.content.replace(/\n/g, '')));
  } catch (e) {
    return json({ ok: false, error: `JSON parse failed on ${filePath}: ${e.message}` }, 500);
  }
  if (!Array.isArray(data)) return json({ ok: false, error: `${filePath} is not a list` }, 500);

  // Duplicate slug check
  if (data.some((e) => e?.slug === body.slug)) {
    return json({ ok: false, error: `Slug '${body.slug}' already exists in ${filePath}` }, 409);
  }

  const entry = typeConf.defaults(body);

  if (dryRun) {
    return json({
      ok: true,
      dryRun: true,
      filePath,
      entry,
      liveUrl: `https://www.rank4ai.co.uk${typeConf.urlPrefix}${body.slug}/`,
      note: 'Nothing committed. Remove dryRun to actually create.',
    });
  }

  // Append + write back (keep existing indentation style — 2 space)
  data.push(entry);
  const patched = JSON.stringify(data, null, 2) + '\n';

  const commitMessage = `Dashboard: create ${type} page '${body.slug}'

Set via Rank4AI Dashboard page-create.
Type: ${type}
Slug: ${body.slug}
Title: ${(body.title || body.question || '').slice(0, 80)}
File: ${filePath}`;

  const result = await ghPut({
    owner: repoConf.owner,
    repo: repoConf.repo,
    path: filePath,
    content: patched,
    sha: existing.sha,
    message: commitMessage,
    token: env.GITHUB_TOKEN,
  });

  const deployId = await triggerDeployHook(repoConf.deployHookId);

  return json({
    ok: true,
    filePath,
    type,
    slug: body.slug,
    liveUrl: `https://www.rank4ai.co.uk${typeConf.urlPrefix}${body.slug}/`,
    commit: result.commit?.sha,
    commitUrl: result.commit?.html_url,
    deployTriggered: !!deployId,
    deployId,
    deployNote: deployId
      ? 'Deploy hook fired. Page should be live in 1-2 minutes.'
      : 'Committed. Awaiting CF auto-deploy (may be delayed).',
  });
}
