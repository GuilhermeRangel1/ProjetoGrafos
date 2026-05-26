export default function LoadingScreen({ progress, status, error }) {
  const pct = Math.round(progress * 100)

  if (status === 'error') {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center bg-[#0a0a0f] z-50">
        <div className="text-red-400 text-xl font-semibold mb-2">Failed to load dataset</div>
        <div className="text-red-300 text-sm">{error}</div>
        <div className="mt-4 text-slate-400 text-xs">
          Make sure <code className="bg-slate-800 px-1 rounded">public/dataset.csv</code> exists.
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-[#0a0a0f] z-50">
      {/* Spotify-ish logo mark */}
      <div className="mb-8">
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="32" fill="#1DB954" opacity="0.15" />
          <circle cx="32" cy="32" r="20" stroke="#1DB954" strokeWidth="2" fill="none" opacity="0.4" />
          <circle cx="32" cy="32" r="6" fill="#1DB954" />
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const angle = (i / 6) * Math.PI * 2 - Math.PI / 2
            return (
              <line
                key={i}
                x1={32 + Math.cos(angle) * 9}
                y1={32 + Math.sin(angle) * 9}
                x2={32 + Math.cos(angle) * 18}
                y2={32 + Math.sin(angle) * 18}
                stroke="#1DB954"
                strokeWidth="1.5"
                opacity="0.6"
              />
            )
          })}
        </svg>
      </div>

      <h1 className="text-2xl font-bold text-white mb-1 tracking-tight">Spotify Artist–Genre Graph</h1>
      <p className="text-slate-400 text-sm mb-8">Parsing {(114000).toLocaleString()} tracks…</p>

      {/* Progress bar */}
      <div className="w-72 bg-slate-800 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-[#1DB954] rounded-full transition-all duration-200"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-slate-500 text-xs mt-3">{pct}%</p>
    </div>
  )
}
