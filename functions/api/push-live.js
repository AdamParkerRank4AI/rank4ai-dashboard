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

// Per-project CF Pages Deploy Hook IDs. Each hook is a unique URL that
// triggers a new deployment from the project's configured Git branch.
// Created once via the CF API (see POST /pages/projects/{name}/deploy_hooks).
// Hook IDs are not secret on their own but anyone with the ID can trigger
// a deploy, so we wrap the endpoint with EDIT_SECRET auth.
const SITE_CONFIG = {
  'rank4ai': {
    project: 'rank4ai-preview',
    hookId: 'fbb51eae-c449-412c-99f7-a01686b1ff32',
    accountId: 'a29a9e6a4fa4965762858586f129b445',
  },
  'market-invoice': {
    project: 'market-invoice',
    hookId: '3e647ae6-8048-4014-b424-ccb137adfa5f',
    accountId: 'a29a9e6a4fa4965762858586f129b445',
  },
  'seocompare': {
    project: 'seocompare',
    hookId: '2c148416-94e3-4fb1-a91d-84b5d012b229',
    accountId: '927d3dd61a9375f0c8185df7b2a1764e',
  },
  'dashboard': {
    project: 'rank4ai-dashboard',
    hookId: '0064972e-334f-4b49-8348-e3f666f13c04',
    accountId: 'a29a9e6a4fa4965762858586f129b445',
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

  // Fire the deploy hook. No auth needed on the hook itself (the hook ID
  // is the auth). POST with empty body triggers a new deployment from the
  // project's configured Git branch.
  const hookUrl = `https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/${conf.hookId}`;
  const r = await fetch(hookUrl, { method: 'POST' });
  const data = await r.json();
  if (!r.ok || !data.result) {
    return json({
      ok: false,
      error: 'Cloudflare deploy hook failed',
      cfStatus: r.status,
      cfResponse: data,
    }, 502);
  }

  return json({
    ok: true,
    site,
    project: conf.project,
    deployId: data.result.id,
    deploymentUrl: `https://dash.cloudflare.com/${conf.accountId}/pages/view/${conf.project}`,
    note: 'Deployment triggered. Usually live within 1–2 minutes.',
  });
}
