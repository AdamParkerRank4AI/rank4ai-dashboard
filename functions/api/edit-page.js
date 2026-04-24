/**
 * Edit-page API — patches title or meta description on a specific page of a
 * specific site, via GitHub API. Cloudflare auto-deploys after the commit.
 *
 * POST /api/edit-page
 * Header: Authorization: Bearer <EDIT_SECRET>
 * Body:  { site, path, field, newValue, dryRun? }
 *   site:     'rank4ai' | 'market-invoice' | 'seocompare'
 *   path:     URL path on the site, e.g. '/what-we-do/pricing/'
 *   field:    'title' | 'meta_desc'
 *   newValue: string
 *   dryRun:   boolean (optional) — returns what would change without committing
 *
 * Required env vars (set in Cloudflare Pages settings):
 *   EDIT_SECRET   — bearer token that UI must send
 *   GITHUB_TOKEN  — fine-grained PAT with contents:write on the 3 site repos
 */

const SITE_REPOS = {
  'rank4ai':        { owner: 'AdamParkerRank4AI', repo: 'rank4ai-preview', pagesDir: 'src/pages', dataDir: 'src/data', deployHookId: 'fbb51eae-c449-412c-99f7-a01686b1ff32' },
  'market-invoice': { owner: 'AdamParkerRank4AI', repo: 'market-invoice',  pagesDir: 'src/pages', dataDir: 'src/data', deployHookId: '3e647ae6-8048-4014-b424-ccb137adfa5f' },
  'seocompare':     { owner: 'AdamParkerRank4AI', repo: 'seocompare',      pagesDir: 'src/pages', dataDir: 'src/data', deployHookId: '2c148416-94e3-4fb1-a91d-84b5d012b229' },
};

// Fire a Cloudflare Pages deploy hook to force immediate deployment of a
// freshly-committed change. CF Pages GitHub webhook has been unreliable;
// this is the belt-and-braces safeguard so edits always reach live.
async function triggerDeployHook(hookId) {
  if (!hookId) return null;
  try {
    const r = await fetch(`https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/${hookId}`, { method: 'POST' });
    const d = await r.json();
    return d?.result?.id || null;
  } catch {
    return null;
  }
}

// Which URL prefix maps to which JSON data file + how the edit fields map
// onto that file's record schema. Only populated for sites/routes that are
// actually JSON-driven (R4 is the big one).
// For each mapping the fields object says: given an editor field name
// (title / meta_desc), which JSON record key do we write to?
const JSON_ROUTES = {
  'rank4ai': [
    {
      prefix: '/blog/',
      file: 'blogs.json',
      fields: { title: 'metaTitle', meta_desc: 'metaDesc' },
    },
    {
      prefix: '/learn/questions/',
      file: 'questions.json',
      fields: { title: 'metaTitle', meta_desc: 'metaDesc' },
    },
    {
      prefix: '/research/stats/',
      file: 'stats.json',
      fields: { title: 'title' },
    },
    {
      prefix: '/research/weekly-intelligence/',
      file: 'weekly.json',
      fields: { title: 'metaTitle', meta_desc: 'metaDesc' },
    },
  ],
};

const ALLOWED_FIELDS = new Set(['title', 'meta_desc']);
const MAX_FIELD_LENGTH = { title: 70, meta_desc: 160 };

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  });
}

function b64encode(str) {
  return btoa(unescape(encodeURIComponent(str)));
}
function b64decode(str) {
  return decodeURIComponent(escape(atob(str)));
}

// Given a site + url path, see if it's served from a JSON data file.
// Returns { file, slug, jsonKey } or null.
function resolveJsonRoute(site, urlPath, field) {
  const routes = JSON_ROUTES[site] || [];
  // Normalise: ensure trailing slash for prefix matching, then strip it to get slug
  const normalised = urlPath.endsWith('/') ? urlPath : urlPath + '/';
  for (const route of routes) {
    if (normalised.startsWith(route.prefix)) {
      const slug = normalised.slice(route.prefix.length).replace(/\/+$/, '');
      if (!slug) continue; // skip hub pages
      const jsonKey = route.fields[field];
      if (!jsonKey) {
        return { error: `This field (${field}) is not editable on ${route.prefix}* pages (only ${Object.keys(route.fields).join(', ')} are).` };
      }
      return { file: route.file, slug, jsonKey };
    }
  }
  return null;
}

// Map a URL path to the most likely source .astro file in the repo.
// Returns candidate file paths in priority order.
function candidateAstroPaths(urlPath, pagesDir) {
  // Strip trailing slash + leading slash
  let p = urlPath.replace(/\/+$/, '').replace(/^\/+/, '');
  if (p === '') p = 'index';
  const parts = p.split('/');
  // Try:
  //  1. pagesDir/<p>.astro             (single file)
  //  2. pagesDir/<p>/index.astro       (directory with index)
  return [
    `${pagesDir}/${parts.join('/')}.astro`,
    `${pagesDir}/${parts.join('/')}/index.astro`,
  ];
}

