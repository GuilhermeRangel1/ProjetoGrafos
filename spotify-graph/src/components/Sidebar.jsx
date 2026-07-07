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
    <div className="absolute top-0 right-0 h-full w-[22rem] sm:w-[26rem] max-w-[calc(100vw-1rem)] bg-[#1f2d1e]/92 backdrop-blur border-l border-[#c4b37e]/35 flex flex-col z-20 shadow-[0_22px_56px_rgba(0,0,0,0.38)]">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-[#c4b37e]/25"
        style={{ borderTopColor: color, borderTopWidth: 3 }}
      >
        <div>
          <span
            className="text-[10px] font-semibold uppercase tracking-widest"
            style={{ color }}
          >
            {isGenre ? 'Gênero' : (isTrack ? 'Música' : 'Artista')}
          </span>
          <h2 className="text-[#f7efcf] font-bold text-base leading-tight mt-0.5 truncate max-w-[260px]" title={node.label}>
            {node.label}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-[#a9a080] hover:text-[#f7efcf] transition-colors text-lg leading-none"
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
              <StatCard label="Popularidade média" value={node.popularityAvg?.toFixed(1) ?? '—'} />
              <StatCard label="Faixas" value={node.trackCount?.toLocaleString() ?? '—'} />
            </>
          )}
          {!isGenre && !isTrack && (
            <StatCard label="Gêneros" value={node.genreCount ?? '—'} />
          )}
        </div>

        {/* Track Specific details */}
        {isTrack && (
          <section className="space-y-4">
            <div>
              <SectionTitle>Artista</SectionTitle>
              <div className="text-[#f7efcf] font-medium text-sm mt-1">{node.artistLabel}</div>
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

        {/* Genres for artist nodes */}
        {!isGenre && !isTrack && node.genres && node.genres.length > 0 && (
          <section>
            <SectionTitle>Gêneros</SectionTitle>
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
            <SectionTitle>Principais faixas</SectionTitle>
            <ul className="mt-2 space-y-1.5">
              {node.topTracks.slice(0, 20).map((t, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-[#7e866e] text-xs w-4 text-right shrink-0">{i + 1}</span>
                  <button
                    type="button"
                    onClick={() => onSelectTrack?.(t, node)}
                    className="text-left text-[#efe6c8] hover:text-[#8fbd8c] text-xs truncate flex-1 transition-colors hover:underline"
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
          <section className="pt-2 border-t border-[#c4b37e]/25">
            <SectionTitle>Gerar Playlist Automática</SectionTitle>
            <p className="text-[10px] text-[#b8ad8b] mt-1 mb-3">
              Baseada na similaridade entre músicas usando os algoritmos de grafos BFS e DFS.
            </p>
            <div className="flex flex-col gap-2">
              <button 
                onClick={() => handleGeneratePlaylist('bfs')}
                disabled={loadingPlaylist}
                className="w-full bg-[#8fbd8c]/20 hover:bg-[#8fbd8c]/30 text-[#eaf3dc] border border-[#8fbd8c]/45 py-1.5 px-3 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
              >
                🎶 Playlist Suave (BFS)
              </button>
              <button 
                onClick={() => handleGeneratePlaylist('dfs')}
                disabled={loadingPlaylist}
                className="w-full bg-[#c88a9a]/20 hover:bg-[#c88a9a]/30 text-[#f0bdc8] border border-[#c88a9a]/40 py-1.5 px-3 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
              >
                🎸 Mergulho Profundo (DFS)
              </button>
            </div>

            {loadingPlaylist && (
              <div className="text-xs text-[#8fbd8c] mt-3 animate-pulse">Gerando playlist no backend Python...</div>
            )}

            {playlistError && (
              <div className="text-xs text-[#f0bdc8] mt-3 bg-[#c88a9a]/20 p-2 rounded border border-[#c88a9a]/30">
                {playlistError}
                <div className="text-[9px] mt-1 text-slate-400">Verifique se o backend Python está rodando na porta 5000.</div>
              </div>
            )}

            {playlist && (
              <div className="mt-4 bg-[#111a12]/58 rounded-lg p-3 border border-[#c4b37e]/30">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#f7efcf]">Playlist ({playlist.playlist.length} faixas)</span>
                  <button onClick={() => setPlaylist(null)} className="text-[10px] text-[#a9a080] hover:text-[#f7efcf]">Fechar</button>
                </div>
                
                {playlist.fallback_usado && (
                  <div className="text-[10px] leading-relaxed text-[#efe6c8] mb-3 bg-[#8a6d2f]/18 border border-[#c4b37e]/20 p-2.5 rounded-lg">
                    Playlist iniciada por similaridade sonora a partir de <b>{playlist.seed_utilizado.name}</b>, de <b>{playlist.seed_utilizado.artist}</b>.
                  </div>
                )}

                <div className="space-y-3 mt-3 max-h-64 overflow-y-auto pr-1">
                  {playlist.playlist.map((track, i) => (
                    <div key={i} className="flex flex-col gap-1">
                      <span className="text-xs font-medium text-[#f7efcf]">
                        {i + 1}. {track.name}
                      </span>
                      <span className="text-[10px] text-[#a9a080]">{track.artist}</span>
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
    <div className="bg-[#293b28]/72 border border-[#8fbd8c]/25 rounded-lg px-3 py-2">
      <div className="text-[#a9a080] text-[10px] uppercase tracking-wider">{label}</div>
      <div className="text-[#f7efcf] font-semibold text-lg">{value}</div>
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <h3 className="text-[#d9cfad] text-[10px] uppercase tracking-wider font-semibold">{children}</h3>
  )
}

function PopularityBar({ value, color }) {
  return (
    <div className="w-12 h-1.5 bg-[#111a12] rounded-full overflow-hidden shrink-0">
      <div
        className="h-full rounded-full"
        style={{ width: `${value}%`, background: color }}
      />
    </div>
  )
}
