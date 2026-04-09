/**
 * Rank4AI Visitor & Bot Tracker
 * Cloudflare Worker that logs every visit — splits into humans vs bots/crawlers.
 * Stores data in Cloudflare KV.
 *
 * Deploy: npx wrangler deploy --name rank4ai-tracker
 * KV Namespace: TRACKER_KV (create first)
 */

// Known bot patterns
const BOT_PATTERNS = [
  // AI Crawlers
  { pattern: /GPTBot/i, name: 'GPTBot', type: 'ai', owner: 'OpenAI (ChatGPT)' },
  { pattern: /ChatGPT-User/i, name: 'ChatGPT-User', type: 'ai', owner: 'OpenAI' },
  { pattern: /ClaudeBot/i, name: 'ClaudeBot', type: 'ai', owner: 'Anthropic (Claude)' },
  { pattern: /Claude-Web/i, name: 'Claude-Web', type: 'ai', owner: 'Anthropic' },
  { pattern: /anthropic-ai/i, name: 'Anthropic-AI', type: 'ai', owner: 'Anthropic' },
  { pattern: /PerplexityBot/i, name: 'PerplexityBot', type: 'ai', owner: 'Perplexity' },
  { pattern: /Google-Extended/i, name: 'Google-Extended', type: 'ai', owner: 'Google (Gemini)' },
  { pattern: /GoogleOther/i, name: 'GoogleOther', type: 'ai', owner: 'Google (AI/ML)' },
  { pattern: /cohere-ai/i, name: 'Cohere-AI', type: 'ai', owner: 'Cohere' },
  { pattern: /Bytespider/i, name: 'Bytespider', type: 'ai', owner: 'ByteDance (TikTok)' },
  { pattern: /CCBot/i, name: 'CCBot', type: 'ai', owner: 'Common Crawl' },
  { pattern: /meta-externalagent/i, name: 'Meta-ExternalAgent', type: 'ai', owner: 'Meta AI' },

  // Search Engine Crawlers
  { pattern: /Googlebot/i, name: 'Googlebot', type: 'search', owner: 'Google' },
  { pattern: /Googlebot-Image/i, name: 'Googlebot-Image', type: 'search', owner: 'Google' },
  { pattern: /Googlebot-Video/i, name: 'Googlebot-Video', type: 'search', owner: 'Google' },
  { pattern: /AdsBot-Google/i, name: 'AdsBot-Google', type: 'search', owner: 'Google Ads' },
  { pattern: /Mediapartners-Google/i, name: 'Mediapartners', type: 'search', owner: 'Google AdSense' },
  { pattern: /bingbot/i, name: 'Bingbot', type: 'search', owner: 'Microsoft Bing' },
  { pattern: /msnbot/i, name: 'MSNBot', type: 'search', owner: 'Microsoft' },
  { pattern: /YandexBot/i, name: 'YandexBot', type: 'search', owner: 'Yandex' },
  { pattern: /Baiduspider/i, name: 'Baiduspider', type: 'search', owner: 'Baidu' },
  { pattern: /DuckDuckBot/i, name: 'DuckDuckBot', type: 'search', owner: 'DuckDuckGo' },
  { pattern: /Applebot/i, name: 'Applebot', type: 'search', owner: 'Apple (Siri/Spotlight)' },

  // Social Media Crawlers
  { pattern: /facebookexternalhit/i, name: 'Facebook', type: 'social', owner: 'Meta' },
  { pattern: /Twitterbot/i, name: 'Twitterbot', type: 'social', owner: 'X/Twitter' },
  { pattern: /LinkedInBot/i, name: 'LinkedInBot', type: 'social', owner: 'LinkedIn' },
  { pattern: /Pinterest/i, name: 'Pinterest', type: 'social', owner: 'Pinterest' },
  { pattern: /Slackbot/i, name: 'Slackbot', type: 'social', owner: 'Slack' },
  { pattern: /TelegramBot/i, name: 'TelegramBot', type: 'social', owner: 'Telegram' },
  { pattern: /WhatsApp/i, name: 'WhatsApp', type: 'social', owner: 'Meta' },

  // SEO & Monitoring
  { pattern: /AhrefsBot/i, name: 'AhrefsBot', type: 'seo', owner: 'Ahrefs' },
  { pattern: /SemrushBot/i, name: 'SemrushBot', type: 'seo', owner: 'Semrush' },
  { pattern: /MJ12bot/i, name: 'MajesticBot', type: 'seo', owner: 'Majestic' },
  { pattern: /DotBot/i, name: 'DotBot', type: 'seo', owner: 'Moz' },
  { pattern: /rogerbot/i, name: 'RogerBot', type: 'seo', owner: 'Moz' },
  { pattern: /ScreamingFrog/i, name: 'ScreamingFrog', type: 'seo', owner: 'Screaming Frog' },
  { pattern: /UptimeRobot/i, name: 'UptimeRobot', type: 'monitor', owner: 'UptimeRobot' },
  { pattern: /Pingdom/i, name: 'Pingdom', type: 'monitor', owner: 'Pingdom' },
  { pattern: /StatusCake/i, name: 'StatusCake', type: 'monitor', owner: 'StatusCake' },

  // Generic bot patterns
  { pattern: /bot\b/i, name: 'Unknown Bot', type: 'other', owner: 'Unknown' },
  { pattern: /crawler/i, name: 'Unknown Crawler', type: 'other', owner: 'Unknown' },
  { pattern: /spider/i, name: 'Unknown Spider', type: 'other', owner: 'Unknown' },
  { pattern: /headless/i, name: 'Headless Browser', type: 'other', owner: 'Unknown' },
  { pattern: /puppeteer/i, name: 'Puppeteer', type: 'other', owner: 'Unknown' },
  { pattern: /playwright/i, name: 'Playwright', type: 'other', owner: 'Unknown' },
];

