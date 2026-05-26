import Papa from 'papaparse'

// Parse CSV in streaming mode, building artist/genre data structures
export const parseDataset = (url, onProgress) => {
  return new Promise((resolve, reject) => {
    // Accumulate: artistId → { popularity[], genres: Set, tracks: [{name, popularity}] }
    const artistMap = new Map()
    // genreId → { trackCount, totalPopularity }
    const genreMap = new Map()
    // artistId → genreId pair deduplication
    const pairSet = new Set()

    let rowCount = 0
    let totalBytes = 0

    Papa.parse(url, {
      download: true,
      header: true,
      skipEmptyLines: true,
      worker: false,
      chunk: (results, parser) => {
        for (const row of results.data) {
          rowCount++
          const rawArtists = row.artists || ''
          const genre = (row.track_genre || '').trim()
          const popularity = parseFloat(row.popularity) || 0
          const trackName = (row.track_name || '').trim()
          const trackId = row.track_id || ''

          if (!genre) continue

          // Split multi-artist entries (separated by ";")
          const artists = rawArtists
            .split(';')
            .map((a) => a.trim().replace(/^['"\[]+|['"\]]+$/g, ''))
            .filter(Boolean)

          // Update genre map
          if (!genreMap.has(genre)) {
            genreMap.set(genre, { trackCount: 0, totalPopularity: 0 })
          }
          const gd = genreMap.get(genre)
          gd.trackCount++
          gd.totalPopularity += popularity

          // Update artist map
          for (const artist of artists) {
            if (!artistMap.has(artist)) {
              artistMap.set(artist, {
                popularitySum: 0,
                trackCount: 0,
                genres: new Set(),
                topTracks: [],
              })
            }
            const ad = artistMap.get(artist)
            ad.popularitySum += popularity
            ad.trackCount++
            ad.genres.add(genre)

            // Keep up to 5 top tracks
            ad.topTracks.push({ name: trackName, popularity, id: trackId })
            if (ad.topTracks.length > 20) {
              ad.topTracks.sort((a, b) => b.popularity - a.popularity)
              ad.topTracks.length = 5
            }

            pairSet.add(`${artist}|||${genre}`)
          }
        }

        // Estimate progress via row count (dataset ~114k rows)
        totalBytes += results.data.length
        onProgress(Math.min(0.95, rowCount / 114000))
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
    activeGenres = null, // Set of genre names, null = all
  } = {}
) => {
  // Filter and rank artists
  let artists = Array.from(artistMap.entries())
    .map(([id, d]) => ({
      id: `artist:${id}`,
      rawId: id,
      type: 'artist',
      label: id,
      trackCount: d.trackCount,
      popularityAvg: d.trackCount > 0 ? d.popularitySum / d.trackCount : 0,
      genres: Array.from(d.genres),
      topTracks: d.topTracks.sort((a, b) => b.popularity - a.popularity).slice(0, 5),
      genreCount: d.genres.size,
    }))
    .filter((a) => a.trackCount >= minTracks)
    .filter((a) => a.popularityAvg >= minPopularity)
    .filter((a) => a.genreCount >= minGenreCount)

  // Apply genre filter if set
  if (activeGenres && activeGenres.size > 0) {
    artists = artists.filter((a) => a.genres.some((g) => activeGenres.has(g)))
  }

  // Limit by top popularity
  if (artists.length > maxArtists) {
    artists.sort((a, b) => b.popularityAvg - a.popularityAvg)
    artists = artists.slice(0, maxArtists)
  }

  const artistIdSet = new Set(artists.map((a) => a.id))

  // Build genre nodes only for genres that have at least one visible artist
  const visibleGenres = new Set()
  for (const artist of artists) {
    for (const g of artist.genres) {
      if (!activeGenres || activeGenres.has(g)) {
        visibleGenres.add(g)
      }
    }
  }

  const genres = Array.from(visibleGenres).map((g) => {
    const gd = genreMap.get(g) || { trackCount: 0, totalPopularity: 0 }
    return {
      id: `genre:${g}`,
      rawId: g,
      type: 'genre',
      label: g,
      trackCount: gd.trackCount,
      popularityAvg: gd.trackCount > 0 ? gd.totalPopularity / gd.trackCount : 0,
    }
  })

  const genreIdSet = new Set(genres.map((g) => g.id))

  // Build links
  const links = []
  for (const key of pairSet) {
    const [rawArtist, rawGenre] = key.split('|||')
    const artistId = `artist:${rawArtist}`
    const genreId = `genre:${rawGenre}`
    if (artistIdSet.has(artistId) && genreIdSet.has(genreId)) {
      if (!activeGenres || activeGenres.has(rawGenre)) {
        links.push({ source: artistId, target: genreId })
      }
    }
  }

  return {
    nodes: [...genres, ...artists],
    links,
  }
}
