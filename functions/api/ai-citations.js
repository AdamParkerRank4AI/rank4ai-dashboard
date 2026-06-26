/**
 * GET /api/ai-citations — LIVE AI-citation feed straight from Supabase
 * `fleet_bot_hits` (the Cloudflare Pages middleware logs every AI-bot fetch). This
 * replaces the once-daily static snapshot for the "recent live fetches" + last-24h
 * count, so AiCitationsTile is actually live instead of "as of this morning's run".
 *
 * Verification mirrors scripts/fetch_fleet_bot_hits.py: a genuine citation = an
 * ai-user fetch (ChatGPT-User / Claude-User / Perplexity-User) whose egress ASN
 * matches the operator's own or cloud network; spoofed user-agents are dropped.
 *
 * Needs env SUPABASE_SERVICE_KEY (already set for /api/delete-lead). Read-only:
 * the service key stays server-side in the Function — never exposed to the client.
 */
const SUPABASE_URL = 'https://tsscscjcxbzhicuuhter.supabase.co';

const OPS = {
  openai:     [['OPENAI'],     ['MICROSOFT', 'AZURE']],
  anthropic:  [['ANTHROPIC'],  ['AMAZON', 'AWS']],
  perplexity: [['PERPLEXITY'], ['GOOGLE', 'AMAZON', 'AWS']],
  mistral:    [['MISTRAL'],    ['OVH', 'SCALEWAY', 'AMAZON']],
};
function operator(bot, ua) {
  const s = `${bot || ''} ${ua || ''}`.toLowerCase();
  if (s.includes('perplexity')) return 'perplexity';
  if (s.includes('claude') || s.includes('anthropic')) return 'anthropic';
  if (s.includes('chatgpt') || s.includes('oai-') || s.includes('gptbot') || s.includes('openai')) return 'openai';
  if (s.includes('mistral')) return 'mistral';
  return null;
}
function verdict(bot, ua, asn) {
  const op = operator(bot, ua);
  if (!op) return ['unknown', null];
  const [own, cloud] = OPS[op];
  const o = (asn || '').toUpperCase();
  if (own.some((x) => o.includes(x))) return ['verified', op];
  if (cloud.some((x) => o.includes(x))) return ['plausible', op];
  return ['spoof?', op];
}

const headers = {
  'access-control-allow-origin': '*',
  'content-type': 'application/json',
  // 30s edge/browser cache: a live tile that's at most 30s stale, while shielding
  // Supabase from a burst of reloads.
  'cache-control': 'public, max-age=30',
};

export async function onRequestGet(context) {
  const key = context.env.SUPABASE_SERVICE_KEY;
  if (!key) {
    return new Response(JSON.stringify({ live: false, error: 'SUPABASE_SERVICE_KEY not set on this Pages project' }), { status: 200, headers });
  }
  const since = new Date(Date.now() - 30 * 864e5).toISOString();
  const cols = 'site,bot_name,bot_category,path,asn_org,user_agent,created_at';
  const url = `${SUPABASE_URL}/rest/v1/fleet_bot_hits?select=${cols}&bot_category=eq.ai-user&created_at=gte.${since}&order=created_at.desc&limit=1500`;
  let rows = [];
  try {
    const r = await fetch(url, { headers: { apikey: key, Authorization: `Bearer ${key}` } });
    rows = await r.json();
    if (!Array.isArray(rows)) rows = [];
  } catch (e) {
    return new Response(JSON.stringify({ live: false, error: String(e) }), { status: 200, headers });
  }
  const now = Date.now();
  const recent = [];
  const bySite = {};
  let total24 = 0, total1h = 0, spoofed = 0, verified = 0;
  for (const r of rows) {
    if ((r.bot_category || '') !== 'ai-user') continue;
    const [v, eng] = verdict(r.bot_name, r.user_agent, r.asn_org);
    if (v === 'spoof?') { spoofed++; continue; }
    if (v === 'unknown') continue;
    verified++;
    const site = r.site || '?';
    const age = now - Date.parse(r.created_at);
    const fresh = age <= 864e5;      // 24h
    if (fresh) total24++;
    if (age <= 3.6e6) total1h++;     // 1h
    const s = bySite[site] || (bySite[site] = { site, c24: 0, engines: {} });
    if (fresh) s.c24++;
    s.engines[eng || '?'] = (s.engines[eng || '?'] || 0) + 1;
    if (recent.length < 20) {
      recent.push({ site, path: r.path || '/', bot: r.bot_name, engine: eng, asn_org: r.asn_org, created_at: r.created_at, verdict: v, fresh: age <= 3.6e6 });
    }
  }
  const out = {
    live: true,
    generated_at: new Date().toISOString(),
    newest: recent[0]?.created_at || null,
    total_1h: total1h,
    total_24h: total24,
    verified_in_window: verified,
    spoofed,
    by_site: Object.values(bySite).sort((a, b) => b.c24 - a.c24).slice(0, 12),
    recent,
  };
  return new Response(JSON.stringify(out), { status: 200, headers });
}
