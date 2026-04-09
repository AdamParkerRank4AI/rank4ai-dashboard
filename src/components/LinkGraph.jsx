import { useState, useMemo } from 'react';

export default function LinkGraph({ pages, links }) {
  const [selectedPage, setSelectedPage] = useState(null);

  const pageMap = useMemo(() => {
    const map = {};
    (pages || []).forEach(p => {
      map[p.url] = p;
    });
    return map;
  }, [pages]);

  // Build link counts
  const linkCounts = useMemo(() => {
    const incoming = {};
    const outgoing = {};
    (links || []).forEach(l => {
      if (l.type === 'internal') {
        incoming[l.to] = (incoming[l.to] || 0) + 1;
        outgoing[l.from] = (outgoing[l.from] || 0) + 1;
      }
    });
    return { incoming, outgoing };
  }, [links]);

  // Sort pages by incoming links
  const sortedPages = useMemo(() => {
    return [...(pages || [])].sort((a, b) => {
      const aIn = linkCounts.incoming[a.url] || 0;
      const bIn = linkCounts.incoming[b.url] || 0;
      return bIn - aIn;
    });
  }, [pages, linkCounts]);

  const maxLinks = Math.max(...sortedPages.map(p => linkCounts.incoming[p.url] || 0), 1);

  // Get links for selected page
  const selectedLinks = useMemo(() => {
    if (!selectedPage) return { incoming: [], outgoing: [] };
    const incoming = (links || []).filter(l => l.to === selectedPage && l.type === 'internal').map(l => l.from);
    const outgoing = (links || []).filter(l => l.from === selectedPage && l.type === 'internal').map(l => l.to);
    return { incoming, outgoing };
  }, [selectedPage, links]);

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: selectedPage ? '1fr 1fr' : '1fr', gap: 16 }}>
        <div>
          <p style={{ color: '#9ca3af', fontSize: 11, marginBottom: 8 }}>
            Click a page to see its links. Bar size = incoming internal links.
          </p>
          <div style={{ maxHeight: 500, overflowY: 'auto' }}>
            {sortedPages.slice(0, 50).map((p, i) => {
              const inLinks = linkCounts.incoming[p.url] || 0;
              const outLinks = linkCounts.outgoing[p.url] || 0;
              const isOrphan = inLinks === 0 && p.path !== '/';
              const isSelected = selectedPage === p.url;
              const width = Math.max((inLinks / maxLinks) * 100, 2);

              return (
                <div
                  key={i}
                  onClick={() => setSelectedPage(isSelected ? null : p.url)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '3px 0',
                    cursor: 'pointer', borderBottom: '1px solid #1f2937',
                    background: isSelected ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                  }}
                >
                  <span style={{
                    fontSize: 10, color: isOrphan ? '#ef4444' : '#9ca3af',
                    width: 80, flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {p.path}
                  </span>
                  <div style={{ flex: 1, background: '#1f2937', borderRadius: 3, height: 16, overflow: 'hidden' }}>
                    <div style={{
                      width: `${width}%`, height: '100%',
                      background: isOrphan ? '#7f1d1d' : '#1d4ed8',
                      borderRadius: 3, display: 'flex', alignItems: 'center', paddingLeft: 4,
                    }}>
                      <span style={{ fontSize: 9, color: '#fff' }}>{inLinks} in / {outLinks} out</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {selectedPage && (
          <div style={{ borderLeft: '1px solid #1f2937', paddingLeft: 16 }}>
            <p style={{ color: '#3b82f6', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
              {new URL(selectedPage).pathname}
            </p>
            <p style={{ color: '#6b7280', fontSize: 10, marginBottom: 12 }}>
              {linkCounts.incoming[selectedPage] || 0} incoming · {linkCounts.outgoing[selectedPage] || 0} outgoing
            </p>

            <p style={{ color: '#22c55e', fontSize: 11, fontWeight: 600, marginBottom: 4 }}>Incoming links ({selectedLinks.incoming.length}):</p>
            <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 12 }}>
              {selectedLinks.incoming.slice(0, 20).map((url, i) => (
                <div key={i} style={{ fontSize: 10, color: '#9ca3af', padding: '2px 0' }}>
                  {new URL(url).pathname}
                </div>
              ))}
            </div>

            <p style={{ color: '#eab308', fontSize: 11, fontWeight: 600, marginBottom: 4 }}>Outgoing links ({selectedLinks.outgoing.length}):</p>
            <div style={{ maxHeight: 200, overflowY: 'auto' }}>
              {selectedLinks.outgoing.slice(0, 20).map((url, i) => (
                <div key={i} style={{ fontSize: 10, color: '#9ca3af', padding: '2px 0' }}>
                  {new URL(url).pathname}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
