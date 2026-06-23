// Single shared derivation of a site's lifecycle status, so the overview and
// the sidebar can't drift apart. clients.json `siteStatus` is the SOLE source
// of truth (one of: live | prelaunch | needs | paused | staging).
//
// NOTE (19 Jun 2026): the legacy `pre_launch` boolean is deliberately NOT read
// here any more. It used to be an OR-fallback, which caused silent drift — a
// site could be set live via siteStatus but still show PRE-LAUNCH because an
// old pre_launch:true was left behind (the Her Vitals bug). Edit ONLY siteStatus.
// All 23 clients carry siteStatus, so there is nothing to fall back to.

export type SiteStatus = 'live' | 'prelaunch' | 'needs' | 'paused' | 'staging';

export function statusOf(c: any): SiteStatus {
  if (c?.staging) return 'staging';
  if (c?.siteStatus === 'paused') return 'paused';
  if (c?.siteStatus === 'needs') return 'needs';
  if (c?.siteStatus === 'prelaunch') return 'prelaunch';
  if (c?.siteStatus === 'staging') return 'staging';
  return 'live';
}

// Display ordering: live first, then the not-yet / parked states.
export const STATUS_RANK: Record<SiteStatus, number> = {
  live: 0, prelaunch: 1, needs: 2, paused: 3, staging: 4,
};

export const STATUS_PILL: Record<SiteStatus, string> = {
  live: 'bg-emerald-900/40 text-emerald-400',
  prelaunch: 'bg-blue-900/40 text-blue-300',
  needs: 'bg-amber-900/40 text-amber-300',
  paused: 'bg-gray-800 text-gray-400',
  staging: 'bg-yellow-900/50 text-yellow-400',
};

export const STATUS_LABEL: Record<SiteStatus, string> = {
  live: 'Live', prelaunch: 'Pre-launch', needs: 'Needs setup', paused: 'Paused', staging: 'Staging',
};
