import { useRef, useCallback, useMemo, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { GENRE_NODE_RADIUS, ARTIST_NODE_RADIUS } from '../utils/colors'
import { displayGenreLabel } from '../utils/genreTranslations'

const MIN_POP = 0
const MAX_POP = 100

const getLinkEndpointId = (endpoint) => (
  typeof endpoint === 'object' && endpoint !== null ? endpoint.id : endpoint
)

export default function GraphView({
  graphData,
  genreColorMap,
  selectedNode,
  setSelectedNode,
  searchQuery,
  trackSearchQuery,
  showLabels,
  graphRef: externalRef,
}) {
  const internalRef = useRef(null)
  const fgRef = externalRef || internalRef

  // Pre-compute radius scale for artist nodes (by popularity)
  const getArtistRadius = useCallback((node) => {
    const t = Math.max(0, Math.min(1, (node.popularityAvg - MIN_POP) / (MAX_POP - MIN_POP)))
    return ARTIST_NODE_RADIUS.min + t * (ARTIST_NODE_RADIUS.max - ARTIST_NODE_RADIUS.min)
  }, [])

  const getGenreRadius = useCallback((node) => {
    return GENRE_NODE_RADIUS.min
  }, [])

  const getTrackRadius = useCallback((node) => {
    const t = Math.max(0, Math.min(1, (node.popularity - MIN_POP) / (MAX_POP - MIN_POP)))
    return 2.5 + t * 4 // 2.5px to 6.5px based on popularity
  }, [])

  // Avoid cloning thousands of nodes/links on every graph update.
  const stableData = useMemo(() => graphData, [graphData])
  const selectedGraphContext = useMemo(() => {
    const relatedNodeIds = new Set()
    const relatedLinkIds = new Set()
    if (!selectedNode) return { relatedNodeIds, relatedLinkIds }

    relatedNodeIds.add(selectedNode.id)
    for (const link of stableData.links) {
      const sourceId = getLinkEndpointId(link.source)
      const targetId = getLinkEndpointId(link.target)
      const isDirect = sourceId === selectedNode.id || targetId === selectedNode.id
      const isSelectedArtistTrack =
        selectedNode.type === 'artist' &&
        link.type === 'track-link' &&
        sourceId === selectedNode.id

      if (isDirect || isSelectedArtistTrack) {
        relatedLinkIds.add(`${sourceId}->${targetId}`)
        relatedNodeIds.add(sourceId)
        relatedNodeIds.add(targetId)
      }
    }

    return { relatedNodeIds, relatedLinkIds }
  }, [selectedNode, stableData])

  useEffect(() => {
    const graph = fgRef.current
    if (!graph) return

    graph.d3Force('charge')?.strength(-14)
    graph.d3Force('link')?.distance((link) => (link.type === 'track-link' ? 14 : 34)).strength(0.28)
    graph.d3ReheatSimulation()
  }, [fgRef, stableData])

  useEffect(() => {
    if (selectedNode?.type !== 'track') return
    const graph = fgRef.current
    if (!graph) return

    const graphNode = stableData.nodes.find((node) => node.id === selectedNode.id)
    if (!graphNode || typeof graphNode.x !== 'number' || typeof graphNode.y !== 'number') return

    graph.centerAt(graphNode.x, graphNode.y, 600)
    graph.zoom(Math.max(graph.zoom(), 3), 600)
  }, [fgRef, selectedNode, stableData])

  const searchLower = searchQuery ? searchQuery.toLowerCase() : ''
  const trackSearchLower = trackSearchQuery ? trackSearchQuery.toLowerCase() : ''

  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const isGenre = node.type === 'genre'
      const isTrack = node.type === 'track'
      const displayLabel = isGenre ? displayGenreLabel(node.label) : node.label

      let color
      if (isGenre) {
        color = genreColorMap.get(node.label) || '#888'
      } else if (isTrack) {
        color = genreColorMap.get(node.genre) || '#1DB954'
      } else {
        color = genreColorMap.get(node.genres?.[0]) || '#6b7280'
      }

      const radius = isGenre ? getGenreRadius(node) : (isTrack ? getTrackRadius(node) : getArtistRadius(node))

      // Highlight logic
      const isSelected = selectedNode?.id === node.id
      const isRelatedToSelection = selectedGraphContext.relatedNodeIds.has(node.id)

      const hasArtistQuery = !!searchLower
      let isArtistMatch = false
      if (hasArtistQuery) {
        if (node.type === 'artist' || node.type === 'genre') {
          isArtistMatch = node.label.toLowerCase().includes(searchLower) ||
            (node.type === 'genre' && displayGenreLabel(node.label).toLowerCase().includes(searchLower))
        } else if (node.type === 'track') {
          isArtistMatch = node.label.toLowerCase().includes(searchLower) ||
                          (node.artistLabel && node.artistLabel.toLowerCase().includes(searchLower))
        }
      }

      const hasTrackQuery = !!trackSearchLower
      let isTrackMatch = false
      if (hasTrackQuery) {
        if (node.type === 'track') {
          isTrackMatch = node.label.toLowerCase().includes(trackSearchLower)
        } else if (node.type === 'artist') {
          isTrackMatch = node.topTracks?.some((t) => t.name.toLowerCase().includes(trackSearchLower))
        }
      }

      let isSearchMatch = false
      if (hasArtistQuery && hasTrackQuery) {
        isSearchMatch = isArtistMatch && isTrackMatch
      } else if (hasArtistQuery) {
        isSearchMatch = isArtistMatch
      } else if (hasTrackQuery) {
        isSearchMatch = isTrackMatch
      }

      const dimmed =
        ((hasArtistQuery || hasTrackQuery) && !isSearchMatch) ||
        (selectedNode && !isSelected && !isRelatedToSelection)

      ctx.save()

      // Glow for selected/matched
      if (isSelected || isSearchMatch || isRelatedToSelection) {
        ctx.shadowColor = color
        ctx.shadowBlur = isSelected || isSearchMatch ? 12 : 6
      }

      // Draw circle
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI)
      ctx.fillStyle = dimmed ? `${color}33` : color
      ctx.fill()

      if (isTrack) {
        // Draw the inner dot for vinyl disc look
        ctx.beginPath()
        ctx.arc(node.x, node.y, radius * 0.4, 0, 2 * Math.PI)
        ctx.fillStyle = dimmed ? 'rgba(255, 255, 255, 0.2)' : '#fff'
        ctx.fill()
      }

      if (isSelected || isSearchMatch || isRelatedToSelection) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = (isSelected || isSearchMatch ? 1.5 : 0.8) / globalScale
        ctx.stroke()
      }

      ctx.restore()

      // Labels
      const showLabel = showLabels
        ? isGenre || isSearchMatch || isSelected || (isTrack && globalScale > 2.5)
        : isSelected || isSearchMatch || (isGenre && globalScale > 1.5)

      if (showLabel) {
        const fontSize = isGenre
          ? Math.max(3, 10 / globalScale)
          : isTrack
            ? Math.max(2, 7.5 / globalScale)
            : Math.max(2.5, 8 / globalScale)

        ctx.save()
        ctx.font = `${isGenre ? 'bold ' : ''}${fontSize}px Inter, system-ui`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'

        const yOffset = radius + fontSize * 0.9

        // Text shadow for readability
        ctx.fillStyle = 'rgba(0,0,0,0.7)'
        ctx.fillText(displayLabel, node.x + 0.5, node.y + yOffset + 0.5)
        ctx.fillStyle = isGenre ? '#fff' : '#cbd5e1'
        ctx.fillText(displayLabel, node.x, node.y + yOffset)
        ctx.restore()
      }
    },
    [genreColorMap, selectedNode, selectedGraphContext, searchLower, trackSearchLower, showLabels, getArtistRadius, getGenreRadius, getTrackRadius]
  )

  const nodePointerAreaPaint = useCallback(
    (node, color, ctx) => {
      const isGenre = node.type === 'genre'
      const isTrack = node.type === 'track'
      const radius = isGenre ? getGenreRadius(node) : (isTrack ? getTrackRadius(node) : getArtistRadius(node))
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI)
      ctx.fillStyle = color
      ctx.fill()
    },
    [getArtistRadius, getGenreRadius, getTrackRadius]
  )

  const handleNodeClick = useCallback(
    (node) => {
      setSelectedNode((prev) => (prev?.id === node.id ? null : node))
    },
    [setSelectedNode]
  )

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null)
  }, [setSelectedNode])

  const nodeVal = useCallback((node) => {
    if (node.type === 'genre') return 6
    if (node.type === 'track') {
      const t = Math.max(0, Math.min(1, (node.popularity - MIN_POP) / (MAX_POP - MIN_POP)))
      return 0.5 + t * 1.5
    }
    const t = Math.max(0, Math.min(1, (node.popularityAvg - MIN_POP) / (MAX_POP - MIN_POP)))
    return 1 + t * 3
  }, [])

  // Link color: match source genre, or subtle green for track links
  const linkColor = useCallback(
    (link) => {
      const sourceId = getLinkEndpointId(link.source)
      const targetId = getLinkEndpointId(link.target)
      const isSelectedLink = selectedGraphContext.relatedLinkIds.has(`${sourceId}->${targetId}`)

      if (isSelectedLink) {
        if (link.type === 'track-link') return 'rgba(29, 185, 84, 0.85)'
        return 'rgba(255, 255, 255, 0.38)'
      }

      if (selectedNode) return 'rgba(255,255,255,0.025)'

      if (link.type === 'track-link') {
        return 'rgba(29, 185, 84, 0.08)' // faint Spotify green
      }
      const target = typeof link.target === 'object' ? link.target : null
      if (!target) return '#ffffff08'
      const color = genreColorMap.get(target.label) || '#ffffff'
      return `${color}18`
    },
    [genreColorMap, selectedNode, selectedGraphContext]
  )

  const linkWidth = useCallback(
    (link) => {
      const sourceId = getLinkEndpointId(link.source)
      const targetId = getLinkEndpointId(link.target)
      if (selectedGraphContext.relatedLinkIds.has(`${sourceId}->${targetId}`)) {
        return link.type === 'track-link' ? 1.2 : 0.9
      }
      if (link.type === 'track-link') return 0.2
      return 0.4
    },
    [selectedGraphContext]
  )

  return (
    <ForceGraph2D
      ref={fgRef}
      graphData={stableData}
      nodeCanvasObject={nodeCanvasObject}
      nodePointerAreaPaint={nodePointerAreaPaint}
      nodeVal={nodeVal}
      linkColor={linkColor}
      linkWidth={linkWidth}
      onNodeClick={handleNodeClick}
      onBackgroundClick={handleBackgroundClick}
      warmupTicks={0}
      cooldownTicks={55}
      cooldownTime={2200}
      d3AlphaDecay={0.075}
      d3VelocityDecay={0.7}
      backgroundColor="#0a0a0f"
      nodeRelSize={1}
      enableNodeDrag
      enableZoomInteraction
      minZoom={0.1}
      maxZoom={20}
    />
  )
}
