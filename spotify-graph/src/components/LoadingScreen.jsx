export default function LoadingScreen({ progress, status, error }) {
  const pct = Math.round(progress * 100)
  const isStarting = pct === 0

  if (status === 'error') {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center z-50" style={{ background: 'linear-gradient(180deg, #10170f 0%, #182719 48%, #263a2a 100%)' }}>
        <div className="text-[#9f3442] text-xl font-semibold mb-2">Falha ao carregar o dataset</div>
        <div className="text-[#8a4150] text-sm">{error}</div>
        <div className="mt-4 text-[#d9cfad] text-xs">
          Verifique se <code className="bg-[#1f2d1e] px-1 rounded">public/dataset.csv</code> existe.
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center z-50" style={{ background: 'linear-gradient(180deg, #10170f 0%, #182719 48%, #263a2a 100%)' }}>
      <div className="mb-8">
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="32" fill="#5c9f79" opacity="0.18" />
          <circle cx="32" cy="32" r="20" stroke="#5c9f79" strokeWidth="2" fill="none" opacity="0.45" />
          <circle cx="32" cy="32" r="6" fill="#5c9f79" />
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const angle = (i / 6) * Math.PI * 2 - Math.PI / 2
            return (
              <line
                key={i}
                x1={32 + Math.cos(angle) * 9}
                y1={32 + Math.sin(angle) * 9}
                x2={32 + Math.cos(angle) * 18}
                y2={32 + Math.sin(angle) * 18}
                stroke="#5c9f79"
                strokeWidth="1.5"
                opacity="0.6"
              />
            )
          })}
        </svg>
      </div>

      <h1 className="text-2xl font-bold text-[#f7efcf] mb-1 tracking-tight">Grafo de artistas e gêneros do Spotify</h1>
      <p className="text-[#d9cfad] text-sm mb-8">
        {isStarting ? 'Preparando dataset...' : `Processando ${(114000).toLocaleString('pt-BR')} faixas...`}
      </p>

      <div className="w-72 bg-[#0e150f]/80 rounded-full h-2 overflow-hidden border border-[#c4b37e]/20">
        <div
          className={`h-full bg-[#5c9f79] rounded-full transition-all duration-200 ${
            isStarting ? 'animate-pulse' : ''
          }`}
          style={{ width: `${isStarting ? 12 : pct}%` }}
        />
      </div>
      <p className="text-[#a9a080] text-xs mt-3">{isStarting ? 'Iniciando...' : `${pct}%`}</p>
    </div>
  )
}
