/**
 * Cloudflare Pages Function: forwards an audit request to the Mac-hosted
 * audit-server.js via the rank4ai-audit Cloudflare Tunnel.
 *
 * Called by src/pages/run-audit.astro. Keeps the shared AUDIT_SECRET
 * server-side so the browser never sees it.
 *
 * Env vars (set in Cloudflare Pages -> Settings -> Environment variables):
 *   AUDIT_SECRET   shared secret, must match what's in the Mac's .env
 *
 * Optional override:
 *   AUDIT_TUNNEL_URL  full URL of the tunnel (defaults to
 *                     https://audit.rank4ai.co.uk/audit)
 */

export async function onRequestPost({ request, env }) {
  const secret = env.AUDIT_SECRET;
  if (!secret) {
    return json({ error: "Server misconfigured: AUDIT_SECRET env var not set in Cloudflare Pages" }, 500);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  const url = (body.url || "").trim();
  const version = body.version === "v2" ? "v2" : "v1";
  const leadName = (body.lead_name || "").trim();
  const leadId = (body.lead_id || "").trim();

  if (!url) {
    return json({ error: "url is required" }, 400);
  }
  if (!/^https?:\/\//i.test(url)) {
    return json({ error: "url must start with http:// or https://" }, 400);
  }

  const tunnelUrl = env.AUDIT_TUNNEL_URL || "https://audit.rank4ai.co.uk/audit";

  try {
    const upstream = await fetch(tunnelUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Audit-Secret": secret,
      },
      body: JSON.stringify({ url, version, lead_name: leadName, lead_id: leadId }),
      // Audit takes multiple minutes. Pages Functions cap at 30s compute, so
      // the connection will get cut, but the audit keeps running on the Mac
      // and emails the PDF on completion. The form uses this shape: fire
      // and forget, email arrives minutes later.
      signal: AbortSignal.timeout(25000),
    });
    const text = await upstream.text();
    // Pass through whatever audit-server returned. If we timed out on the
    // fetch (common because audits run for minutes), the Mac keeps running
    // the job and the email will still arrive.
    return new Response(text, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("Content-Type") || "application/json" },
    });
  } catch (err) {
    // Timeout is expected for long audits. Treat as "queued, email coming".
    if (err && err.name === "TimeoutError") {
      return json({
        status: "queued",
        message: "Audit is running on the Mac. PDF will arrive by email when complete (typically 3 to 10 minutes).",
        version,
        url,
      }, 202);
    }
    return json({ error: "Could not reach the audit service: " + (err?.message || String(err)) }, 502);
  }
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
