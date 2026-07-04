import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export default function Sidebar({ node, genreColorMap, onSelectTrack, onClose }) {
  const [playlist, setPlaylist] = useState(null)
  const [loadingPlaylist, setLoadingPlaylist] = useState(false)
  const [playlistError, setPlaylistError] = useState(null)
  const handleGeneratePlaylist = async (algorithm) => {
    setLoadingPlaylist(true)
    setPlaylistError(null)
    setPlaylist(null)
    
    try {
      // Usar node.rawId ou node.label como seed (track id ou nome de artista)
      const seed = node.type === 'track' ? node.rawId : node.label
      const res = await fetch(`${API_URL}/api/playlist?seed=${encodeURIComponent(seed)}&algorithm=${algorithm}`)
      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.error || 'Erro ao gerar playlist')
      }
      
      setPlaylist(data)
    } catch (err) {
      setPlaylistError(err.message)
    } finally {
      setLoadingPlaylist(false)
    }
  }

  if (!node) return null

  const isGenre = node.type === 'genre'
  const isTrack = node.type === 'track'
  const color = isGenre
    ? genreColorMap.get(node.label) || '#888'
    : isTrack
      ? '#1DB954'
      : genreColorMap.get(node.genres?.[0]) || '#888'

  return (
    <div className="absolute top-0 right-0 h-full w-[22rem] sm:w-[26rem] max-w-[calc(100vw-1rem)] bg-[#12121c]/95 backdrop-blur border-l border-slate-700/50 flex flex-col z-20 shadow-2xl">
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

            <div className="-mx-4 pt-2">
              <iframe
                key={node.rawId}
                src={`https://open.spotify.com/embed/track/${node.rawId}?utm_source=generator&autoplay=1`}
                width="100%"
                height="152"
                frameBorder="0"
                scrolling="no"
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                loading="lazy"
                style={{ display: 'block' }}
              />
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
              {node.topTracks.slice(0, 20).map((t, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-slate-600 text-xs w-4 text-right shrink-0">{i + 1}</span>
                  <button
                    type="button"
                    onClick={() => onSelectTrack?.(t, node)}
                    className="text-left text-slate-300 hover:text-[#1DB954] text-xs truncate flex-1 transition-colors hover:underline"
                    title="Selecionar música no grafo"
                  >
                    {t.name}
                  </button>
                  <PopularityBar value={t.popularity} color={color} />
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Playlist Generator Section */}
        {(!isGenre) && (
          <section className="pt-2 border-t border-slate-700/50">
            <SectionTitle>Gerar Playlist Automática</SectionTitle>
            <p className="text-[10px] text-slate-400 mt-1 mb-3">
              Baseada na similaridade entre músicas usando os algoritmos de grafos BFS e DFS.
            </p>
            <div className="flex flex-col gap-2">
              <button 
                onClick={() => handleGeneratePlaylist('bfs')}
                disabled={loadingPlaylist}
                className="w-full bg-[#1DB954]/20 hover:bg-[#1DB954]/30 text-[#1DB954] border border-[#1DB954]/50 py-1.5 px-3 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
              >
                🎶 Playlist Suave (BFS)
              </button>
              <button 
                onClick={() => handleGeneratePlaylist('dfs')}
                disabled={loadingPlaylist}
                className="w-full bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/50 py-1.5 px-3 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
              >
                🎸 Mergulho Profundo (DFS)
              </button>
            </div>

            {loadingPlaylist && (
              <div className="text-xs text-[#1DB954] mt-3 animate-pulse">Gerando playlist no backend Python...</div>
            )}

            {playlistError && (
              <div className="text-xs text-red-400 mt-3 bg-red-400/10 p-2 rounded border border-red-400/30">
                {playlistError}
                <div className="text-[9px] mt-1 text-slate-400">Verifique se o backend Python está rodando na porta 5000.</div>
              </div>
            )}

            {playlist && (
              <div className="mt-4 bg-slate-800/40 rounded-lg p-3 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-white">Playlist ({playlist.playlist.length} faixas)</span>
                  <button onClick={() => setPlaylist(null)} className="text-[10px] text-slate-400 hover:text-white">Fechar</button>
                </div>
                
                {playlist.fallback_usado && (
                  <div className="text-[10px] text-yellow-400 mb-3 bg-yellow-400/10 p-2 rounded">
                    A música selecionada não estava na nossa amostra processada do grafo. Começamos a playlist a partir de uma música de estilo parecido: <b>{playlist.seed_utilizado.name} - {playlist.seed_utilizado.artist}</b>.
                  </div>
                )}

                <div className="space-y-3 mt-3 max-h-64 overflow-y-auto pr-1">
                  {playlist.playlist.map((track, i) => (
                    <div key={i} className="flex flex-col gap-1">
                      <span className="text-xs font-medium text-slate-200">
                        {i + 1}. {track.name}
                      </span>
                      <span className="text-[10px] text-slate-500">{track.artist}</span>
                      <iframe
                        src={`https://open.spotify.com/embed/track/${track.id}?utm_source=generator`}
                        width="100%"
                        height="80"
                        frameBorder="0"
                        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                        loading="lazy"
                        className="rounded-md mt-1"
                      ></iframe>
                    </div>
                  ))}
                </div>
              </div>
            )}
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
