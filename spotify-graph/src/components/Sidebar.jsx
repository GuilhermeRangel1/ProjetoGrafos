export default function Sidebar({ node, genreColorMap, onClose }) {
  if (!node) return null

  const isGenre = node.type === 'genre'
  const isTrack = node.type === 'track'
  const color = isGenre
    ? genreColorMap.get(node.label) || '#888'
    : isTrack
      ? '#1DB954'
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
            {isGenre ? 'Genre' : (isTrack ? 'Música' : 'Artist')}
          </span>
          <h2 className="text-white font-bold text-base leading-tight mt-0.5 truncate max-w-[200px]" title={node.label}>
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
          {isTrack ? (
            <>
              <StatCard label="Popularidade" value={node.popularity ?? '—'} />
              <StatCard label="Gênero" value={node.genre ?? '—'} />
            </>
          ) : (
            <>
              <StatCard label="Avg Popularity" value={node.popularityAvg?.toFixed(1) ?? '—'} />
              <StatCard label="Tracks" value={node.trackCount?.toLocaleString() ?? '—'} />
            </>
          )}
          {!isGenre && !isTrack && (
            <StatCard label="Genres" value={node.genreCount ?? '—'} />
          )}
        </div>

        {/* Track Specific details */}
        {isTrack && (
          <section className="space-y-4">
            <div>
              <SectionTitle>Artista</SectionTitle>
              <div className="text-white font-medium text-sm mt-1">{node.artistLabel}</div>
            </div>

            <div className="pt-2">
              <a
                href={node.spotifyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full bg-[#1DB954] hover:bg-[#1ed760] text-black font-bold py-2.5 px-4 rounded-full transition-colors text-sm shadow-md"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.586 14.424c-.18.295-.565.387-.86.207-2.377-1.454-5.37-1.783-8.893-.978-.336.077-.67-.133-.747-.47-.077-.337.133-.67.47-.747 3.852-.88 7.15-.51 9.816 1.127.295.18.387.563.207.86zm1.226-2.722c-.226.367-.707.487-1.074.26-2.72-1.672-6.87-2.157-10.075-1.182-.413.125-.847-.107-.972-.52-.125-.413.107-.847.52-.972 3.667-1.112 8.225-.572 11.34 1.343.367.227.488.708.26 1.074zm.107-2.833C14.384 8.7 8.564 8.51 5.176 9.537c-.52.158-1.07-.143-1.228-.662-.158-.52.143-1.07.662-1.228 3.885-1.18 10.31-.96 14.37 1.45.47.28.62.89.34 1.36-.28.47-.89.62-1.36.34z"/>
                </svg>
                Ouvir música no Spotify?
              </a>
            </div>
          </section>
        )}

        {/* Genres (for artist nodes) */}
        {!isGenre && !isTrack && node.genres && node.genres.length > 0 && (
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
        {!isGenre && !isTrack && node.topTracks && node.topTracks.length > 0 && (
          <section>
            <SectionTitle>Top Tracks</SectionTitle>
            <ul className="mt-2 space-y-1.5">
              {node.topTracks.map((t, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-slate-600 text-xs w-4 text-right shrink-0">{i + 1}</span>
                  <a
                    href={`https://open.spotify.com/track/${t.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-300 hover:text-[#1DB954] text-xs truncate flex-1 transition-colors hover:underline"
                    title="Ouvir no Spotify"
                  >
                    {t.name}
                  </a>
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
