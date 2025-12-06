from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime


def _remove_accents(s: str) -> str:
    import unicodedata
    if not isinstance(s, str):
        return s
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def _geojson_centroid(feature):
    geom = feature.get('geometry') or {}
    gtype = geom.get('type')
    coords = []
    if gtype == 'Polygon':
        for ring in geom.get('coordinates', []):
            for lon, lat in ring:
                coords.append((lat, lon))
    elif gtype == 'MultiPolygon':
        for poly in geom.get('coordinates', []):
            for ring in poly:
                for lon, lat in ring:
                    coords.append((lat, lon))
    if not coords:
        return None, None
    avg_lat = sum([c[0] for c in coords]) / len(coords)
    avg_lon = sum([c[1] for c in coords]) / len(coords)
    return avg_lat, avg_lon


def sync_bairros_from_geojson(geojson_path: Path, bairros_csv: Path, audit_csv: Path = None):
    """Sincroniza features do GeoJSON para um CSV de bairros.

    - Valida que cada feature tenha um nome em properties (EBAIRRNOME/NAME/bairro/nome).
      The top-level feature 'id' is optional; when missing we prefer using properties['OBJECTID']
      or leave as None. This makes the sync tolerant to GeoJSON produced without top-level ids.
    - Adiciona bairros ausentes com valores padrão.
    - Atualiza centroides quando divergentes.
    - Registra ações no arquivo de auditoria (CSV) se fornecido.
    """
    if not geojson_path.exists():
        raise FileNotFoundError(f"GeoJSON não encontrado: {geojson_path}")

    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    features = data.get('features', [])
    # validate (require name; id is optional)
    bad = []
    extracted = []
    for feat in features:
        props = feat.get('properties', {}) or {}
        # prefer explicit bairro name fields used in the Recife GeoJSON
        name = props.get('EBAIRRNOME') or props.get('EBAIRRNOMEOF') or props.get('NAME') or props.get('bairro') or props.get('nome')
        if not name:
            bad.append({'id': feat.get('id'), 'name': name, 'properties': props})
            continue

        # feature id is optional; if missing try OBJECTID from properties
        fid = feat.get('id')
        if fid is None:
            fid = props.get('OBJECTID') if props.get('OBJECTID') is not None else None

        lat, lon = _geojson_centroid(feat)
        extracted.append({'id': fid, 'bairro': str(name).strip(), 'lat_centroid': lat, 'lon_centroid': lon})

    if bad:
        # Abort and raise so the caller can log and stop the app; report only missing names
        raise ValueError(f"GeoJSON validation failed: {len(bad)} features missing name. Example: {bad[:3]}")

    df_geo = pd.DataFrame(extracted)
    df_geo['bairro_upper'] = df_geo['bairro'].str.strip().map(lambda x: _remove_accents(x).upper())

    if bairros_csv.exists():
        df_db = pd.read_csv(bairros_csv)
    else:
        df_db = pd.DataFrame(columns=['id', 'bairro', 'lat_centroid', 'lon_centroid', 'vulnerabilidade', 'has_precip_data', 'source'])

    # normalize existing
    if 'bairro' in df_db.columns:
        df_db['bairro_upper'] = df_db['bairro'].astype(str).map(lambda x: _remove_accents(x).upper())
    else:
        df_db['bairro'] = ''
        df_db['bairro_upper'] = ''

    now = datetime.utcnow().isoformat()
    audit_rows = []

    # Add or update
    for _, row in df_geo.iterrows():
        match = df_db[df_db['bairro_upper'] == row['bairro_upper']]
        if match.empty:
            new = {
                'id': row['id'],
                'bairro': row['bairro'],
                'lat_centroid': row['lat_centroid'],
                'lon_centroid': row['lon_centroid'],
                'vulnerabilidade': np.nan,
                'has_precip_data': False,
                'source': 'geojson-sync'
            }
            df_db = pd.concat([df_db, pd.DataFrame([new])], ignore_index=True)
            audit_rows.append({'timestamp': now, 'action': 'add_bairro', 'bairro': row['bairro'], 'note': 'added from geojson'})
        else:
            idx = match.index[0]
            changed = False
            # update lat/lon if diverged
            try:
                old_lat = float(df_db.at[idx, 'lat_centroid']) if pd.notna(df_db.at[idx, 'lat_centroid']) else None
            except Exception:
                old_lat = None
            try:
                old_lon = float(df_db.at[idx, 'lon_centroid']) if pd.notna(df_db.at[idx, 'lon_centroid']) else None
            except Exception:
                old_lon = None
            if (old_lat != row['lat_centroid']) or (old_lon != row['lon_centroid']):
                df_db.at[idx, 'lat_centroid'] = row['lat_centroid']
                df_db.at[idx, 'lon_centroid'] = row['lon_centroid']
                df_db.at[idx, 'source'] = 'geojson-sync'
                changed = True
            if changed:
                audit_rows.append({'timestamp': now, 'action': 'update_centroid', 'bairro': row['bairro'], 'note': 'centroid updated from geojson'})

    # cleanup helper column
    if 'bairro_upper' in df_db.columns:
        df_db = df_db.drop(columns=['bairro_upper'])

    # persist
    bairros_csv.parent.mkdir(parents=True, exist_ok=True)
    df_db.to_csv(bairros_csv, index=False)

    # write audit CSV
    if audit_csv:
        audit_csv.parent.mkdir(parents=True, exist_ok=True)
        df_audit = pd.DataFrame(audit_rows)
        if audit_csv.exists():
            df_prev = pd.read_csv(audit_csv)
            df_out = pd.concat([df_prev, df_audit], ignore_index=True)
        else:
            df_out = df_audit
        df_out.to_csv(audit_csv, index=False)

    return True