function identifyVisitor(userAgent) {
  if (!userAgent) return { isBot: true, name: 'No User Agent', type: 'other', owner: 'Unknown' };

  for (const bot of BOT_PATTERNS) {
    if (bot.pattern.test(userAgent)) {
      return { isBot: true, name: bot.name, type: bot.type, owner: bot.owner };
    }
  }

  return { isBot: false, name: 'Human', type: 'human', owner: null };
}

function getSiteId(hostname) {
  if (hostname.includes('rank4ai')) return 'rank4ai';
  if (hostname.includes('marketinvoice')) return 'market-invoice';
  if (hostname.includes('seocompare')) return 'seocompare';
  return hostname;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Track endpoint — receives visitor data from sites
    if (url.pathname === '/track') {
      try {
        const body = await request.json();
        const userAgent = body.ua || request.headers.get('user-agent') || '';
        const visitor = identifyVisitor(userAgent);
        const siteId = body.site || getSiteId(body.hostname || '');
        const today = new Date().toISOString().slice(0, 10);
        const hour = new Date().getUTCHours();

        const entry = {
          ts: Date.now(),
          site: siteId,
          path: body.path || '/',
          ua: userAgent.slice(0, 200),
          ...visitor,
          ip_country: request.headers.get('cf-ipcountry') || '',
          referer: body.referer || '',
        };

        // Store in KV — daily log per site
        const key = `visits:${siteId}:${today}`;
        const existing = await env.TRACKER_KV.get(key, 'json') || [];
        existing.push(entry);

        // Keep last 5000 entries per day per site
        const trimmed = existing.slice(-5000);
        await env.TRACKER_KV.put(key, JSON.stringify(trimmed), {
          expirationTtl: 60 * 60 * 24 * 90, // Keep 90 days
        });

        // Update daily summary
        const summaryKey = `summary:${siteId}:${today}`;
        const summary = await env.TRACKER_KV.get(summaryKey, 'json') || {
          date: today, site: siteId,
          humans: 0, bots: 0,
          by_type: {}, by_name: {}, by_hour: {},
          top_paths: {}, countries: {},
        };

        if (visitor.isBot) {
          summary.bots++;
          summary.by_type[visitor.type] = (summary.by_type[visitor.type] || 0) + 1;
          summary.by_name[visitor.name] = (summary.by_name[visitor.name] || 0) + 1;
        } else {
          summary.humans++;
        }
        summary.by_hour[hour] = (summary.by_hour[hour] || 0) + 1;
        summary.top_paths[entry.path] = (summary.top_paths[entry.path] || 0) + 1;
        summary.countries[entry.ip_country] = (summary.countries[entry.ip_country] || 0) + 1;

        await env.TRACKER_KV.put(summaryKey, JSON.stringify(summary), {
          expirationTtl: 60 * 60 * 24 * 90,
        });

        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // API endpoint — get data for dashboard
    if (url.pathname === '/api/summary') {
      const siteId = url.searchParams.get('site') || 'rank4ai';
      const days = parseInt(url.searchParams.get('days') || '30');
      const summaries = [];

      for (let i = 0; i < days; i++) {
        const date = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
        const data = await env.TRACKER_KV.get(`summary:${siteId}:${date}`, 'json');
        if (data) summaries.push(data);
      }

      return new Response(JSON.stringify({
        site: siteId,
        days: summaries.length,
        summaries: summaries.reverse(),
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // API endpoint — get today's bot breakdown
    if (url.pathname === '/api/bots') {
      const siteId = url.searchParams.get('site') || 'rank4ai';
      const today = new Date().toISOString().slice(0, 10);
      const summary = await env.TRACKER_KV.get(`summary:${siteId}:${today}`, 'json');

      return new Response(JSON.stringify(summary || { date: today, humans: 0, bots: 0 }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // API endpoint — get all sites overview
    if (url.pathname === '/api/overview') {
      const today = new Date().toISOString().slice(0, 10);
      const overview = {};

      for (const site of ['rank4ai', 'market-invoice', 'seocompare']) {
        const data = await env.TRACKER_KV.get(`summary:${site}:${today}`, 'json');
        overview[site] = data || { date: today, humans: 0, bots: 0, by_type: {}, by_name: {} };
      }

      return new Response(JSON.stringify(overview), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Default — info page
    return new Response(JSON.stringify({
      name: 'Rank4AI Visitor & Bot Tracker',
      endpoints: {
        'POST /track': 'Log a visit (send {site, path, ua, hostname, referer})',
        'GET /api/summary?site=rank4ai&days=30': 'Get daily summaries',
        'GET /api/bots?site=rank4ai': 'Get today\'s bot breakdown',
        'GET /api/overview': 'Get all sites overview',
      },
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};
