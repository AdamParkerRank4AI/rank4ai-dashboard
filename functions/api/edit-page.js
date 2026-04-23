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
  'rank4ai':        { owner: 'AdamParkerRank4AI', repo: 'rank4ai-preview', pagesDir: 'src/pages' },
  'market-invoice': { owner: 'AdamParkerRank4AI', repo: 'market-invoice',  pagesDir: 'src/pages' },
  'seocompare':     { owner: 'AdamParkerRank4AI', repo: 'seocompare',      pagesDir: 'src/pages' },
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

  // Locate the source file
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
      error: 'Source file not found. This path might be generated from JSON data (blogs.json/questions.json) rather than a static .astro file — JSON editing is not yet supported.',
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

  return json({
    ok: true,
    filePath,
    patternMatched: which,
    commit: result.commit?.sha,
    commitUrl: result.commit?.html_url,
    deployNote: 'Cloudflare Pages will auto-deploy this commit within 1–2 minutes.',
  });
}
