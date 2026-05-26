import {
  schemeTableau10,
  schemePaired,
  schemeSet3,
  schemeDark2,
  schemeSet1,
  schemeSet2,
  schemeAccent,
} from 'd3-scale-chromatic'

// Build a palette of 114+ distinct colors by combining multiple d3 schemes
const buildPalette = () => {
  const schemes = [
    ...schemeTableau10,
    ...schemePaired,
    ...schemeSet3,
    ...schemeDark2,
    ...schemeSet1,
    ...schemeSet2,
    ...schemeAccent,
  ]
  // Deduplicate while preserving order
  const seen = new Set()
  const palette = []
  for (const c of schemes) {
    const key = c.toLowerCase()
    if (!seen.has(key)) {
      seen.add(key)
      palette.push(c)
    }
  }
  // If we still need more, generate HSL steps
  while (palette.length < 114) {
    const i = palette.length
    const h = Math.round((i * 137.508) % 360)
    const s = 65 + (i % 3) * 10
    const l = 45 + (i % 2) * 15
    palette.push(`hsl(${h},${s}%,${l}%)`)
  }
  return palette
}

const PALETTE = buildPalette()

// Map genre name → color deterministically (alphabetical index)
export const buildGenreColorMap = (genres) => {
  const sorted = [...genres].sort()
  const map = new Map()
  sorted.forEach((g, i) => {
    map.set(g, PALETTE[i % PALETTE.length])
  })
  return map
}

export const GENRE_NODE_RADIUS = { min: 12, max: 22 }
export const ARTIST_NODE_RADIUS = { min: 3, max: 9 }