async function ghGet({ owner, repo, path, token }) {
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=main`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'rank4ai-dashboard-edit',
    },
  });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`GitHub GET ${path} failed: ${r.status} ${await r.text()}`);
  return await r.json();
}

async function ghPut({ owner, repo, path, content, sha, message, token }) {
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'rank4ai-dashboard-edit',
    },
    body: JSON.stringify({
      message,
      content: b64encode(content),
      sha,
      branch: 'main',
      committer: { name: 'Rank4AI Dashboard', email: 'dashboard@rank4ai.co.uk' },
    }),
  });
  if (!r.ok) throw new Error(`GitHub PUT ${path} failed: ${r.status} ${await r.text()}`);
  return await r.json();
}

// Patch a title or description in an .astro file source.
// Returns { patched: string, changes: number, which: string } or throws.
function patchAstroSource(src, field, newValue) {
  const changes = [];

  if (field === 'title') {
    // Pattern 1: const title = "..."
    const constRe = /(^\s*const\s+title\s*=\s*)"([^"]+)"(\s*;?\s*$)/m;
    if (constRe.test(src)) {
      src = src.replace(constRe, (_, pre, _old, post) => {
        changes.push('const title');
        return `${pre}"${newValue.replace(/"/g, '\\"')}"${post}`;
      });
    } else {
      // Pattern 2: <Layout title="..."  or  <BaseLayout title="..."  or  <ArticleLayout title="..."
      const layoutRe = /(<(?:Layout|BaseLayout|ArticleLayout)\s+title\s*=\s*)"([^"]+)"/;
      if (layoutRe.test(src)) {
        src = src.replace(layoutRe, (_, pre, _old) => {
          changes.push('Layout title prop');
          return `${pre}"${newValue.replace(/"/g, '\\"')}"`;
        });
      }
    }
  } else if (field === 'meta_desc') {
    const constRe = /(^\s*const\s+description\s*=\s*)"([^"]+)"(\s*;?\s*$)/m;
    if (constRe.test(src)) {
      src = src.replace(constRe, (_, pre, _old, post) => {
        changes.push('const description');
        return `${pre}"${newValue.replace(/"/g, '\\"')}"${post}`;
      });
    } else {
      // Try <Layout description="..."
      const layoutRe = /(<(?:Layout|BaseLayout|ArticleLayout)[^>]*\sdescription\s*=\s*)"([^"]+)"/;
      if (layoutRe.test(src)) {
        src = src.replace(layoutRe, (_, pre, _old) => {
          changes.push('Layout description prop');
          return `${pre}"${newValue.replace(/"/g, '\\"')}"`;
        });
      }
    }
  }

  return { patched: src, changes: changes.length, which: changes.join(', ') };
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

  const EDIT_SECRET = env.EDIT_SECRET;
  const GITHUB_TOKEN = env.GITHUB_TOKEN;
  if (!EDIT_SECRET || !GITHUB_TOKEN) {
    return json({ ok: false, error: 'Server not configured. EDIT_SECRET + GITHUB_TOKEN env vars required.' }, 500);
  }

  const auth = request.headers.get('Authorization') || '';
  if (auth !== `Bearer ${EDIT_SECRET}`) {
    return json({ ok: false, error: 'Unauthorized' }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid JSON' }, 400);
  }

  const { site, path, field, newValue, dryRun } = body;
  const repoConf = SITE_REPOS[site];
  if (!repoConf) return json({ ok: false, error: `Unknown site: ${site}` }, 400);
  if (!ALLOWED_FIELDS.has(field)) return json({ ok: false, error: `Field not editable: ${field}` }, 400);
  if (typeof newValue !== 'string') return json({ ok: false, error: 'newValue must be a string' }, 400);
  if (newValue.length === 0) return json({ ok: false, error: 'newValue cannot be empty' }, 400);
  if (newValue.length > 500) return json({ ok: false, error: 'newValue too long (max 500 chars)' }, 400);
  if (newValue.length > MAX_FIELD_LENGTH[field]) {
    return json({
      ok: false,
      error: `${field} exceeds recommended length (${newValue.length} > ${MAX_FIELD_LENGTH[field]} chars). Shorten and retry.`,
    }, 400);
  }

  // FIRST: try JSON-driven route (R4 blogs/questions/stats/weekly)
  const jsonRoute = resolveJsonRoute(site, path, field);
  if (jsonRoute && jsonRoute.error) {
    return json({ ok: false, error: jsonRoute.error }, 400);
  }
  if (jsonRoute && jsonRoute.file) {
    const filePath = `${repoConf.dataDir}/${jsonRoute.file}`;
    const gh = await ghGet({ owner: repoConf.owner, repo: repoConf.repo, path: filePath, token: GITHUB_TOKEN });
    if (!gh) {
      return json({ ok: false, error: `JSON file not found: ${filePath}` }, 404);
    }
    const src = b64decode(gh.content.replace(/\n/g, ''));
    let data;
    try {
      data = JSON.parse(src);
    } catch (e) {
      return json({ ok: false, error: `JSON parse failed on ${filePath}: ${e.message}` }, 500);
    }
    if (!Array.isArray(data)) {
      return json({ ok: false, error: `${filePath} is not a list` }, 500);
    }

    const entryIdx = data.findIndex((e) => e && e.slug === jsonRoute.slug);
    if (entryIdx < 0) {
      return json({
        ok: false,
        error: `Slug "${jsonRoute.slug}" not found in ${filePath}. Known first slugs: ${data.slice(0, 3).map(e => e.slug).join(', ')}…`,
        filePath,
      }, 404);
    }

    const oldValue = data[entryIdx][jsonRoute.jsonKey];
    if (oldValue === newValue) {
      return json({ ok: true, noChange: true, filePath, slug: jsonRoute.slug });
    }
    data[entryIdx][jsonRoute.jsonKey] = newValue;

    // Match existing file's indentation. Most R4 JSON uses 2-space indent.
    const patched = JSON.stringify(data, null, 2) + '\n';

    if (dryRun) {
      return json({
        ok: true,
        dryRun: true,
        filePath,
        slug: jsonRoute.slug,
        jsonKey: jsonRoute.jsonKey,
        old: oldValue,
        new: newValue,
      });
    }

    const commitMessage = `Dashboard edit: update ${jsonRoute.jsonKey} on ${path}

Set via Rank4AI Dashboard Page Compliance editor (JSON route).
Slug: ${jsonRoute.slug}
Field: ${field} → ${jsonRoute.jsonKey}
File: ${filePath}
New value: ${newValue.slice(0, 80)}${newValue.length > 80 ? '…' : ''}`;

    const result = await ghPut({
      owner: repoConf.owner,
      repo: repoConf.repo,
      path: filePath,
      content: patched,
      sha: gh.sha,
      message: commitMessage,
      token: GITHUB_TOKEN,
    });

    // Force immediate deployment — CF GitHub webhook has been unreliable
    const deployId = await triggerDeployHook(repoConf.deployHookId);

    return json({
      ok: true,
      filePath,
      jsonKey: jsonRoute.jsonKey,
      slug: jsonRoute.slug,
      commit: result.commit?.sha,
      commitUrl: result.commit?.html_url,
      deployTriggered: !!deployId,
      deployId,
      deployNote: deployId
        ? 'Deploy hook fired. Usually live in 1-2 minutes.'
        : 'Committed. Waiting for CF auto-deploy (may be delayed — check dashboard parity).',
    });
  }

  // FALLBACK: static .astro file
  const candidates = candidateAstroPaths(path, repoConf.pagesDir);
  let file = null;
  let filePath = null;
  for (const candidate of candidates) {
    const f = await ghGet({ owner: repoConf.owner, repo: repoConf.repo, path: candidate, token: GITHUB_TOKEN });
    if (f) { file = f; filePath = candidate; break; }
  }
  if (!file) {
    return json({
      ok: false,
      error: 'Source file not found. Path not matched by any .astro file or JSON route.',
      tried: candidates,
    }, 404);
  }

  const src = b64decode(file.content.replace(/\n/g, ''));
  const { patched, changes, which } = patchAstroSource(src, field, newValue);

  if (changes === 0) {
    return json({
      ok: false,
      error: `Could not find ${field} pattern in ${filePath}. Expected either "const ${field === 'title' ? 'title' : 'description'} = ..." or a Layout prop. Manual edit may be needed.`,
      filePath,
    }, 422);
  }

  if (dryRun) {
    return json({
      ok: true,
      dryRun: true,
      filePath,
      patternMatched: which,
      changes,
      preview: patched.slice(0, 400),
    });
  }

  const commitMessage = `Dashboard edit: update ${field} on ${path}

Set via Rank4AI Dashboard Page Compliance editor.
Field: ${field}
New value: ${newValue.slice(0, 80)}${newValue.length > 80 ? '…' : ''}
File: ${filePath}`;

  const result = await ghPut({
    owner: repoConf.owner,
    repo: repoConf.repo,
    path: filePath,
    content: patched,
    sha: file.sha,
    message: commitMessage,
    token: GITHUB_TOKEN,
  });

  const deployId = await triggerDeployHook(repoConf.deployHookId);

  return json({
    ok: true,
    filePath,
    patternMatched: which,
    commit: result.commit?.sha,
    commitUrl: result.commit?.html_url,
    deployTriggered: !!deployId,
    deployId,
    deployNote: deployId
      ? 'Deploy hook fired. Usually live in 1-2 minutes.'
      : 'Committed. Waiting for CF auto-deploy (may be delayed — check dashboard parity).',
  });
}
