import Papa from 'papaparse'

const PINNED_ARTISTS = ['Billie Eilish']
const ESTIMATED_ROWS = 114000

const hashString = (value) => {
  let hash = 2166136261
  for (let i = 0; i < value.length; i++) {
    hash ^= value.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

const polarPoint = (angle, radius, center = { x: 0, y: 0 }) => ({
  x: center.x + Math.cos(angle) * radius,
  y: center.y + Math.sin(angle) * radius,
})

export const parseDataset = (url, onProgress) => {
  return new Promise((resolve, reject) => {
    const artistMap = new Map()
    const genreMap = new Map()
    const pairSet = new Set()
    let rowCount = 0

    onProgress(0.02)

    Papa.parse(`${url}?v=${Date.now()}`, {
      download: true,
      header: true,
      skipEmptyLines: true,
      worker: false,
      chunk: (results) => {
        for (const row of results.data) {
          rowCount++
          const rawArtists = row.artists || ''
          const genre = (row.track_genre || '').trim()
          const popularity = parseFloat(row.popularity) || 0
          const trackName = (row.track_name || '').trim()
          const trackId = row.track_id || ''

          if (!genre) continue

          const artists = rawArtists
            .split(';')
            .map((artist) => artist.trim().replace(/^['"\[]+|['"\]]+$/g, ''))
            .filter(Boolean)

          if (!genreMap.has(genre)) {
            genreMap.set(genre, { trackCount: 0, totalPopularity: 0 })
          }
          const genreData = genreMap.get(genre)
          genreData.trackCount++
          genreData.totalPopularity += popularity

          for (const artist of artists) {
            if (!artistMap.has(artist)) {
              artistMap.set(artist, {
                popularitySum: 0,
                trackCount: 0,
                genres: new Set(),
                topTracks: [],
              })
            }
            const artistData = artistMap.get(artist)
            artistData.popularitySum += popularity
            artistData.trackCount++
            artistData.genres.add(genre)
            artistData.topTracks.push({ name: trackName, popularity, id: trackId })

            if (artistData.topTracks.length > 120) {
              artistData.topTracks.sort((a, b) => b.popularity - a.popularity)
              artistData.topTracks.length = 80
            }

            pairSet.add(`${artist}|||${genre}`)
          }
        }

        onProgress(Math.min(0.97, 0.02 + (rowCount / ESTIMATED_ROWS) * 0.95))
      },
      complete: () => {
        if (rowCount === 0) {
          reject(new Error('dataset.csv not found or empty. Place the file at spotify-graph/public/dataset.csv'))
          return
        }
        onProgress(1)
        resolve({ artistMap, genreMap, pairSet })
      },
      error: (err) => reject(new Error(err.message || String(err))),
    })
  })
}

export const buildGraphData = (
  { artistMap, genreMap, pairSet },
  {
    minTracks = 3,
    maxArtists = 5000,
    minPopularity = 0,
    minGenreCount = 1,
    activeGenres = null,
    showTracks = false,
    tracksPerArtist = 1,
    maxTrackArtists = 250,
    trackSearchQuery = '',
    focusedArtistId = null,
    pinnedArtists = PINNED_ARTISTS,
  } = {}
) => {
  const normalizedTrackSearch = trackSearchQuery.trim().toLowerCase()

  let artists = Array.from(artistMap.entries())
    .map(([id, data]) => ({
      id: `artist:${id}`,
      rawId: id,
      type: 'artist',
      label: id,
      trackCount: data.trackCount,
      popularityAvg: data.trackCount > 0 ? data.popularitySum / data.trackCount : 0,
      genres: Array.from(data.genres),
      topTracks: data.topTracks.sort((a, b) => b.popularity - a.popularity),
      genreCount: data.genres.size,
      pinned: pinnedArtists.some((name) => id.toLowerCase() === name.toLowerCase()),
      hasTrackSearchMatch: normalizedTrackSearch
        ? data.topTracks.some((track) => track.name.toLowerCase().includes(normalizedTrackSearch))
        : false,
    }))
    .filter((artist) => artist.trackCount >= minTracks)
    .filter((artist) => artist.popularityAvg >= minPopularity)
    .filter((artist) => artist.genreCount >= minGenreCount)

  if (activeGenres && activeGenres.size > 0) {
    artists = artists.filter((artist) => artist.genres.some((genre) => activeGenres.has(genre)))
  }

  if (artists.length > maxArtists) {
    const pinned = artists.filter((artist) => artist.pinned || artist.hasTrackSearchMatch)
    const pinnedIds = new Set(pinned.map((artist) => artist.id))
    const ranked = artists
      .filter((artist) => !pinnedIds.has(artist.id))
      .sort((a, b) => b.popularityAvg - a.popularityAvg)
      .slice(0, Math.max(0, maxArtists - pinned.length))
    artists = [...pinned, ...ranked]
  }

  const artistIdSet = new Set(artists.map((artist) => artist.id))
  const visibleGenres = new Set()

  for (const artist of artists) {
    for (const genre of artist.genres) {
      if (!activeGenres || activeGenres.has(genre)) {
        visibleGenres.add(genre)
      }
    }
  }

  const orderedVisibleGenres = Array.from(visibleGenres).sort((a, b) => a.localeCompare(b))
  const genrePositionMap = new Map()
  const genreRadius = Math.max(480, Math.min(900, orderedVisibleGenres.length * 22))

  const genres = orderedVisibleGenres.map((genre, index) => {
    const genreData = genreMap.get(genre) || { trackCount: 0, totalPopularity: 0 }
    const angle = (index / Math.max(1, orderedVisibleGenres.length)) * Math.PI * 2 - Math.PI / 2
    const position = polarPoint(angle, genreRadius)
    genrePositionMap.set(genre, position)

    return {
      id: `genre:${genre}`,
      rawId: genre,
      type: 'genre',
      label: genre,
      trackCount: genreData.trackCount,
      popularityAvg: genreData.trackCount > 0 ? genreData.totalPopularity / genreData.trackCount : 0,
      x: position.x,
      y: position.y,
      fx: position.x,
      fy: position.y,
    }
  })

  const genreIdSet = new Set(genres.map((genre) => genre.id))

  artists = artists.map((artist) => {
    const primaryGenre = artist.genres.find((genre) => visibleGenres.has(genre)) || artist.genres[0]
    const base = genrePositionMap.get(primaryGenre) || { x: 0, y: 0 }
    const hash = hashString(artist.rawId)
    const angle = ((hash % 360) / 360) * Math.PI * 2
    const ring = 45 + ((Math.floor(hash / 360) % 8) * 24)
    const jitter = artist.pinned ? 0 : (hash % 17) - 8
    const position = polarPoint(angle, ring + jitter, base)

    return {
      ...artist,
      primaryGenre,
      x: position.x,
      y: position.y,
    }
  })

  const links = []
  for (const key of pairSet) {
    const [rawArtist, rawGenre] = key.split('|||')
    const artistId = `artist:${rawArtist}`
    const genreId = `genre:${rawGenre}`
    if (artistIdSet.has(artistId) && genreIdSet.has(genreId) && (!activeGenres || activeGenres.has(rawGenre))) {
      links.push({ source: artistId, target: genreId })
    }
  }

  const nodes = [...genres, ...artists]
  if (showTracks || normalizedTrackSearch || focusedArtistId) {
    const artistsWithTracks = artists
      .slice()
      .sort((a, b) => {
        if (a.id === focusedArtistId && b.id !== focusedArtistId) return -1
        if (a.id !== focusedArtistId && b.id === focusedArtistId) return 1
        if (a.hasTrackSearchMatch && !b.hasTrackSearchMatch) return -1
        if (!a.hasTrackSearchMatch && b.hasTrackSearchMatch) return 1
        if (a.pinned && !b.pinned) return -1
        if (!a.pinned && b.pinned) return 1
        return b.popularityAvg - a.popularityAvg
      })
      .filter((artist) => !focusedArtistId || showTracks || normalizedTrackSearch || artist.id === focusedArtistId)
      .slice(0, focusedArtistId ? Math.max(maxTrackArtists, 1) : (normalizedTrackSearch ? Math.max(maxTrackArtists, 500) : maxTrackArtists))

    for (const artist of artistsWithTracks) {
      if (!artist.topTracks) continue

      const seenTrackIds = new Set()
      const isFocusedArtist = artist.id === focusedArtistId
      const candidateTracks = normalizedTrackSearch
        ? artist.topTracks.filter((track) => track.name.toLowerCase().includes(normalizedTrackSearch))
        : artist.topTracks
      const tracksToShow = []

      for (const track of candidateTracks) {
        const dedupeKey = track.id || `${track.name}:${track.popularity}`
        if (seenTrackIds.has(dedupeKey)) continue
        seenTrackIds.add(dedupeKey)
        tracksToShow.push(track)
        if (!isFocusedArtist && tracksToShow.length >= (normalizedTrackSearch ? 40 : Math.max(1, tracksPerArtist))) break
      }

      for (const track of tracksToShow) {
        const trackNodeId = `track:${artist.id}:${track.id}`
        const trackAngle = ((hashString(trackNodeId) % 360) / 360) * Math.PI * 2
        const trackPosition = polarPoint(trackAngle, 22, artist)

        nodes.push({
          id: trackNodeId,
          rawId: track.id,
          type: 'track',
          label: track.name,
          popularity: track.popularity,
          spotifyUrl: `https://open.spotify.com/track/${track.id}`,
          artistId: artist.id,
          artistLabel: artist.label,
          genre: artist.genres?.[0] || '',
          x: trackPosition.x,
          y: trackPosition.y,
        })
        links.push({
          source: artist.id,
          target: trackNodeId,
          type: 'track-link',
        })
      }
    }
  }

  return {
    nodes,
    links,
  }
}
