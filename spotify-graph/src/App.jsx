import { useState, useRef, useCallback, useEffect } from 'react'
import { useGraphData } from './hooks/useGraphData'
import GraphView from './components/GraphView'
import Sidebar from './components/Sidebar'
import Controls from './components/Controls'
import LoadingScreen from './components/LoadingScreen'
import ChartsPanel from './components/ChartsPanel'

function BackButton({ onClick, side = 'right', tone = 'light' }) {
  const isDark = tone === 'dark'

  return (
    <button
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: 20,
        right: side === 'right' ? 20 : 'auto',
        left: side === 'left' ? 20 : 'auto',
        zIndex: 15,
        background: isDark ? 'rgba(31, 45, 30, 0.86)' : 'rgba(255, 249, 235, 0.92)',
        border: isDark ? '1px solid rgba(196, 179, 126, 0.38)' : '1px solid rgba(128, 101, 67, 0.18)',
        color: isDark ? '#efe6c8' : '#6e6a53',
        fontFamily: "'Nunito', 'Inter', sans-serif",
        fontSize: '0.7rem',
        padding: '8px 15px',
        borderRadius: 999,
        cursor: 'pointer',
        transition: 'all 0.18s',
        boxShadow: isDark ? '0 14px 32px rgba(0, 0, 0, 0.24)' : '0 12px 28px rgba(85, 74, 50, 0.16)',
      }}
      onMouseEnter={e => { e.target.style.borderColor = isDark ? '#8fbd8c' : '#8cbf99'; e.target.style.color = isDark ? '#f7efcf' : '#2f5942' }}
      onMouseLeave={e => {
        e.target.style.borderColor = isDark ? 'rgba(196, 179, 126, 0.38)' : 'rgba(128, 101, 67, 0.18)'
        e.target.style.color = isDark ? '#efe6c8' : '#6e6a53'
      }}
    >
      ← Voltar
    </button>
  )
}

