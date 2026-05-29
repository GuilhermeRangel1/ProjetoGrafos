import { useState, useMemo } from 'react'

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
    return allGenres.filter((g) => g.toLowerCase().includes(genreSearch.toLowerCase()))
  }, [allGenres, genreSearch])

  const allActive = !activeGenres || activeGenres.size === 0

  const toggleGenre = (g) => {
    if (!activeGenres || activeGenres.size === 0) {
      // Start from "all selected", uncheck one means show only others
      const next = new Set(allGenres)
      next.delete(g)
      setActiveGenres(next)
    } else {
      const next = new Set(activeGenres)
      if (next.has(g)) {
        next.delete(g)
      } else {
        next.add(g)
      }
      if (next.size === allGenres.length) {
        setActiveGenres(null)
      } else {
        setActiveGenres(next)
      }
    }
  }

  const isActive = (g) => allActive || (activeGenres && activeGenres.has(g))

  return (
    <div className="absolute top-0 left-0 h-full flex flex-col z-20 pointer-events-none">
      {/* Toggle button */}
      <button
        className="pointer-events-auto mt-4 ml-4 bg-[#12121c]/90 border border-slate-700/60 rounded-lg px-3 py-1.5 text-slate-300 text-xs hover:text-white hover:border-slate-500 transition-all self-start"
        onClick={() => setPanelOpen((v) => !v)}
      >
        {panelOpen ? '← Hide' : '→ Filters'}
      </button>

      {panelOpen && (
        <div className="pointer-events-auto ml-4 mt-2 w-64 bg-[#12121c]/95 backdrop-blur border border-slate-700/50 rounded-xl flex flex-col shadow-2xl overflow-hidden max-h-[calc(100vh-100px)]">
          {/* Search */}
          <div className="px-3 pt-3 pb-2 border-b border-slate-700/50 space-y-2">
            <input
              type="text"
              placeholder="Search artist…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-1.5 outline-none border border-slate-600/50 focus:border-[#1DB954]/60 placeholder-slate-500"
            />
            <input
              type="text"
              placeholder="Search song…"
              value={trackSearchQuery}
              onChange={(e) => setTrackSearchQuery(e.target.value)}
              className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-1.5 outline-none border border-slate-600/50 focus:border-[#1DB954]/60 placeholder-slate-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto">
            {/* Sliders */}
            <div className="px-3 py-3 space-y-4 border-b border-slate-700/50">
              <SliderRow
                label="Min Popularity"
                value={minPopularity}
                min={0}
                max={100}
                step={5}
                onChange={setMinPopularity}
                format={(v) => v}
              />
              <SliderRow
                label="Min Genres per Artist"
                value={minGenreCount}
                min={1}
                max={10}
                step={1}
                onChange={setMinGenreCount}
                format={(v) => v}
              />
              <SliderRow
                label="Max Artists"
                value={maxArtists}
                min={500}
                max={5000}
                step={500}
                onChange={setMaxArtists}
                format={(v) => v.toLocaleString()}
              />
            </div>

            {/* Controls row */}
            <div className="px-3 py-2 flex gap-2 border-b border-slate-700/50">
              <button
                onClick={onResetView}
                className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs py-1.5 rounded-lg transition-colors"
              >
                Reset View
              </button>
              <button
                onClick={() => setShowLabels((v) => !v)}
                className={`flex-1 text-xs py-1.5 rounded-lg transition-colors border ${
                  showLabels
                    ? 'bg-[#1DB954]/20 border-[#1DB954]/50 text-[#1DB954]'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
                }`}
              >
                Labels {showLabels ? 'On' : 'Off'}
              </button>
            </div>

            {/* Show Songs Toggle */}
            <div className="px-3 py-2 flex items-center justify-between border-b border-slate-700/50">
              <span className="text-slate-400 text-xs font-medium">Exibir Músicas</span>
              <button
                onClick={() => setShowTracks((v) => !v)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors border ${
                  showTracks
                    ? 'bg-[#1DB954]/20 border-[#1DB954]/50 text-[#1DB954]'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
                }`}
              >
                {showTracks ? 'Sim' : 'Não'}
              </button>
            </div>

            {/* Stats */}
            <div className="px-3 py-2 flex gap-3 border-b border-slate-700/50">
              <span className="text-slate-500 text-[10px]">{nodeCount.toLocaleString()} nodes</span>
              <span className="text-slate-500 text-[10px]">{linkCount.toLocaleString()} links</span>
            </div>

            {/* Genre filter */}
            <div className="px-3 py-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold">
                  Genres ({allGenres.length})
                </span>
                <button
                  className="text-[#1DB954] text-[10px] hover:underline"
                  onClick={() => setActiveGenres(null)}
                >
                  All
                </button>
              </div>
              <input
                type="text"
                placeholder="Filter genres…"
                value={genreSearch}
                onChange={(e) => setGenreSearch(e.target.value)}
                className="w-full bg-slate-800 text-white text-xs rounded-md px-2 py-1 outline-none border border-slate-600/50 focus:border-[#1DB954]/60 placeholder-slate-500 mb-2"
              />
              <div className="space-y-0.5 max-h-48 overflow-y-auto pr-1">
                {filteredGenres.map((g) => {
                  const color = genreColorMap.get(g) || '#888'
                  const active = isActive(g)
                  return (
                    <label
                      key={g}
                      className="flex items-center gap-2 cursor-pointer py-0.5 group"
                    >
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0 transition-opacity"
                        style={{ background: color, opacity: active ? 1 : 0.2 }}
                      />
                      <input
                        type="checkbox"
                        className="hidden"
                        checked={active}
                        onChange={() => toggleGenre(g)}
                      />
                      <span
                        className={`text-xs truncate transition-colors ${
                          active ? 'text-slate-300' : 'text-slate-600'
                        } group-hover:text-slate-200`}
                      >
                        {g}
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
        <span className="text-slate-400 text-[11px]">{label}</span>
        <span className="text-[#1DB954] text-[11px] font-semibold">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[#1DB954] h-1"
      />
    </div>
  )
}
