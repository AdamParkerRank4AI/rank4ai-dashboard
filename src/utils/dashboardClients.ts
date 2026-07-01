import allClients from '../data/clients.json';

export const DASHBOARD_ID: string = (process.env.DASHBOARD || 'current').toLowerCase();

export function clientBelongs(c: any): boolean {
  const owner = (c?.dashboard || 'current').toLowerCase();
  return owner === DASHBOARD_ID;
}

const filtered = (allClients as any[]).filter(clientBelongs);

export default filtered;
export { allClients };

/**
 * Some data feeds (fleet_bot_hits, bot_hits, human_traffic) key each site by a
 * DOMAIN-derived slug rather than the clients.json id, because those repos are
 * named after their domain. Two sites drift: the womenshealth repo publishes
 * hervitals.co.uk (key `hervitals`) and company-rescue publishes ltdturnaround.co.uk
 * (key `ltdturnaround`). Without this map those two get filtered out of the bot /
 * AI-citation tiles even though the data is present. Add a pair here if a new site
 * ever ships under a domain that differs from its client id.
 */
export const BOT_SITE_ALIAS: Record<string, string> = {
  hervitals: 'womenshealth',
  ltdturnaround: 'company-rescue',
};

/** Normalise a feed's per-site key to the clients.json id. */
export function toClientId(siteKey: string): string {
  return BOT_SITE_ALIAS[siteKey] || siteKey;
}