function LandingPage({ onSelect }) {
  const cards = [
    {
      id: 'airports',
      icon: '✈',
      title: 'Aeroportos do Brasil',
      desc: 'Rede de aeroportos brasileiros com rotas, algoritmos de caminho e estatísticas regionais.',
      accent: '#5c9f79',
    },
    {
      id: 'spotify',
      icon: '🎵',
      title: 'Grafo Spotify',
      desc: 'Grafo interativo de artistas e gêneros musicais com geração de playlists via BFS e DFS.',
      accent: '#4f8fb8',
    },
  ]

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: 'linear-gradient(180deg, #f7edcf 0%, #cfe3c2 54%, #a8cfbf 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'Nunito', 'Inter', sans-serif",
      gap: 48,
      color: '#354733',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: "'Nunito', 'Inter', sans-serif",
          fontWeight: 900,
          fontSize: '2.35rem',
          color: '#2f5942',
          marginBottom: 8,
        }}>
          DataGraph
        </div>
        <div style={{ color: '#6e6a53', fontSize: '0.75rem', letterSpacing: 1.4, fontWeight: 800 }}>
          SELECIONE UMA VISUALIZAÇÃO
        </div>
      </div>

      <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap', justifyContent: 'center' }}>
        {cards.map(card => (
          <button
            key={card.id}
            onClick={() => onSelect(card.id)}
            style={{
              background: 'rgba(255, 249, 235, 0.82)',
              border: `1px solid rgba(128, 101, 67, 0.16)`,
              borderRadius: 18,
              padding: '36px 40px',
              width: 260,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s',
              color: '#354733',
              boxShadow: '0 18px 40px rgba(72, 92, 61, 0.16)',
              backdropFilter: 'blur(10px)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = card.accent
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = `0 22px 46px ${card.accent}35`
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'rgba(128, 101, 67, 0.16)'
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = '0 18px 40px rgba(72, 92, 61, 0.16)'
            }}
          >
            <div style={{ fontSize: '2.2rem', marginBottom: 16 }}>{card.icon}</div>
            <div style={{
              fontFamily: "'Nunito', 'Inter', sans-serif",
              fontWeight: 900,
              fontSize: '1rem',
              color: card.accent,
              marginBottom: 10,
            }}>
              {card.title}
            </div>
            <div style={{ fontSize: '0.76rem', color: '#6e6a53', lineHeight: 1.65 }}>
              {card.desc}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function SpotifyApp({ onBack }) {
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [trackSearchQuery, setTrackSearchQuery] = useState('')
  const [showLabels, setShowLabels] = useState(false)
  const [showCharts, setShowCharts] = useState(false)
  const [graphExecution, setGraphExecution] = useState(null)
  const executionTimerRef = useRef(null)
  const focusedArtistId = selectedNode?.type === 'artist' ? selectedNode.id : selectedNode?.artistId

  const {
    graphData,
    genreColorMap,
    allGenres,
    loadingProgress,
    loadingStatus,
    error,
    minPopularity,
    setMinPopularity,
    minGenreCount,
    setMinGenreCount,
    activeGenres,
    setActiveGenres,
    maxArtists,
    setMaxArtists,
    showTracks,
    setShowTracks,
  } = useGraphData({ trackSearchQuery, focusedArtistId })

  const graphRef = useRef(null)

  const getEndpointId = useCallback((endpoint) => (
    typeof endpoint === 'object' && endpoint !== null ? endpoint.id : endpoint
  ), [])

  const buildAdjacency = useCallback(() => {
    const adjacency = new Map(graphData.nodes.map((node) => [node.id, []]))
    for (const link of graphData.links) {
      const source = getEndpointId(link.source)
      const target = getEndpointId(link.target)
      if (!adjacency.has(source) || !adjacency.has(target)) continue
      adjacency.get(source).push(target)
      adjacency.get(target).push(source)
    }
    return adjacency
  }, [graphData, getEndpointId])

  const chooseExecutionStart = useCallback((adjacency) => {
    if (selectedNode?.id && adjacency.has(selectedNode.id)) return selectedNode.id
    const artist = graphData.nodes
      .filter((node) => node.type === 'artist' && adjacency.get(node.id)?.length)
      .sort((a, b) => (b.popularityAvg ?? 0) - (a.popularityAvg ?? 0))[0]
    return artist?.id ?? graphData.nodes.find((node) => adjacency.get(node.id)?.length)?.id
  }, [graphData, selectedNode])

  const buildPathFromParents = useCallback((parents, target) => {
    const path = []
    let cursor = target
    while (cursor) {
      path.push(cursor)
      cursor = parents.get(cursor)
    }
    return path.reverse()
  }, [])

  const computeBfsPath = useCallback((adjacency, start) => {
    const queue = [start]
    const parents = new Map([[start, null]])
    let farthest = start

    for (let cursor = 0; cursor < queue.length && cursor < 900; cursor++) {
      const node = queue[cursor]
      farthest = node
      for (const next of adjacency.get(node) ?? []) {
        if (parents.has(next)) continue
        parents.set(next, node)
        queue.push(next)
        if (queue.length > 900) break
      }
    }

    return {
      path: buildPathFromParents(parents, farthest).slice(0, 14),
      visitedOrder: queue.slice(0, 80),
    }
  }, [buildPathFromParents])

  const computeDfsPath = useCallback((adjacency, start) => {
    const visited = new Set()
    const path = []
    const walk = (node, depth = 0) => {
      visited.add(node)
      path.push(node)
      if (depth >= 11) return true
      const nextNodes = [...(adjacency.get(node) ?? [])].sort((a, b) => (adjacency.get(b)?.length ?? 0) - (adjacency.get(a)?.length ?? 0))
      for (const next of nextNodes) {
        if (visited.has(next)) continue
        if (walk(next, depth + 1)) return true
      }
      return path.length >= 9
    }
    walk(start)
    return { path: path.slice(0, 14), visitedOrder: [...visited].slice(0, 80) }
  }, [])

  const computeDijkstraPath = useCallback((adjacency, start) => {
    const distances = new Map([[start, 0]])
    const parents = new Map([[start, null]])
    const visited = new Set()
    const order = []
    let target = start

    const nodes = new Set([start])
    while (nodes.size && order.length < 500) {
      const current = [...nodes].sort((a, b) => (distances.get(a) ?? Infinity) - (distances.get(b) ?? Infinity))[0]
      nodes.delete(current)
      if (visited.has(current)) continue
      visited.add(current)
      order.push(current)
      target = current

      for (const next of adjacency.get(current) ?? []) {
        const degreePenalty = 1 / Math.max(1, adjacency.get(next)?.length ?? 1)
        const weight = 1 + degreePenalty
        const nextDistance = (distances.get(current) ?? 0) + weight
        if (nextDistance < (distances.get(next) ?? Infinity)) {
          distances.set(next, nextDistance)
          parents.set(next, current)
          nodes.add(next)
        }
      }
    }

    return {
      path: buildPathFromParents(parents, target).slice(0, 14),
      visitedOrder: order.slice(0, 80),
    }
  }, [buildPathFromParents])

  const startGraphExecution = useCallback((algorithm) => {
    const adjacency = buildAdjacency()
    const start = chooseExecutionStart(adjacency)
    if (!start) return

    if (executionTimerRef.current) window.clearInterval(executionTimerRef.current)
    setSelectedNode(null)

    const result =
      algorithm === 'dfs'
        ? computeDfsPath(adjacency, start)
        : algorithm === 'dijkstra'
          ? computeDijkstraPath(adjacency, start)
          : computeBfsPath(adjacency, start)

    const path = result.path.length > 1 ? result.path : result.visitedOrder.slice(0, 10)
    const pathNodeIds = new Set(path)
    const pathLinks = path.slice(0, -1).map((nodeId, index) => `${nodeId}->${path[index + 1]}`)
    let step = 1

    setGraphExecution({
      active: true,
      algorithm,
      label: algorithm === 'dfs' ? 'DFS' : algorithm === 'dijkstra' ? 'Dijkstra' : 'BFS',
      path,
      pathNodeIds,
      visitedNodeIds: new Set(path.slice(0, step)),
      activeLinkIds: new Set(),
      currentNodeId: path[0],
      step,
      total: path.length,
    })

    const firstNode = graphData.nodes.find((node) => node.id === path[0])
    if (firstNode && graphRef.current) {
      graphRef.current.centerAt(firstNode.x ?? 0, firstNode.y ?? 0, 700)
      graphRef.current.zoom(Math.max(graphRef.current.zoom(), 1.4), 700)
    }

    executionTimerRef.current = window.setInterval(() => {
      step += 1
      setGraphExecution((prev) => {
        if (!prev) return prev
        const boundedStep = Math.min(step, path.length)
        const nextNode = path[boundedStep - 1]
        const graphNode = graphData.nodes.find((node) => node.id === nextNode)
        if (graphNode && graphRef.current) {
          graphRef.current.centerAt(graphNode.x ?? 0, graphNode.y ?? 0, 420)
        }
        return {
          ...prev,
          visitedNodeIds: new Set(path.slice(0, boundedStep)),
          activeLinkIds: new Set(pathLinks.slice(0, Math.max(0, boundedStep - 1))),
          currentNodeId: nextNode,
          step: boundedStep,
        }
      })
      if (step >= path.length && executionTimerRef.current) {
        window.clearInterval(executionTimerRef.current)
        executionTimerRef.current = null
      }
    }, 720)
  }, [buildAdjacency, chooseExecutionStart, computeBfsPath, computeDfsPath, computeDijkstraPath, graphData, setSelectedNode])

  const stopGraphExecution = useCallback(() => {
    if (executionTimerRef.current) window.clearInterval(executionTimerRef.current)
    executionTimerRef.current = null
    setGraphExecution(null)
  }, [])

  useEffect(() => () => {
    if (executionTimerRef.current) window.clearInterval(executionTimerRef.current)
  }, [])

  const handleResetView = useCallback(() => {
    if (graphRef.current) graphRef.current.zoomToFit(600, 60)
    setSelectedNode(null)
    stopGraphExecution()
  }, [stopGraphExecution])

  const handleSelectSidebarTrack = useCallback((track, artist) => {
    if (!track || !artist) return
    const trackNodeId = `track:${artist.id}:${track.id}`
    setSelectedNode({
      id: trackNodeId,
      rawId: track.id,
      type: 'track',
      label: track.name,
      popularity: track.popularity,
      artistId: artist.id,
      artistLabel: artist.label,
      genre: artist.genres?.[0] || '',
    })
  }, [])

  const isDone = loadingStatus === 'done'
  const isError = loadingStatus === 'error'
  const isLoading = loadingStatus === 'loading' || loadingStatus === 'idle'

  return (
    <div
      className="relative w-screen h-screen overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #10170f 0%, #182719 48%, #263a2a 100%)',
      }}
    >
      {(isLoading || isError) && (
        <LoadingScreen progress={loadingProgress} status={loadingStatus} error={error} />
      )}

      {isDone && (
        <>
          <GraphView
            graphData={graphData}
            genreColorMap={genreColorMap}
            selectedNode={selectedNode}
            setSelectedNode={setSelectedNode}
            searchQuery={searchQuery}
            trackSearchQuery={trackSearchQuery}
            showLabels={showLabels}
            graphRef={graphRef}
            graphExecution={graphExecution}
          />

          <Controls
            allGenres={allGenres}
            genreColorMap={genreColorMap}
            activeGenres={activeGenres}
            setActiveGenres={setActiveGenres}
            minPopularity={minPopularity}
            setMinPopularity={setMinPopularity}
            minGenreCount={minGenreCount}
            setMinGenreCount={setMinGenreCount}
            maxArtists={maxArtists}
            setMaxArtists={setMaxArtists}
            showTracks={showTracks}
            setShowTracks={setShowTracks}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            trackSearchQuery={trackSearchQuery}
            setTrackSearchQuery={setTrackSearchQuery}
            showLabels={showLabels}
            setShowLabels={setShowLabels}
            onResetView={handleResetView}
            nodeCount={graphData.nodes.length}
            linkCount={graphData.links.length}
          />

          {selectedNode && (
            <Sidebar
              node={selectedNode}
              genreColorMap={genreColorMap}
              onSelectTrack={handleSelectSidebarTrack}
              onClose={() => setSelectedNode(null)}
            />
          )}

          <div className="absolute top-4 right-4 flex flex-col items-end gap-2 z-10">
            <button
              onClick={() => setShowCharts(true)}
              style={{
                background: 'rgba(31, 45, 30, 0.86)',
                border: '1px solid rgba(196, 179, 126, 0.38)',
                color: '#efe6c8',
                fontFamily: "'Nunito', 'Inter', sans-serif",
                fontSize: '0.7rem',
                padding: '7px 14px',
                borderRadius: '999px',
                cursor: 'pointer',
                fontWeight: 800,
                boxShadow: '0 14px 32px rgba(0, 0, 0, 0.24)',
              }}
            >
              Gráficos
            </button>
            <div
              style={{
                width: 230,
                background: 'rgba(31, 45, 30, 0.88)',
                border: '1px solid rgba(196, 179, 126, 0.38)',
                borderRadius: 12,
                padding: 12,
                boxShadow: '0 18px 40px rgba(0,0,0,0.28)',
                backdropFilter: 'blur(10px)',
                color: '#efe6c8',
                fontFamily: "'Nunito', 'Inter', sans-serif",
              }}
            >
              <div style={{ fontSize: '0.62rem', letterSpacing: 1.5, textTransform: 'uppercase', color: '#8fbd8c', fontWeight: 900, marginBottom: 8 }}>
                Executar no grafo
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                {[
                  ['bfs', 'BFS'],
                  ['dfs', 'DFS'],
                  ['dijkstra', 'Dijkstra'],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    onClick={() => startGraphExecution(id)}
                    style={{
                      background: graphExecution?.algorithm === id ? 'rgba(143,189,140,0.24)' : 'rgba(16,23,15,0.58)',
                      border: `1px solid ${graphExecution?.algorithm === id ? '#8fbd8c' : 'rgba(196,179,126,0.32)'}`,
                      color: '#efe6c8',
                      borderRadius: 8,
                      padding: '7px 6px',
                      fontSize: '0.64rem',
                      fontWeight: 900,
                      cursor: 'pointer',
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {graphExecution && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ color: '#d9cfad', fontSize: '0.66rem', marginBottom: 6 }}>
                    {graphExecution.label}: passo {graphExecution.step}/{graphExecution.total}
                  </div>
                  <div style={{ height: 5, borderRadius: 999, background: 'rgba(239,230,200,0.14)', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${Math.min(100, (graphExecution.step / graphExecution.total) * 100)}%`,
                        background: '#8fbd8c',
                        transition: 'width 0.35s ease',
                      }}
                    />
                  </div>
                  <button
                    onClick={stopGraphExecution}
                    style={{
                      marginTop: 8,
                      width: '100%',
                      background: 'rgba(200,138,154,0.14)',
                      border: '1px solid rgba(200,138,154,0.45)',
                      color: '#f7efcf',
                      borderRadius: 8,
                      padding: '6px 8px',
                      fontSize: '0.64rem',
                      fontWeight: 900,
                      cursor: 'pointer',
                    }}
                  >
                    Apagar execução
                  </button>
                </div>
              )}
            </div>
            <div className="bg-[#1f2d1e]/86 backdrop-blur border border-[#c4b37e]/40 rounded-lg px-3 py-2 flex gap-4 text-xs text-[#d9cfad] pointer-events-none shadow-sm">
              <span className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded-full bg-[#5c9f79] inline-block" />
                Nó de gênero
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#4f8fb8] inline-block" />
                Nó de artista
              </span>
            </div>
          </div>

          {showCharts && <ChartsPanel onClose={() => setShowCharts(false)} />}
        </>
      )}

      {isDone && !selectedNode && !showCharts && <BackButton onClick={onBack} side="left" tone="dark" />}
    </div>
  )
}

export default function App() {
  const [view, setView] = useState(null)

  if (view === 'airports') {
    return (
      <>
        <iframe
          src="/grafo_interativo.html"
          style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', border: 'none' }}
          title="Aeroportos do Brasil"
        />
        <BackButton onClick={() => setView(null)} />
      </>
    )
  }

  if (view === 'spotify') {
    return <SpotifyApp onBack={() => setView(null)} />
  }

  return <LandingPage onSelect={setView} />
}
