from __future__ import annotations

import argparse
import csv
import json
import math
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

OURAIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
OPENFLIGHTS_AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
OPENFLIGHTS_ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"

UF_REGION = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}


def download_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "DataGraph-Airports/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def haversine_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [a_lat, a_lon, b_lat, b_lon])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def clean(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    if value == r"\N":
        return ""
    return value.strip('"')


def read_ourairports() -> dict[str, dict]:
    text = download_text(OURAIRPORTS_URL)
    airports: dict[str, dict] = {}
    for row in csv.DictReader(text.splitlines()):
        if row.get("iso_country") != "BR":
            continue
        iata = clean(row.get("iata_code")).upper()
        if not iata:
            continue
        uf = clean(row.get("iso_region")).replace("BR-", "")
        airports[iata] = {
            "iata": iata,
            "icao": clean(row.get("gps_code")).upper(),
            "nome": clean(row.get("name")),
            "cidade": clean(row.get("municipality")) or clean(row.get("name")),
            "uf": uf,
            "regiao": UF_REGION.get(uf, "Brasil"),
            "lat": float(row.get("latitude_deg") or 0),
            "lon": float(row.get("longitude_deg") or 0),
            "tipo": clean(row.get("type")),
            "servico_regular": clean(row.get("scheduled_service")),
            "fonte": "OurAirports",
        }
    return airports


def read_openflights_airports() -> dict[str, dict]:
    text = download_text(OPENFLIGHTS_AIRPORTS_URL)
    airports: dict[str, dict] = {}
    for row in csv.reader(text.splitlines()):
        if len(row) < 8:
            continue
        country = clean(row[3])
        iata = clean(row[4]).upper()
        if country != "Brazil" or not iata:
            continue
        airports[iata] = {
            "nome": clean(row[1]),
            "cidade": clean(row[2]),
            "lat": float(row[6] or 0),
            "lon": float(row[7] or 0),
        }
    return airports


def read_openflights_routes(valid_iata: set[str]) -> Counter[tuple[str, str]]:
    text = download_text(OPENFLIGHTS_ROUTES_URL)
    routes: Counter[tuple[str, str]] = Counter()
    for row in csv.reader(text.splitlines()):
        if len(row) < 6:
            continue
        src = clean(row[2]).upper()
        dst = clean(row[4]).upper()
        if src in valid_iata and dst in valid_iata and src != dst:
            routes[tuple(sorted((src, dst)))] += 1
    return routes


def classify_edge(origin: str, dest: str, airports: dict[str, dict], degree: Counter[str]) -> str:
    same_region = airports[origin]["regiao"] == airports[dest]["regiao"]
    hub_cutoff = max(6, sorted(degree.values(), reverse=True)[min(9, len(degree) - 1)] if degree else 6)
    if degree[origin] >= hub_cutoff or degree[dest] >= hub_cutoff:
        return "hub"
    if same_region:
        return "regional"
    return "inter-regional"


def generate() -> tuple[list[dict], list[dict], dict]:
    airports = read_ourairports()
    openflights_airports = read_openflights_airports()

    for iata, data in openflights_airports.items():
        if iata not in airports:
            airports[iata] = {
                "iata": iata,
                "icao": "",
                "nome": data["nome"],
                "cidade": data["cidade"],
                "uf": "",
                "regiao": "Brasil",
                "lat": data["lat"],
                "lon": data["lon"],
                "tipo": "unknown",
                "servico_regular": "",
                "fonte": "OpenFlights",
            }

    route_counts = read_openflights_routes(set(airports))
    degree: Counter[str] = Counter()
    for origin, dest in route_counts:
        degree[origin] += 1
        degree[dest] += 1

    airport_rows = sorted(airports.values(), key=lambda item: (item["regiao"], item["uf"], item["iata"]))
    edge_rows = []
    for (origin, dest), frequency in sorted(route_counts.items()):
        a = airports[origin]
        b = airports[dest]
        distance = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
        tipo = classify_edge(origin, dest, airports, degree)
        edge_rows.append({
            "origem": origin,
            "destino": dest,
            "tipo_conexao": tipo,
            "justificativa": f"rota regular em base publica ({frequency} registro(s) OpenFlights)",
            "peso": round(distance, 1),
            "frequencia_estimada": frequency,
            "fonte": "OpenFlights routes + OurAirports airports",
        })

    meta = {
        "fontes": {
            "aeroportos": OURAIRPORTS_URL,
            "rotas": OPENFLIGHTS_ROUTES_URL,
            "aeroportos_rotas": OPENFLIGHTS_AIRPORTS_URL,
        },
        "observacao": (
            "OurAirports fornece cadastro e coordenadas de aerodromos. OpenFlights fornece rotas publicas "
            "historicas, usadas aqui como proxy de conexoes regulares sem chave de API paga."
        ),
        "aeroportos_brasil_com_iata": len(airport_rows),
        "conexoes_brasil": len(edge_rows),
    }
    return airport_rows, edge_rows, meta


def write_outputs(airport_rows: list[dict], edge_rows: list[dict], meta: dict) -> None:
    DATA.mkdir(exist_ok=True)

    with open(DATA / "aeroportos_data_real.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "iata", "cidade", "regiao", "uf", "nome", "icao", "lat", "lon", "tipo", "servico_regular", "fonte"
        ])
        writer.writeheader()
        writer.writerows(airport_rows)

    with open(DATA / "adjacencias_aeroportos_real.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "origem", "destino", "tipo_conexao", "justificativa", "peso", "frequencia_estimada", "fonte"
        ])
        writer.writeheader()
        writer.writerows(edge_rows)

    with open(DATA / "aeroportos_fontes_real.json", "w", encoding="utf-8") as file:
        json.dump(meta, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa bases publicas e gera a malha realista de aeroportos do Brasil.")
    parser.parse_args()
    airport_rows, edge_rows, meta = generate()
    write_outputs(airport_rows, edge_rows, meta)
    print(f"OK: {meta['aeroportos_brasil_com_iata']} aeroportos e {meta['conexoes_brasil']} conexoes gerados em data/*_real.*")


if __name__ == "__main__":
    main()
