export default function Sidebar({ node, genreColorMap, onClose }) {
  if (!node) return null

  const isGenre = node.type === 'genre'
  const color = isGenre
    ? genreColorMap.get(node.label) || '#888'
    : genreColorMap.get(node.genres?.[0]) || '#888'

  return (
    <div className="absolute top-0 right-0 h-full w-72 bg-[#12121c]/95 backdrop-blur border-l border-slate-700/50 flex flex-col z-20 shadow-2xl">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50"
        style={{ borderTopColor: color, borderTopWidth: 3 }}
      >
        <div>
          <span
            className="text-[10px] font-semibold uppercase tracking-widest"
            style={{ color }}
          >
            {isGenre ? 'Genre' : 'Artist'}
          </span>
          <h2 className="text-white font-bold text-base leading-tight mt-0.5 truncate max-w-[200px]">
            {node.label}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-white transition-colors text-lg leading-none"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Avg Popularity" value={node.popularityAvg?.toFixed(1) ?? '—'} />
          <StatCard label="Tracks" value={node.trackCount?.toLocaleString() ?? '—'} />
          {!isGenre && (
            <StatCard label="Genres" value={node.genreCount ?? '—'} />
          )}
        </div>

        {/* Genres (for artist nodes) */}
        {!isGenre && node.genres && node.genres.length > 0 && (
          <section>
            <SectionTitle>Genres</SectionTitle>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {node.genres.sort().map((g) => (
                <span
                  key={g}
                  className="text-[11px] px-2 py-0.5 rounded-full font-medium"
                  style={{
                    background: `${genreColorMap.get(g) || '#888'}22`,
                    color: genreColorMap.get(g) || '#aaa',
                    border: `1px solid ${genreColorMap.get(g) || '#888'}55`,
                  }}
                >
                  {g}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Top tracks (artist only) */}
        {!isGenre && node.topTracks && node.topTracks.length > 0 && (
          <section>
            <SectionTitle>Top Tracks</SectionTitle>
            <ul className="mt-2 space-y-1.5">
              {node.topTracks.map((t, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-slate-600 text-xs w-4 text-right shrink-0">{i + 1}</span>
                  <span className="text-slate-300 text-xs truncate flex-1">{t.name}</span>
                  <PopularityBar value={t.popularity} color={color} />
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="bg-slate-800/60 rounded-lg px-3 py-2">
      <div className="text-slate-500 text-[10px] uppercase tracking-wider">{label}</div>
      <div className="text-white font-semibold text-lg">{value}</div>
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <h3 className="text-slate-500 text-[10px] uppercase tracking-wider font-semibold">{children}</h3>
  )
}

function PopularityBar({ value, color }) {
  return (
    <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden shrink-0">
      <div
        className="h-full rounded-full"
        style={{ width: `${value}%`, background: color }}
      />
    </div>
  )
}
