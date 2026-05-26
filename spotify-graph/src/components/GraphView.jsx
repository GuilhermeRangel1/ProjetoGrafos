import { useRef, useCallback, useMemo, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { GENRE_NODE_RADIUS, ARTIST_NODE_RADIUS } from '../utils/colors'

const MIN_POP = 0
const MAX_POP = 100

export default function GraphView({
  graphData,
  genreColorMap,
  selectedNode,
  setSelectedNode,
  searchQuery,
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

  // Memoize data shape — ForceGraph re-runs simulation when this changes
  const stableData = useMemo(() => ({
    nodes: graphData.nodes.map((n) => ({ ...n })),
    links: graphData.links.map((l) => ({ ...l })),
  }), [graphData])

  const searchLower = searchQuery.toLowerCase()

  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const isGenre = node.type === 'genre'
      const color = isGenre
        ? genreColorMap.get(node.label) || '#888'
        : genreColorMap.get(node.genres?.[0]) || '#6b7280'

      const radius = isGenre ? getGenreRadius(node) : getArtistRadius(node)

      // Highlight logic
      const isSelected = selectedNode?.id === node.id
      const isSearchMatch =
        searchLower && node.label.toLowerCase().includes(searchLower)
      const dimmed =
        (searchLower && !isSearchMatch) ||
        (selectedNode && !isSelected)

      ctx.save()

      // Glow for selected/matched
      if (isSelected || isSearchMatch) {
        ctx.shadowColor = color
        ctx.shadowBlur = 12
      }

      // Draw circle
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI)
      ctx.fillStyle = dimmed ? `${color}33` : color
      ctx.fill()

      if (isSelected || isSearchMatch) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 1.5 / globalScale
        ctx.stroke()
      }

      ctx.restore()

      // Labels
      const showLabel = showLabels
        ? isGenre || isSearchMatch || isSelected
        : isSelected || isSearchMatch || (isGenre && globalScale > 1.5)

      if (showLabel) {
        const fontSize = isGenre
          ? Math.max(3, 10 / globalScale)
          : Math.max(2.5, 8 / globalScale)

        ctx.save()
        ctx.font = `${isGenre ? 'bold ' : ''}${fontSize}px Inter, system-ui`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'

        const yOffset = radius + fontSize * 0.9

        // Text shadow for readability
        ctx.fillStyle = 'rgba(0,0,0,0.7)'
        ctx.fillText(node.label, node.x + 0.5, node.y + yOffset + 0.5)
        ctx.fillStyle = isGenre ? '#fff' : '#cbd5e1'
        ctx.fillText(node.label, node.x, node.y + yOffset)
        ctx.restore()
      }
    },
    [genreColorMap, selectedNode, searchLower, showLabels, getArtistRadius, getGenreRadius]
  )

  const nodePointerAreaPaint = useCallback(
    (node, color, ctx) => {
      const isGenre = node.type === 'genre'
      const radius = isGenre ? getGenreRadius(node) : getArtistRadius(node)
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI)
      ctx.fillStyle = color
      ctx.fill()
    },
    [getArtistRadius, getGenreRadius]
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
    const t = Math.max(0, Math.min(1, (node.popularityAvg - MIN_POP) / (MAX_POP - MIN_POP)))
    return 1 + t * 3
  }, [])

  // Link color: match source genre
  const linkColor = useCallback(
    (link) => {
      const target = typeof link.target === 'object' ? link.target : null
      if (!target) return '#ffffff08'
      const color = genreColorMap.get(target.label) || '#ffffff'
      return `${color}18`
    },
    [genreColorMap]
  )

  return (
    <ForceGraph2D
      ref={fgRef}
      graphData={stableData}
      nodeCanvasObject={nodeCanvasObject}
      nodePointerAreaPaint={nodePointerAreaPaint}
      nodeVal={nodeVal}
      linkColor={linkColor}
      linkWidth={0.4}
      onNodeClick={handleNodeClick}
      onBackgroundClick={handleBackgroundClick}
      warmupTicks={0}
      cooldownTicks={150}
      cooldownTime={8000}
      d3AlphaDecay={0.03}
      d3VelocityDecay={0.5}
      backgroundColor="#0a0a0f"
      nodeRelSize={1}
      enableNodeDrag
      enableZoomInteraction
      minZoom={0.1}
      maxZoom={20}
    />
  )
}
