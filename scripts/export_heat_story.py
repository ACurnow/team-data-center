"""Export Warm Ishikari results and a hand-drawn base map for the interactive story page (web/heat_story).

Writes out/heat_story/story.json (scenarios, networks, monthly balances) and
out/heat_story/base.json: one array, one record per line (meta, sea, river, roads by class, coast,
city line, labels). Map coordinates are integers in 1e-4 degrees from the south-west corner of
`EXTENT`, delta-encoded along each line: [x0, y0, dx1, dy1, ...].
Run: uv run python scripts/export_heat_story.py
View locally: cp web/heat_story/index.html out/heat_story/ && python -m http.server -d out/heat_story
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox
from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import linemerge, nearest_points, split, unary_union

from dcopt.common.geo import load_graph, paths, use_overpass_mirror
from dcopt.heat.v1 import (JMA_SOURCE, KINDS, MONTHS_EN, MONTHS_JA, SNOW, TEMP, Assumptions,  # noqa: E402
                         design, ishikari_sites, pairwise, standalone_and_shared)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "heat_story"
VIEW = (141.265, 43.133, 141.405, 43.222)    # W, S, E, N: the network and its neighbours, always shown
EXTENT = (141.05, 43.00, 141.62, 43.34)      # drawn data, so wide or tall screens show real ground at the edges
SCALE = 10_000                               # 1e-4 degree units (about 8 m east-west, 11 m north-south here)
ASSUMED = {"new_greenhouse", "aquaculture", "snow"}
SCENARIOS = {
    "base": ("標準の前提（IT負荷10MW）", "Base case (10 MW IT load)", Assumptions(), True),
    "half": ("廃熱が半分（IT負荷5MW）", "Half the waste heat (5 MW)", Assumptions(it_load_mw=5), True),
    "existing": ("既存の施設だけ", "Existing sites only", Assumptions(), False),
    "cautious": ("慎重な前提（導管15万円/m・灯油95円/L）", "Cautious (pipes 150k yen/m, kerosene 95 yen/L)",
                 Assumptions(pipe_yen_m=150_000, kerosene_yen_l=95), True),
}
# District labels: centroid of the OSM place nodes whose name starts with the prefix.
DISTRICTS = [("花川", "花川", "Hanakawa"), ("樽川", "樽川", "Tarukawa"), ("花畔", "花畔", "Banaguro"),
             ("緑苑台", "緑苑台", "Ryokuendai"), ("新港", "石狩湾新港", "Ishikari Bay New Port"),
             ("八幡町", "八幡", "Hachiman"), ("生振", "生振", "Oyafuru")]
TOWNS = [(("屯田", "新琴似", "篠路", "太平", "あいの里", "新川", "百合が原"), "札幌市", "Sapporo"),
         (("太美", "当別太", "スウェーデンヒルズ", "ビトエ", "獅子内"), "当別町", "Tobetsu"),
         (("銭函",), "小樽市", "Otaru")]


def osm_settings() -> None:
    use_overpass_mirror()


def r5(x: float) -> float:
    return round(float(x), 5)


def enc(coords) -> list[int] | None:
    """Delta-encode one line or ring in 1e-4 degree units; None when it collapses to a point."""
    pts, last = [], None
    for x, y in coords:
        p = (round((x - EXTENT[0]) * SCALE), round((y - EXTENT[1]) * SCALE))
        if p != last:
            pts.append(p)
            last = p
    if len(pts) < 2:
        return None
    out = [pts[0][0], pts[0][1]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += [x1 - x0, y1 - y0]
    return out


def lines_of(geom) -> list:
    if geom.is_empty:
        return []
    if geom.geom_type in ("LineString", "LinearRing"):
        return [geom.coords]
    if geom.geom_type == "Polygon":
        return [geom.exterior.coords] + [r.coords for r in geom.interiors]
    if geom.geom_type in ("MultiLineString", "MultiPolygon", "GeometryCollection"):
        return [c for g in geom.geoms for c in lines_of(g)]
    return []


def encode_all(geom, tol: float) -> list[list[int]]:
    return [e for c in lines_of(geom.simplify(tol)) if (e := enc(c))]


def export_design(d) -> dict:
    adj: dict[int, list[int]] = {}
    for a, b, _ in d.edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    parent, order = {0: None}, [0]
    for n in order:                                   # orient pipes from the data center outward
        for nb in adj.get(n, []):
            if nb not in parent:
                parent[nb] = n
                order.append(nb)
    pipes = []
    for a, b, metres in d.edges:
        path = d.paths[a, b]                          # (lat, lon) from a to b
        if parent.get(a) == b:
            path = list(reversed(path))
        if len(path) < 2:                             # two sites on the same road node: nothing to draw
            path = list(path) * 2
        line = LineString([(lon, lat) for lat, lon in path]).simplify(0.00003)
        pipes.append({"path": [[r5(x), r5(y)] for x, y in line.coords], "km": round(metres / 1000, 2),
                      "flow": round(d.edge_flow.get((a, b), 0.0)),
                      "monthly": [round(v) for v in d.edge_flow_month.get((a, b), [0.0] * 12)]})
    A = d.A
    return {
        "connected": [d.sites[i].key for i in d.connected],
        "served": {d.sites[i].key: [round(v) for v in d.served[i]] for i in d.connected},
        "pipes": pipes,
        "supply": [round(w / (1 - 1 / A.cop)) for w in d.waste_heat],
        "kpi": {"users": len(d.connected), "delivered": round(d.delivered), "pipe_km": round(d.pipe_m / 1000, 1),
                "capex_oku": round(d.capex / 1e8, 1), "net_m": round(d.annual_net / 1e6, 1),
                "payback": round(d.payback_years, 1) if np.isfinite(d.payback_years) else None,
                "co2_t": round(d.co2_t), "heat_used": round(float(sum(d.supply_used) / sum(d.waste_heat)), 3)},
    }


def base_map() -> list[dict]:
    osm_settings()
    ext, view = box(*EXTENT), box(*VIEW)
    records: list[dict] = [{"layer": "meta", "view": VIEW, "extent": EXTENT, "scale": SCALE,
                            "note": "OpenStreetMap contributors (ODbL); integers in 1e-4 degrees from the "
                                    "extent's south-west corner, delta-encoded along each line"}]
    water = ox.features_from_bbox(bbox=EXTENT, tags={"natural": ["water", "coastline"]}).reset_index()
    sea = None
    coast_lines = [g for g in water.geometry if g.geom_type == "LineString"]
    coast = linemerge(coast_lines) if coast_lines else None
    if coast is not None:
        parts = split(ext, coast.intersection(ext.buffer(0.05)))
        bay = Point(141.22, 43.26)
        sea_parts = [g for g in getattr(parts, "geoms", [parts]) if g.contains(bay)]
        sea = unary_union(sea_parts) if sea_parts else None
        records.append({"layer": "sea", "rings": encode_all(sea, 0.0001) if sea else []})
        records.append({"layer": "coast", "lines": encode_all(coast.intersection(ext), 0.00005)})
    polys = water[water.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].to_crs(6680)
    polys = polys[polys.geometry.area > 2000].to_crs(4326)          # ponds under 0.2 ha are dropped
    river = unary_union(list(polys.geometry)).intersection(ext)
    records.append({"layer": "river", "rings": encode_all(river, 0.0001)})
    G = load_graph("ishikari")
    keep = {"motorway": 4, "trunk": 3, "primary": 3, "secondary": 2, "tertiary": 2, "unclassified": 1,
            "residential": 0}
    roads: dict[int, list] = {k: [] for k in range(5)}
    for u, v, data in G.edges(data=True):
        hwy = data.get("highway")
        hwy = hwy[0] if isinstance(hwy, list) else hwy
        if hwy not in keep:
            continue
        geom = data.get("geometry") or LineString([(G.nodes[u]["x"], G.nodes[u]["y"]),
                                                   (G.nodes[v]["x"], G.nodes[v]["y"])])
        roads[keep[hwy]].append(geom)
    for k, geoms in roads.items():
        merged = linemerge(MultiLineString(geoms)).intersection(ext)
        records.append({"layer": "road", "class": k, "lines": encode_all(merged, 0.00008 if k == 0 else 0.00005)})
    city = gpd.read_file(paths("ishikari")["boundary"]).geometry.iloc[0]
    line = city.boundary.intersection(box(EXTENT[0], EXTENT[1], EXTENT[2], 43.295))   # not the 43.30 clip
    if sea is not None:
        line = line.difference(sea.buffer(0.001))                                       # not the offshore part
    records.append({"layer": "city", "lines": encode_all(line, 0.0001)})
    places = ox.features_from_bbox(bbox=EXTENT, tags={"place": ["suburb", "quarter", "neighbourhood"]}).reset_index()
    places = places[(places.element == "node") & places["name"].notna()]
    labels = []
    for prefix, ja, en in DISTRICTS:
        hit = places[places["name"].str.startswith(prefix)]
        if len(hit):
            labels.append({"layer": "label", "kind": "district", "ja": ja, "en": en,
                           "lon": r5(hit.geometry.x.mean()), "lat": r5(hit.geometry.y.mean())})
    for prefixes, ja, en in TOWNS:
        hit = places[places["name"].str.startswith(prefixes)]
        inside = hit[hit.geometry.within(view)]
        hit = inside if len(inside) else hit           # outside the view: shown only on wide screens
        if len(hit):
            labels.append({"layer": "label", "kind": "town", "ja": ja, "en": en,
                           "lon": r5(hit.geometry.x.mean()), "lat": r5(hit.geometry.y.mean())})
    big = max(getattr(river, "geoms", [river]), key=lambda g: g.area)     # the Ishikari River itself
    on_river = nearest_points(big, Point(141.395, 43.215))[0]
    labels.append({"layer": "label", "kind": "water", "ja": "石狩川", "en": "Ishikari River",
                   "lon": r5(on_river.x), "lat": r5(on_river.y)})
    if sea is not None:
        at = sea.intersection(view.buffer(-0.004)).representative_point()
        labels.append({"layer": "label", "kind": "sea", "ja": "石狩湾", "en": "Ishikari Bay",
                       "lon": r5(at.x), "lat": r5(at.y)})
    return records + labels


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dc, sites = ishikari_sites()
    story = {
        "view": VIEW,
        "months": {"ja": MONTHS_JA, "en": MONTHS_EN},
        "climate": {"temp": TEMP, "snow": SNOW, "source": JMA_SOURCE},
        "kinds": {k: {"ja": v[0], "en": v[1]} for k, v in KINDS.items()},
        "dc": {"name": dc.name, "name_en": dc.name_en, "lon": r5(dc.lon), "lat": r5(dc.lat)},
        "sites": [{"id": s.key, "name": s.name, "name_en": s.name_en, "kind": s.kind, "lon": r5(s.lon),
                   "lat": r5(s.lat), "annual": round(s.annual_mwh), "monthly": [round(v) for v in s.monthly()],
                   "assumed": s.kind in ASSUMED, "source": s.source} for s in sites],
        "scenarios": {},
    }
    for key, (ja, en, A, assumed) in SCENARIOS.items():
        kinds = set(KINDS) if assumed else set(KINDS) - ASSUMED
        opt = design(dc, sites, A, k=3, kinds=kinds, time_limit=60)
        pw = pairwise(dc, sites, A, kinds=kinds)
        flips = [{"id": r["site"].key, "alone": round(r["alone"] / 1e4), "shared": round(r["shared"] / 1e4),
                  "own_km": round(r["own_pipe_m"] / 1000, 1)}
                 for r in standalone_and_shared(opt, dc) if r["connected"]]
        story["scenarios"][key] = {
            "label": {"ja": ja, "en": en}, "kinds": sorted(kinds),
            "assumptions": {"it_mw": A.it_load_mw, "recovery": A.recovery, "cop": A.cop, "kerosene": A.kerosene_yen_l,
                            "power": A.power_yen_kwh, "pipe_man_per_m": A.pipe_yen_m / 1e4, "years": A.years,
                            "rate": A.rate, "value_per_mwh": round(A.value_yen_per_mwh),
                            "co2_per_mwh": round(A.co2_t_per_mwh, 3)},
            "opt": export_design(opt), "pairs": export_design(pw), "flips": flips,
            "solve_s": round(opt.seconds, 1), "status": opt.status.split(".")[0],
        }
        sc = story["scenarios"][key]
        print(f"{key}: opt {sc['opt']['kpi']} | pairs {sc['pairs']['kpi']} | {sc['status']} in {sc['solve_s']} s")
        print("   kinds connected:", sorted({s.kind for s in opt.sites if s.key in sc['opt']['connected']}))
    (OUT / "story.json").write_text(json.dumps(story, ensure_ascii=False, separators=(",", ":")))
    records = base_map()
    (OUT / "base.json").write_text("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":"))
                                                      for r in records) + "\n]\n")
    for f in ("story.json", "base.json"):
        print(f, f"{(OUT / f).stat().st_size / 1e6:.2f} MB")
    print("labels:", [(r["ja"], r["lon"], r["lat"]) for r in records if r["layer"] == "label"])


if __name__ == "__main__":
    main()
