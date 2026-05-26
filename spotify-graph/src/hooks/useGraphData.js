import { useState, useEffect, useMemo, useCallback } from 'react'
import { parseDataset, buildGraphData } from '../utils/dataProcessor'
import { buildGenreColorMap } from '../utils/colors'

export const useGraphData = () => {
  const [rawData, setRawData] = useState(null)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [loadingStatus, setLoadingStatus] = useState('idle') // idle | loading | done | error
  const [error, setError] = useState(null)

  // Filter state
  const [minPopularity, setMinPopularity] = useState(0)
  const [minGenreCount, setMinGenreCount] = useState(1)
  const [activeGenres, setActiveGenres] = useState(null) // null = all
  const [maxArtists, setMaxArtists] = useState(2000)

  const load = useCallback(async () => {
    setLoadingStatus('loading')
    setLoadingProgress(0)
    try {
      const data = await parseDataset('/dataset.csv', setLoadingProgress)
      setRawData(data)
      setLoadingStatus('done')
    } catch (e) {
      setError(e.message || 'Failed to load dataset')
      setLoadingStatus('error')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // All genre names (sorted)
  const allGenres = useMemo(() => {
    if (!rawData) return []
    return Array.from(rawData.genreMap.keys()).sort()
  }, [rawData])

  // Color map (stable across re-renders)
  const genreColorMap = useMemo(() => {
    if (allGenres.length === 0) return new Map()
    return buildGenreColorMap(allGenres)
  }, [allGenres])

  // Derived graph data
  const graphData = useMemo(() => {
    if (!rawData) return { nodes: [], links: [] }
    return buildGraphData(rawData, {
      minTracks: 3,
      maxArtists,
      minPopularity,
      minGenreCount,
      activeGenres: activeGenres && activeGenres.size > 0 ? activeGenres : null,
    })
  }, [rawData, minPopularity, minGenreCount, activeGenres, maxArtists])

  return {
    graphData,
    genreColorMap,
    allGenres,
    loadingProgress,
    loadingStatus,
    error,
    // filter controls
    minPopularity,
    setMinPopularity,
    minGenreCount,
    setMinGenreCount,
    activeGenres,
    setActiveGenres,
    maxArtists,
    setMaxArtists,
  }
}
