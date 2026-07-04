import { useState, useMemo } from 'react'
import { displayGenreLabel, normalizeGenreText } from '../utils/genreTranslations'

export default function Controls({
  allGenres,
  genreColorMap,
  activeGenres,
  setActiveGenres,
  minPopularity,
  setMinPopularity,
  minGenreCount,
  setMinGenreCount,
  maxArtists,
  setMaxArtists,
  showTracks,
  setShowTracks,
  searchQuery,
  setSearchQuery,
  trackSearchQuery,
  setTrackSearchQuery,
  showLabels,
  setShowLabels,
  onResetView,
  nodeCount,
  linkCount,
}) {
  const [genreSearch, setGenreSearch] = useState('')
  const [panelOpen, setPanelOpen] = useState(true)

  const filteredGenres = useMemo(() => {
    if (!genreSearch) return allGenres
    const query = genreSearch.toLowerCase()
    return allGenres.filter((genre) =>
      genre.toLowerCase().includes(query) || normalizeGenreText(genre).includes(query)
    )
  }, [allGenres, genreSearch])

  const allActive = !activeGenres || activeGenres.size === 0

  const toggleGenre = (genre) => {
    if (!activeGenres || activeGenres.size === 0) {
      const next = new Set(allGenres)
      next.delete(genre)
      setActiveGenres(next)
    } else {
      const next = new Set(activeGenres)
      if (next.has(genre)) {
        next.delete(genre)
      } else {
        next.add(genre)
      }
      if (next.size === allGenres.length) {
        setActiveGenres(null)
      } else {
        setActiveGenres(next)
      }
    }
  }

  const isActive = (genre) => allActive || (activeGenres && activeGenres.has(genre))

  return (
    <div className="absolute top-0 left-0 h-full flex flex-col z-20 pointer-events-none">
      <button
        className="pointer-events-auto mt-4 ml-4 bg-[#1f2d1e]/88 border border-[#c4b37e]/40 rounded-full px-3 py-1.5 text-[#efe6c8] text-xs hover:border-[#8fbd8c] transition-all self-start shadow-[0_10px_28px_rgba(0,0,0,0.22)]"
        onClick={() => setPanelOpen((v) => !v)}
      >
        {panelOpen ? '< Ocultar' : '> Filtros'}
      </button>

      {panelOpen && (
        <div className="pointer-events-auto ml-4 mt-2 w-64 bg-[#1f2d1e]/90 backdrop-blur border border-[#c4b37e]/35 rounded-xl flex flex-col shadow-[0_22px_52px_rgba(0,0,0,0.32)] overflow-hidden max-h-[calc(100vh-100px)]">
          <div className="px-3 pt-3 pb-2 border-b border-[#c4b37e]/25 space-y-2">
            <input
              type="text"
              placeholder="Buscar artista..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#111a12]/70 text-[#efe6c8] text-sm rounded-lg px-3 py-1.5 outline-none border border-[#c4b37e]/30 focus:border-[#8fbd8c] placeholder-[#9f9475]"
            />
            <input
              type="text"
              placeholder="Buscar música..."
              value={trackSearchQuery}
              onChange={(e) => setTrackSearchQuery(e.target.value)}
              className="w-full bg-[#111a12]/70 text-[#efe6c8] text-sm rounded-lg px-3 py-1.5 outline-none border border-[#c4b37e]/30 focus:border-[#8fbd8c] placeholder-[#9f9475]"
            />
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="px-3 py-3 space-y-4 border-b border-[#c4b37e]/25">
              <SliderRow
                label="Popularidade mínima"
                value={minPopularity}
                min={0}
                max={100}
                step={5}
                onChange={setMinPopularity}
                format={(value) => value}
              />
              <SliderRow
                label="Mín. gêneros por artista"
                value={minGenreCount}
                min={1}
                max={10}
                step={1}
                onChange={setMinGenreCount}
                format={(value) => value}
              />
              <SliderRow
                label="Máx. artistas"
                value={maxArtists}
                min={500}
                max={10000}
                step={500}
                onChange={setMaxArtists}
                format={(value) => value.toLocaleString('pt-BR')}
              />
            </div>

            <div className="px-3 py-2 flex gap-2 border-b border-[#c4b37e]/25">
              <button
                onClick={onResetView}
                className="flex-1 bg-[#293b28] hover:bg-[#334932] text-[#efe6c8] text-xs py-1.5 rounded-lg transition-colors border border-[#8fbd8c]/30"
              >
                Recentrar
              </button>
              <div className="flex-1 flex items-center justify-between bg-[#293b28] border border-[#8fbd8c]/30 rounded-lg px-2 py-1.5">
                <span className="text-[#d9cfad] text-xs">Rótulos</span>
                <button
                  type="button"
                  aria-label={showLabels ? 'Desativar rótulos' : 'Ativar rótulos'}
                  title={showLabels ? 'Desativar rótulos' : 'Ativar rótulos'}
                  onClick={() => setShowLabels((value) => !value)}
                  className={`relative h-4 w-8 rounded-full border transition-colors ${
                    showLabels
                      ? 'bg-[#8fbd8c]/35 border-[#8fbd8c]/70'
                      : 'bg-[#121b13] border-[#c4b37e]/45'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-2.5 w-2.5 rounded-full transition-all ${
                      showLabels ? 'left-4 bg-[#8fbd8c]' : 'left-0.5 bg-[#9f9475]'
                    }`}
                  />
                </button>
              </div>
            </div>

            <div className="px-3 py-2 border-b border-[#c4b37e]/25">
              <div className="flex items-center justify-between">
                <span className="text-[#d9cfad] text-xs font-medium">Exibir músicas</span>
                <button
                  onClick={() => setShowTracks((value) => !value)}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors border ${
                    showTracks
                      ? 'bg-[#8fbd8c]/25 border-[#8fbd8c]/60 text-[#eaf3dc]'
                      : 'bg-[#111a12]/70 border-[#c4b37e]/35 text-[#d9cfad] hover:text-[#efe6c8]'
                  }`}
                >
                  {showTracks ? 'Sim' : 'Não'}
                </button>
              </div>
              <p className="mt-1 text-[10px] leading-snug text-[#a9a080]">
                Desativado por padrão para manter mais artistas na tela com melhor desempenho.
              </p>
            </div>

            <div className="px-3 py-2 flex gap-3 border-b border-[#c4b37e]/25">
              <span className="text-[#a9a080] text-[10px]">{nodeCount.toLocaleString('pt-BR')} nós</span>
              <span className="text-[#a9a080] text-[10px]">{linkCount.toLocaleString('pt-BR')} conexões</span>
            </div>

            <div className="px-3 py-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[#d9cfad] text-[10px] uppercase tracking-wider font-semibold">
                  Gêneros ({allGenres.length})
                </span>
                <button
                  className="text-[#8fbd8c] text-[10px] hover:underline"
                  onClick={() => setActiveGenres(null)}
                >
                  Todos
                </button>
              </div>
              <input
                type="text"
                placeholder="Filtrar gêneros..."
                value={genreSearch}
                onChange={(e) => setGenreSearch(e.target.value)}
                className="w-full bg-[#111a12]/70 text-[#efe6c8] text-xs rounded-md px-2 py-1 outline-none border border-[#c4b37e]/30 focus:border-[#8fbd8c] placeholder-[#9f9475] mb-2"
              />
              <div className="space-y-0.5 max-h-48 overflow-y-auto pr-1">
                {filteredGenres.map((genre) => {
                  const color = genreColorMap.get(genre) || '#888'
                  const active = isActive(genre)
                  return (
                    <label
                      key={genre}
                      className="flex items-center gap-2 cursor-pointer py-0.5 group"
                      title={genre}
                    >
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0 transition-opacity"
                        style={{ background: color, opacity: active ? 1 : 0.2 }}
                      />
                      <input
                        type="checkbox"
                        className="hidden"
                        checked={active}
                        onChange={() => toggleGenre(genre)}
                      />
                      <span
                        className={`text-xs truncate transition-colors ${
                          active ? 'text-[#efe6c8]' : 'text-[#7e866e]'
                        } group-hover:text-[#f7efcf]`}
                      >
                        {displayGenreLabel(genre)}
                      </span>
                    </label>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SliderRow({ label, value, min, max, step, onChange, format }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-[#d9cfad] text-[11px]">{label}</span>
        <span className="text-[#8fbd8c] text-[11px] font-semibold">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[#8fbd8c] h-1"
      />
    </div>
  )
}
