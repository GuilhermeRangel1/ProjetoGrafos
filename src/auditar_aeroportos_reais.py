import csv
import math
from collections import defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def haversine(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_airports():
    path = DATA / "aeroportos_data_real.csv"
    airports = {}
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            iata = row["iata"].strip().upper()
            airports[iata] = row
    return airports


def load_edges():
    path = DATA / "adjacencias_aeroportos_real.csv"
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def connected_components(airports, edges):
    adj = defaultdict(set)
    for iata in airports:
        adj[iata]
    for edge in edges:
        adj[edge["origem"]].add(edge["destino"])
        adj[edge["destino"]].add(edge["origem"])

    seen = set()
    sizes = []
    for start in airports:
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        size = 0
        while queue:
            node = queue.popleft()
            size += 1
            for nxt in adj[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        sizes.append(size)
    return sorted(sizes, reverse=True), adj


def audit():
    airports = load_airports()
    edges = load_edges()
    airport_ids = set(airports)
    connected_airports = set()
    for edge in edges:
        connected_airports.add(edge["origem"].strip().upper())
        connected_airports.add(edge["destino"].strip().upper())

    missing_endpoints = []
    loops = []
    duplicate_keys = set()
    seen_keys = set()
    invalid_weights = []
    distance_mismatches = []
    suspicious_distances = []
    source_count_missing = []

    for edge in edges:
        origem = edge["origem"].strip().upper()
        destino = edge["destino"].strip().upper()
        key = tuple(sorted((origem, destino)))

        if origem not in airport_ids or destino not in airport_ids:
            missing_endpoints.append((origem, destino))
        if origem == destino:
            loops.append((origem, destino))
        if key in seen_keys:
            duplicate_keys.add(key)
        seen_keys.add(key)

        try:
            peso = float(edge["peso"])
        except ValueError:
            invalid_weights.append((origem, destino, edge["peso"]))
            continue

        if peso <= 0:
            invalid_weights.append((origem, destino, edge["peso"]))
        if peso < 25 or peso > 4000:
            suspicious_distances.append((origem, destino, peso))

        if origem in airport_ids and destino in airport_ids:
            a = airports[origem]
            b = airports[destino]
            calc = haversine(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))
            if abs(calc - peso) > 2.0:
                distance_mismatches.append((origem, destino, peso, round(calc, 1)))

        try:
            if int(edge.get("frequencia_estimada", "0")) <= 0:
                source_count_missing.append((origem, destino))
        except ValueError:
            source_count_missing.append((origem, destino))

    component_sizes, adj = connected_components(airports, edges)
    active_airports = {iata: airports[iata] for iata in connected_airports if iata in airports}
    active_component_sizes, _ = connected_components(active_airports, edges)
    isolated = [iata for iata, neighbors in adj.items() if not neighbors]

    for label, value in [
        ("aeroportos_cadastrados", len(airports)),
        ("aeroportos_na_malha_ativa", len(connected_airports)),
        ("aeroportos_descartados_por_grau_zero", len(airport_ids - connected_airports)),
        ("conexoes", len(edges)),
        ("componentes_cadastro_completo", len(component_sizes)),
        ("componentes_malha_ativa", len(active_component_sizes)),
        ("maior_componente_ativa", active_component_sizes[0] if active_component_sizes else 0),
        ("isolados_no_cadastro_completo", len(isolated)),
        ("endpoints_inexistentes", len(missing_endpoints)),
        ("auto_lacos", len(loops)),
        ("duplicatas_nao_direcionadas", len(duplicate_keys)),
        ("pesos_invalidos", len(invalid_weights)),
        ("distancias_suspeitas", len(suspicious_distances)),
        ("distancias_divergentes", len(distance_mismatches)),
        ("arestas_sem_contagem_fonte", len(source_count_missing)),
    ]:
        print(f"{label}: {value}")

    print("componentes_top5:", ", ".join(map(str, component_sizes[:5])))
    print("componentes_ativas_top5:", ", ".join(map(str, active_component_sizes[:5])))
    print("rec_vizinhos:", ", ".join(sorted(adj["REC"])))
    print("poa_vizinhos:", ", ".join(sorted(adj["POA"])))
    if suspicious_distances:
        sample = "; ".join(f"{a}-{b}:{d:.1f}" for a, b, d in suspicious_distances[:8])
        print("amostra_distancias_suspeitas:", sample)


if __name__ == "__main__":
    audit()
