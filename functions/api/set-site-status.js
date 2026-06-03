/**
 * Set a site's lifecycle status in src/data/clients.json.
 *
 * POST /api/set-site-status
 * Header: Authorization: Bearer <EDIT_SECRET>
 * Body:  { clientId, status }
 *   clientId: client entry id in clients.json
 *   status:   one of live | prelaunch | paused | needs
 *
 * Writes back to the rank4ai-dashboard repo on main, fires the deploy hook.
 * The committed clients.json is the single source of truth: the dashboard
 * display rebuilds from it, and the Python fetchers read it (via
 * scripts/site_status.py) to skip non-live sites on their next run.
 */

const OWNER = 'AdamParkerRank4AI';
const REPO = 'rank4ai-dashboard';
const FILE_PATH = 'src/data/clients.json';
const DEPLOY_HOOK_ID = '0064972e-334f-4b49-8348-e3f666f13c04';
const VALID = ['live', 'prelaunch', 'paused', 'needs'];

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  });
}
function b64encode(s) { return btoa(unescape(encodeURIComponent(s))); }
function b64decode(s) { return decodeURIComponent(escape(atob(s))); }

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
    return json({ ok: false, error: 'Server not configured' }, 500);
  }
  if ((request.headers.get('Authorization') || '') !== `Bearer ${env.EDIT_SECRET}`) {
    return json({ ok: false, error: 'Unauthorized' }, 401);
  }

  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: 'Invalid JSON' }, 400); }

  const { clientId, status } = body;
  if (!clientId || !VALID.includes(status)) {
    return json({ ok: false, error: `Missing clientId or invalid status (${VALID.join('|')})` }, 400);
  }

  const ghHeaders = {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    Accept: 'application/vnd.github+json',
    'User-Agent': 'rank4ai-dashboard-status-toggle',
  };
  const getR = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/contents/${FILE_PATH}?ref=main`, { headers: ghHeaders });
  if (!getR.ok) return json({ ok: false, error: `Failed to fetch clients.json: ${getR.status}` }, 500);
  const file = await getR.json();
  let data;
  try { data = JSON.parse(b64decode(file.content.replace(/\n/g, ''))); } catch (e) {
    return json({ ok: false, error: `Parse clients.json: ${e.message}` }, 500);
  }

  const client = data.find((c) => c.id === clientId);
  if (!client) return json({ ok: false, error: `Unknown client: ${clientId}` }, 404);

  if (client.siteStatus === status) {
    return json({ ok: true, noChange: true, clientId, status });
  }
  client.siteStatus = status;
  // Keep pre_launch in sync so legacy readers stay consistent.
  client.pre_launch = status === 'prelaunch';

  const patched = JSON.stringify(data, null, 2) + '\n';
  const putR = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/contents/${FILE_PATH}`, {
    method: 'PUT',
    headers: { ...ghHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: `Dashboard: set ${clientId} status → ${status}`,
      content: b64encode(patched),
      sha: file.sha,
      branch: 'main',
      committer: { name: 'Rank4AI Dashboard', email: 'dashboard@rank4ai.co.uk' },
    }),
  });
  if (!putR.ok) return json({ ok: false, error: `GitHub PUT failed: ${putR.status}` }, 500);
  const putData = await putR.json();

  let deployId = null;
  try {
    const hookR = await fetch(`https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/${DEPLOY_HOOK_ID}`, { method: 'POST' });
    const hookData = await hookR.json();
    deployId = hookData?.result?.id || null;
  } catch {}

  return json({
    ok: true,
    clientId,
    status,
    commit: putData.commit?.sha,
    commitUrl: putData.commit?.html_url,
    deployId,
    note: 'Dashboard rebuild reflects the change in 1-2 min. Fetchers skip non-live sites on their next run.',
  });
}
