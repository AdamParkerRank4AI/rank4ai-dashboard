/**
 * Update a client's visible sections in src/data/clients.json.
 *
 * POST /api/update-client-sections
 * Header: Authorization: Bearer <EDIT_SECRET>
 * Body:  { clientId, sectionId, enabled }
 *   clientId:  client entry id in clients.json
 *   sectionId: section id to toggle
 *   enabled:   true = add to clientViewSections, false = remove
 *
 * Writes back to the rank4ai-dashboard repo on main, fires the deploy hook.
 */

const OWNER = 'AdamParkerRank4AI';
const REPO = 'rank4ai-dashboard';
const FILE_PATH = 'src/data/clients.json';
const DEPLOY_HOOK_ID = '0064972e-334f-4b49-8348-e3f666f13c04';

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

  const { clientId, sectionId, enabled } = body;
  if (!clientId || !sectionId || typeof enabled !== 'boolean') {
    return json({ ok: false, error: 'Missing clientId, sectionId, or enabled' }, 400);
  }

  // Fetch current file
  const ghHeaders = {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    Accept: 'application/vnd.github+json',
    'User-Agent': 'rank4ai-dashboard-client-toggle',
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

  client.clientViewSections = client.clientViewSections || [];
  const had = client.clientViewSections.includes(sectionId);
  if (enabled && !had) client.clientViewSections.push(sectionId);
  if (!enabled && had) client.clientViewSections = client.clientViewSections.filter((s) => s !== sectionId);

  if (enabled === had) {
    return json({ ok: true, noChange: true, clientId, sectionId, enabled, sections: client.clientViewSections });
  }

  const patched = JSON.stringify(data, null, 2) + '\n';
  const putR = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/contents/${FILE_PATH}`, {
    method: 'PUT',
    headers: { ...ghHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: `Dashboard: ${enabled ? 'enable' : 'disable'} ${sectionId} for ${clientId} client view`,
      content: b64encode(patched),
      sha: file.sha,
      branch: 'main',
      committer: { name: 'Rank4AI Dashboard', email: 'dashboard@rank4ai.co.uk' },
    }),
  });
  if (!putR.ok) return json({ ok: false, error: `GitHub PUT failed: ${putR.status}` }, 500);
  const putData = await putR.json();

  // Fire deploy hook so the client view reflects the change within 1-2 minutes
  let deployId = null;
  try {
    const hookR = await fetch(`https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/${DEPLOY_HOOK_ID}`, { method: 'POST' });
    const hookData = await hookR.json();
    deployId = hookData?.result?.id || null;
  } catch {}

  return json({
    ok: true,
    clientId,
    sectionId,
    enabled,
    sections: client.clientViewSections,
    commit: putData.commit?.sha,
    commitUrl: putData.commit?.html_url,
    deployId,
    note: 'Dashboard rebuild will reflect the toggle within 1-2 minutes.',
  });
}
