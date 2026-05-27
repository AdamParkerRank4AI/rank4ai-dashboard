/**
 * Delete-lead API — permanently removes a single lead row from its Supabase table.
 *
 * POST /api/delete-lead
 * Header: Authorization: Bearer <EDIT_SECRET>
 * Body:   { site_id, id }
 *
 * Env vars (set in Cloudflare Pages production settings for rank4ai-dashboard):
 *   EDIT_SECRET           — same bearer token as the other editor endpoints
 *   SUPABASE_SERVICE_KEY  — Supabase service_role key (bypasses RLS so DELETE works;
 *                           the lead tables are insert-only for anon). Required.
 *
 * If SUPABASE_SERVICE_KEY isn't set the endpoint returns a clear "not wired"
 * message rather than failing silently.
 */

const SUPABASE_URL = 'https://tsscscjcxbzhicuuhter.supabase.co';

// dashboard site_id -> Supabase table (mirror of scripts/fetch_leads.py SITE_TABLES)
const SITE_TABLES = {
  'market-invoice': 'market_invoice_leads',
  'bestbusinessloans': 'bestbusinessloans_leads',
  'fundbiz': 'fundbiz_leads',
  'cardmachines': 'merchanthq_leads',
  'kartapay': 'kartapay_leads',
  'peptideclear': 'peptideclear_leads',
};

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  });

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.EDIT_SECRET) {
    return json({ error: 'Endpoint not wired: EDIT_SECRET not set on this project.' }, 503);
  }
  if ((request.headers.get('Authorization') || '') !== `Bearer ${env.EDIT_SECRET}`) {
    return json({ error: 'Unauthorized' }, 401);
  }
  if (!env.SUPABASE_SERVICE_KEY) {
    return json({ error: 'Endpoint not wired: SUPABASE_SERVICE_KEY not set on this project.' }, 503);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, 400);
  }

  const siteId = (body.site_id || '').trim();
  const id = (body.id ?? '').toString().trim();
  const table = SITE_TABLES[siteId];
  if (!table) return json({ error: `Unknown site_id: ${siteId}` }, 400);
  if (!id) return json({ error: 'Missing lead id' }, 400);

  const url = `${SUPABASE_URL}/rest/v1/${table}?id=eq.${encodeURIComponent(id)}`;
  const res = await fetch(url, {
    method: 'DELETE',
    headers: {
      apikey: env.SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
      Prefer: 'return=representation',
    },
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    return json({ error: `Supabase delete failed (${res.status}): ${detail.slice(0, 300)}` }, 502);
  }

  let deleted = [];
  try {
    deleted = await res.json();
  } catch {}
  return json({ ok: true, table, id, deleted: Array.isArray(deleted) ? deleted.length : null });
}
