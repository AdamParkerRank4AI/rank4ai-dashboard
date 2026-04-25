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

      const siteMap = {
        'rank4ai': ['rank4ai', 'rank4ai.co.uk', 'www.rank4ai.co.uk'],
        'market-invoice': ['market-invoice', 'marketinvoice.co.uk', 'www.marketinvoice.co.uk'],
        'seocompare': ['seocompare', 'seocompare.co.uk', 'www.seocompare.co.uk'],
      };

      for (const [siteId, keys] of Object.entries(siteMap)) {
        let merged = { date: today, humans: 0, bots: 0, by_type: {}, by_name: {} };
        for (const key of keys) {
          const data = await env.TRACKER_KV.get(`summary:${key}:${today}`, 'json');
          if (data) {
            merged.humans += data.humans || 0;
            merged.bots += data.bots || 0;
            for (const [t, c] of Object.entries(data.by_type || {})) merged.by_type[t] = (merged.by_type[t] || 0) + c;
            for (const [n, c] of Object.entries(data.by_name || {})) merged.by_name[n] = (merged.by_name[n] || 0) + c;
          }
          // Also check bots: prefix
          const botData = await env.TRACKER_KV.get(`bots:${key}:${today}`, 'json');
          if (botData) {
            merged.bots += botData.total || 0;
            for (const [t, c] of Object.entries(botData.by_type || {})) merged.by_type[t] = (merged.by_type[t] || 0) + c;
            for (const [n, c] of Object.entries(botData.by_name || {})) merged.by_name[n] = (merged.by_name[n] || 0) + c;
          }
        }
        overview[siteId] = merged;
      }

      return new Response(JSON.stringify(overview), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // API endpoint — server-side bot hits (from bot-logger Worker route)
    if (url.pathname === '/api/bot-hits') {
      const siteId = url.searchParams.get('site') || 'rank4ai';
      const days = parseInt(url.searchParams.get('days') || '30');
      const results = [];

      for (let i = 0; i < days; i++) {
        const date = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
        const data = await env.TRACKER_KV.get(`bots:${siteId}:${date}`, 'json');
        if (data) results.push(data);
      }

      return new Response(JSON.stringify({
        site: siteId,
        days: results.length,
        data: results.reverse(),
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // API endpoint — all sites bot hits today
    if (url.pathname === '/api/bot-overview') {
      const today = new Date().toISOString().slice(0, 10);
      const overview = {};

      for (const site of ['rank4ai', 'market-invoice', 'seocompare']) {
        const data = await env.TRACKER_KV.get(`bots:${site}:${today}`, 'json');
        overview[site] = data || { date: today, site, total: 0, by_type: {}, by_name: {} };
      }

      return new Response(JSON.stringify(overview), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Citation test endpoint — test a single query against AI models
    if (url.pathname === '/test-citation' && request.method === 'POST') {
      try {
        const body = await request.json();
        const query = body.query;
        const brand = body.brand;
        const domain = body.domain;
        const promptId = body.id || '';

        if (!query || !brand) {
          return new Response(JSON.stringify({ error: 'query and brand required' }), {
            status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const results = {};

        // Test Claude
        if (env.ANTHROPIC_API_KEY) {
          try {
            const resp = await fetch('https://api.anthropic.com/v1/messages', {
              method: 'POST',
              headers: {
                'x-api-key': env.ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
              },
              body: JSON.stringify({
                model: 'claude-sonnet-4-20250514',
                max_tokens: 1024,
                messages: [{ role: 'user', content: query }],
              }),
            });
            if (resp.ok) {
              const data = await resp.json();
              const text = data.content?.[0]?.text || '';
              const textLower = text.toLowerCase();
              results.claude = {
                cited: textLower.includes(brand.toLowerCase()) || textLower.includes((domain || '').toLowerCase()),
                preview: text.slice(0, 300),
              };
            }
          } catch (e) {
            results.claude = { error: e.message };
          }
        }

        // Test ChatGPT
        if (env.OPENAI_API_KEY) {
          try {
            const resp = await fetch('https://api.openai.com/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                model: 'gpt-4o-mini',
                max_tokens: 1024,
                messages: [{ role: 'user', content: query }],
              }),
            });
            if (resp.ok) {
              const data = await resp.json();
              const text = data.choices?.[0]?.message?.content || '';
              const textLower = text.toLowerCase();
              results.chatgpt = {
                cited: textLower.includes(brand.toLowerCase()) || textLower.includes((domain || '').toLowerCase()),
                preview: text.slice(0, 300),
              };
            }
          } catch (e) {
            results.chatgpt = { error: e.message };
          }
        }

        // Test Gemini
        if (env.GEMINI_API_KEY) {
          try {
            const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${env.GEMINI_API_KEY}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                contents: [{ parts: [{ text: query }] }],
                generationConfig: { maxOutputTokens: 1024 },
              }),
            });
            if (resp.ok) {
              const data = await resp.json();
              const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
              const textLower = text.toLowerCase();
              results.gemini = {
                cited: textLower.includes(brand.toLowerCase()) || textLower.includes((domain || '').toLowerCase()),
                preview: text.slice(0, 300),
              };
            }
          } catch (e) {
            results.gemini = { error: e.message };
          }
        }

        // Store result in KV
        const today = new Date().toISOString().slice(0, 10);
        const resultKey = `citation:${promptId || query.slice(0, 50)}:${today}`;
        const resultData = {
          query, brand, domain, promptId,
          tested_at: new Date().toISOString(),
          results,
        };
        await env.TRACKER_KV.put(resultKey, JSON.stringify(resultData), {
          expirationTtl: 60 * 60 * 24 * 90,
        });

        return new Response(JSON.stringify(resultData), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });

      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Get citation history for a prompt
    if (url.pathname === '/api/citation-history') {
      const promptId = url.searchParams.get('id') || '';
      const days = parseInt(url.searchParams.get('days') || '30');
      const history = [];

      for (let i = 0; i < days; i++) {
        const date = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10);
        const data = await env.TRACKER_KV.get(`citation:${promptId}:${date}`, 'json');
        if (data) history.push(data);
      }

      return new Response(JSON.stringify({ id: promptId, history: history.reverse() }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // ========== SITE MANAGER ENDPOINTS ==========

    // Get file content from GitHub
    if (url.pathname === '/api/file' && request.method === 'GET') {
      const repo = url.searchParams.get('repo');
      const path = url.searchParams.get('path');
      const branch = url.searchParams.get('branch') || 'main';

      if (!repo || !path || !env.GITHUB_TOKEN) {
        return new Response(JSON.stringify({ error: 'repo, path required' }), {
          status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      try {
        const resp = await fetch(`https://api.github.com/repos/${repo}/contents/${path}?ref=${branch}`, {
          headers: {
            'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Rank4AI-Dashboard',
          },
        });

        if (!resp.ok) {
          return new Response(JSON.stringify({ error: `GitHub: ${resp.status}` }), {
            status: resp.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const data = await resp.json();
        const content = atob(data.content);

        return new Response(JSON.stringify({
          path: data.path,
          sha: data.sha,
          content,
          size: data.size,
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Update file on GitHub
    if (url.pathname === '/api/file' && request.method === 'PUT') {
      try {
        const body = await request.json();
        const { repo, path, content, sha, message, branch } = body;

        if (!repo || !path || !content || !sha || !env.GITHUB_TOKEN) {
          return new Response(JSON.stringify({ error: 'repo, path, content, sha required' }), {
            status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const resp = await fetch(`https://api.github.com/repos/${repo}/contents/${path}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Rank4AI-Dashboard',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message || `Update ${path} via dashboard`,
            content: btoa(unescape(encodeURIComponent(content))),
            sha,
            branch: branch || 'main',
          }),
        });

        if (!resp.ok) {
          const err = await resp.text();
          return new Response(JSON.stringify({ error: `GitHub: ${resp.status} ${err.slice(0, 200)}` }), {
            status: resp.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const data = await resp.json();
        return new Response(JSON.stringify({ ok: true, sha: data.content?.sha }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Create new file on GitHub
    if (url.pathname === '/api/file' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { repo, path, content, message, branch } = body;

        if (!repo || !path || !content || !env.GITHUB_TOKEN) {
          return new Response(JSON.stringify({ error: 'repo, path, content required' }), {
            status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const resp = await fetch(`https://api.github.com/repos/${repo}/contents/${path}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Rank4AI-Dashboard',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message || `Create ${path} via dashboard`,
            content: btoa(unescape(encodeURIComponent(content))),
            branch: branch || 'main',
          }),
        });

        if (!resp.ok) {
          const err = await resp.text();
          return new Response(JSON.stringify({ error: `GitHub: ${resp.status} ${err.slice(0, 200)}` }), {
            status: resp.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        return new Response(JSON.stringify({ ok: true, path }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Delete file on GitHub
    if (url.pathname === '/api/file' && request.method === 'DELETE') {
      try {
        const body = await request.json();
        const { repo, path, sha, message, branch } = body;

        if (!repo || !path || !sha || !env.GITHUB_TOKEN) {
          return new Response(JSON.stringify({ error: 'repo, path, sha required' }), {
            status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const resp = await fetch(`https://api.github.com/repos/${repo}/contents/${path}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Rank4AI-Dashboard',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message || `Delete ${path} via dashboard`,
            sha,
            branch: branch || 'main',
          }),
        });

        if (!resp.ok) {
          const err = await resp.text();
          return new Response(JSON.stringify({ error: `GitHub: ${resp.status}` }), {
            status: resp.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        return new Response(JSON.stringify({ ok: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // List files in a directory on GitHub
    if (url.pathname === '/api/files' && request.method === 'GET') {
      const repo = url.searchParams.get('repo');
      const path = url.searchParams.get('path') || '';
      const branch = url.searchParams.get('branch') || 'main';

      if (!repo || !env.GITHUB_TOKEN) {
        return new Response(JSON.stringify({ error: 'repo required' }), {
          status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      try {
        const resp = await fetch(`https://api.github.com/repos/${repo}/contents/${path}?ref=${branch}`, {
          headers: {
            'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Rank4AI-Dashboard',
          },
        });

        if (!resp.ok) {
          return new Response(JSON.stringify({ error: `GitHub: ${resp.status}` }), {
            status: resp.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }

        const data = await resp.json();
        const files = Array.isArray(data) ? data.map(f => ({
          name: f.name,
          path: f.path,
          type: f.type,
          size: f.size,
        })) : [];

        return new Response(JSON.stringify({ files }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Default — info page
    return new Response(JSON.stringify({
      name: 'Rank4AI Visitor & Bot Tracker',
      endpoints: {
        'POST /track': 'Log a visit (send {site, path, ua, hostname, referer})',
        'POST /test-citation': 'Test a query against AI models (send {query, brand, domain, id})',
        'GET /api/summary?site=rank4ai&days=30': 'Get daily summaries',
        'GET /api/bots?site=rank4ai': 'Get today\'s bot breakdown',
        'GET /api/overview': 'Get all sites overview',
        'GET /api/citation-history?id=prompt-id&days=30': 'Get citation test history',
      },
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};
