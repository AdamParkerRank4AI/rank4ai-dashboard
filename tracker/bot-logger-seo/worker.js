/**
 * Bot Logger — SEO Compare
 * Cloudflare Worker Route for seocompare.co.uk
 * Logs bot visits to KV, passes request through to Pages.
 */

const BOT_PATTERNS = [
  { pattern: /GPTBot/i, name: 'GPTBot', type: 'ai' },
  { pattern: /ChatGPT-User/i, name: 'ChatGPT-User', type: 'ai' },
  { pattern: /ClaudeBot/i, name: 'ClaudeBot', type: 'ai' },
  { pattern: /Claude-Web/i, name: 'Claude-Web', type: 'ai' },
  { pattern: /anthropic-ai/i, name: 'Anthropic-AI', type: 'ai' },
  { pattern: /PerplexityBot/i, name: 'PerplexityBot', type: 'ai' },
  { pattern: /Google-Extended/i, name: 'Google-Extended', type: 'ai' },
  { pattern: /GoogleOther/i, name: 'GoogleOther', type: 'ai' },
  { pattern: /cohere-ai/i, name: 'Cohere-AI', type: 'ai' },
  { pattern: /Bytespider/i, name: 'Bytespider', type: 'ai' },
  { pattern: /CCBot/i, name: 'CCBot', type: 'ai' },
  { pattern: /meta-externalagent/i, name: 'Meta-Agent', type: 'ai' },
  { pattern: /Googlebot/i, name: 'Googlebot', type: 'search' },
  { pattern: /bingbot/i, name: 'Bingbot', type: 'search' },
  { pattern: /YandexBot/i, name: 'YandexBot', type: 'search' },
  { pattern: /DuckDuckBot/i, name: 'DuckDuckBot', type: 'search' },
  { pattern: /Applebot/i, name: 'Applebot', type: 'search' },
  { pattern: /AdsBot-Google/i, name: 'AdsBot-Google', type: 'search' },
  { pattern: /facebookexternalhit/i, name: 'Facebook', type: 'social' },
  { pattern: /Twitterbot/i, name: 'Twitterbot', type: 'social' },
  { pattern: /LinkedInBot/i, name: 'LinkedInBot', type: 'social' },
  { pattern: /WhatsApp/i, name: 'WhatsApp', type: 'social' },
  { pattern: /Slackbot/i, name: 'Slackbot', type: 'social' },
  { pattern: /AhrefsBot/i, name: 'AhrefsBot', type: 'seo' },
  { pattern: /SemrushBot/i, name: 'SemrushBot', type: 'seo' },
  { pattern: /MJ12bot/i, name: 'MajesticBot', type: 'seo' },
  { pattern: /ScreamingFrog/i, name: 'ScreamingFrog', type: 'seo' },
  { pattern: /UptimeRobot/i, name: 'UptimeRobot', type: 'monitor' },
  { pattern: /bot\b/i, name: 'Other Bot', type: 'other' },
  { pattern: /crawler/i, name: 'Other Crawler', type: 'other' },
  { pattern: /spider/i, name: 'Other Spider', type: 'other' },
];

function identifyBot(ua) {
  if (!ua) return null;
  for (const b of BOT_PATTERNS) {
    if (b.pattern.test(ua)) return b;
  }
  return null;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // API endpoint for dashboard to pull data
    if (url.pathname === '/_bot-api/hits') {
      const days = parseInt(url.searchParams.get('days') || '30');
      const results = [];
      for (let i = 0; i < days; i++) {
        const date = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
        const data = await env.BOT_KV.get(`bots:seocompare:${date}`, 'json');
        if (data) results.push(data);
      }
      return new Response(JSON.stringify({ site: 'seocompare', days: results.length, data: results.reverse() }), {
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    const ua = request.headers.get('user-agent') || '';
    const bot = identifyBot(ua);

    if (bot) {
      ctx.waitUntil(logBotVisit(env, bot, url.pathname, request));
    }

    return fetch(request);
  }
};

async function logBotVisit(env, bot, path, request) {
  try {
    const siteId = 'seocompare';
    const today = new Date().toISOString().slice(0, 10);
    const hour = new Date().getUTCHours();

    const summaryKey = `bots:${siteId}:${today}`;
    const summary = await env.BOT_KV.get(summaryKey, 'json') || {
      date: today, site: siteId, total: 0,
      by_type: {}, by_name: {}, by_hour: {}, top_paths: {},
    };

    summary.total++;
    summary.by_type[bot.type] = (summary.by_type[bot.type] || 0) + 1;
    summary.by_name[bot.name] = (summary.by_name[bot.name] || 0) + 1;
    summary.by_hour[hour] = (summary.by_hour[hour] || 0) + 1;

    const pathKey = path.slice(0, 100);
    summary.top_paths[pathKey] = (summary.top_paths[pathKey] || 0) + 1;
    if (Object.keys(summary.top_paths).length > 50) {
      const sorted = Object.entries(summary.top_paths).sort((a, b) => b[1] - a[1]).slice(0, 50);
      summary.top_paths = Object.fromEntries(sorted);
    }

    await env.BOT_KV.put(summaryKey, JSON.stringify(summary), {
      expirationTtl: 60 * 60 * 24 * 90,
    });

    const logKey = `botlog:${siteId}:${today}`;
    const log = await env.BOT_KV.get(logKey, 'json') || [];
    log.push({
      ts: Date.now(), name: bot.name, type: bot.type,
      path: path.slice(0, 100),
      country: request.headers.get('cf-ipcountry') || '',
    });
    await env.BOT_KV.put(logKey, JSON.stringify(log.slice(-200)), {
      expirationTtl: 60 * 60 * 24 * 90,
    });
  } catch (e) {}
}
