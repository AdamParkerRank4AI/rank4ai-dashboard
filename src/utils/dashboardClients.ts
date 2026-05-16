import allClients from '../data/clients.json';

export const DASHBOARD_ID: string = (process.env.DASHBOARD || 'current').toLowerCase();

export function clientBelongs(c: any): boolean {
  const owner = (c?.dashboard || 'current').toLowerCase();
  return owner === DASHBOARD_ID;
}

const filtered = (allClients as any[]).filter(clientBelongs);

export default filtered;
export { allClients };
