/**
 * Push-live API — triggers a Cloudflare Pages deployment on demand.
 *
 * Each Cloudflare Pages project auto-deploys on git push to its configured
 * branch. This endpoint forces a fresh deployment from the latest main
 * commit by calling the CF Pages API. Useful when the dashboard editor just
 * committed a change and we want immediate rebuild.
 *
 * POST /api/push-live
 * Header: Authorization: Bearer <EDIT_SECRET>
 * Body:  { site }
 *   site: 'rank4ai' | 'market-invoice' | 'seocompare' | 'dashboard'
 *
 * Env vars (set in Cloudflare Pages production settings):
 *   EDIT_SECRET            — same bearer as edit-page endpoint
 *   CF_TOKEN_RANK4AI       — Cloudflare API token for rank4ai account
 *                            (covers: rank4ai-preview, market-invoice,
 *                             rank4ai-dashboard projects)
 *   CF_TOKEN_MUSWELLROSE   — Cloudflare API token for muswellrose account
 *                            (covers: seocompare project)
 *
 * If the relevant token isn't set the endpoint returns a clear "not wired"
 * message rather than failing silently.
 */

const SITE_CONFIG = {
  'rank4ai': {
    accountEnv: 'CF_TOKEN_RANK4AI',
    accountId: 'a29a9e6a4fa4965762858586f129b445',
    project: 'rank4ai-preview',
  },
  'market-invoice': {
    accountEnv: 'CF_TOKEN_RANK4AI',
    accountId: 'a29a9e6a4fa4965762858586f129b445',
    project: 'market-invoice',
  },
  'seocompare': {
    accountEnv: 'CF_TOKEN_MUSWELLROSE',
    accountId: '927d3dd61a9375f0c8185df7b2a1764e',
    project: 'seocompare',
  },
  'dashboard': {
    accountEnv: 'CF_TOKEN_RANK4AI',
    accountId: 'a29a9e6a4fa4965762858586f129b445',
    project: 'rank4ai-dashboard',
  },
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  });
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

  if (!env.EDIT_SECRET) {
    return json({ ok: false, error: 'Server not configured. EDIT_SECRET env var required.' }, 500);
  }
  if ((request.headers.get('Authorization') || '') !== `Bearer ${env.EDIT_SECRET}`) {
    return json({ ok: false, error: 'Unauthorized' }, 401);
  }

  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: 'Invalid JSON' }, 400); }

  const { site } = body;
  const conf = SITE_CONFIG[site];
  if (!conf) return json({ ok: false, error: `Unknown site: ${site}` }, 400);

  const token = env[conf.accountEnv];
  if (!token) {
    return json({
      ok: false,
      error: `Push Live not wired for ${site}. Set ${conf.accountEnv} in Cloudflare Pages env vars.`,
      hint: 'Token is the value of ' + conf.accountEnv + ' in ~/.zshrc on Adam\'s machine.',
    }, 501);
  }

  // Trigger a new deployment from the configured Git branch (main)
  // Docs: https://developers.cloudflare.com/api/operations/pages-deployment-create-deployment
  const url = `https://api.cloudflare.com/client/v4/accounts/${conf.accountId}/pages/projects/${conf.project}/deployments`;
  const form = new FormData();
  form.append('branch', 'main');
  const r = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const data = await r.json();
  if (!r.ok || !data.success) {
    return json({
      ok: false,
      error: 'Cloudflare deploy trigger failed',
      cfStatus: r.status,
      cfErrors: data.errors,
    }, 502);
  }

  const d = data.result || {};
  return json({
    ok: true,
    site,
    project: conf.project,
    deployId: d.id,
    environment: d.environment,
    url: d.url,
    deploymentUrl: `https://dash.cloudflare.com/${conf.accountId}/pages/view/${conf.project}`,
    note: 'Deployment triggered. Usually live within 1–2 minutes.',
  });
}
