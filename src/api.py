from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from graphs.algorithms import bfs, dfs
from analise_parte2 import carregar_dataset, amostrar, normalizar, dist_matrix, construir_grafo_knn

app = Flask(__name__)
CORS(app)

grafo_global = None
mapa_detalhes = {}
mapa_artista_para_tracks = {}
df_completo = None
sample_completo = None

def inicializar_dados():
    global grafo_global, mapa_detalhes, mapa_artista_para_tracks, df_completo, sample_completo
    print("Inicializando a API e carregando o dataset (isso pode levar alguns segundos)...")

    df_completo = carregar_dataset()
    sample_completo = amostrar(df_completo, 2000)
    nos = sample_completo["track_id"].tolist()

    for _, row in sample_completo.iterrows():
        tid = row["track_id"]
        artista = row.get("artists", "Desconhecido")
        nome = row.get("track_name", "Desconhecido")

        mapa_detalhes[tid] = {
            "id": tid,
            "name": nome,
            "artist": artista
        }

        artistas = [a.strip().strip("'").strip('"') for a in artista.split(';')]
        for a in artistas:
            if a not in mapa_artista_para_tracks:
                mapa_artista_para_tracks[a] = []
            mapa_artista_para_tracks[a].append(tid)

    print("Calculando distâncias e construindo grafo...")
    X_norm = normalizar(sample_completo)
    D = dist_matrix(X_norm.values)
    grafo_global = construir_grafo_knn(nos, D, K=10)
    print("Grafo construído com sucesso! API Pronta.")

@app.route('/api/playlist', methods=['GET'])
def gerar_playlist():
    seed = request.args.get('seed')
    algo = request.args.get('algorithm', 'bfs')

    if not seed:
        return jsonify({"error": "Seed não fornecido"}), 400

    origem = seed
    fallback_usado = False

    if origem not in mapa_detalhes:
        if origem in mapa_artista_para_tracks and len(mapa_artista_para_tracks[origem]) > 0:
            origem = mapa_artista_para_tracks[origem][0]
        else:
            track_row = df_completo[df_completo["track_id"] == seed]
            if not track_row.empty:
                genero = track_row.iloc[0]["track_genre"]
                mesmo_genero = sample_completo[sample_completo["track_genre"] == genero]
                if not mesmo_genero.empty:
                    origem = mesmo_genero.iloc[0]["track_id"]
                else:
                    import random
                    origem = random.choice(list(mapa_detalhes.keys()))
            else:
                import random
                origem = random.choice(list(mapa_detalhes.keys()))

            fallback_usado = True

    try:
        tamanho = 15

        if algo == 'bfs':
            ordem_visita, niveis, pais = bfs(grafo_global, origem)
        else:
            ordem_visita, ciclo, arestas = dfs(grafo_global, origem)

        playlist_ids = ordem_visita[:tamanho]
        playlist = [mapa_detalhes[tid] for tid in playlist_ids]

        return jsonify({
            "seed_utilizado": mapa_detalhes[origem],
            "fallback_usado": fallback_usado,
            "playlist": playlist
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    inicializar_dados()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
