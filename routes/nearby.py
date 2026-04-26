"""
routes/nearby.py — Find nearby hospitals and doctors via OpenStreetMap Overpass API
"""
import requests
from flask import Blueprint, g, jsonify, render_template, request
from routes.auth import login_required

nearby_bp = Blueprint("nearby", __name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Overpass QL query — finds hospitals, clinics, doctors within radius
OVERPASS_QUERY = """
[out:json][timeout:25];
(
  node["amenity"="hospital"](around:{radius},{lat},{lon});
  way["amenity"="hospital"](around:{radius},{lat},{lon});
  node["amenity"="clinic"](around:{radius},{lat},{lon});
  way["amenity"="clinic"](around:{radius},{lat},{lon});
  node["amenity"="doctors"](around:{radius},{lat},{lon});
  node["healthcare"="doctor"](around:{radius},{lat},{lon});
  node["healthcare"="hospital"](around:{radius},{lat},{lon});
  node["healthcare"="clinic"](around:{radius},{lat},{lon});
);
out center;
"""


def _parse_overpass(data, user_lat, user_lon):
    """Parse Overpass JSON into clean facility list with distance."""
    import math

    def _dist(lat1, lon1, lat2, lon2):
        R = 6371000  # metres
        φ1, φ2 = math.radians(lat1), math.radians(lat2)
        dφ = math.radians(lat2 - lat1)
        dλ = math.radians(lon2 - lon1)
        a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    results = []
    seen = set()
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or "Unnamed Facility"
        if name in seen:
            continue
        seen.add(name)

        # lat/lon
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if not lat or not lon:
            continue

        dist_m = _dist(user_lat, user_lon, lat, lon)
        amenity = tags.get("amenity") or tags.get("healthcare", "facility")
        kind_map = {
            "hospital": "🏥 Hospital",
            "clinic": "🏨 Clinic",
            "doctors": "👨‍⚕️ Doctor",
            "doctor": "👨‍⚕️ Doctor",
        }
        kind = kind_map.get(amenity, "🏥 Healthcare")

        results.append({
            "name": name,
            "kind": kind,
            "lat": lat,
            "lon": lon,
            "dist_m": round(dist_m),
            "dist_km": round(dist_m / 1000, 2),
            "phone": tags.get("phone") or tags.get("contact:phone", ""),
            "website": tags.get("website") or tags.get("contact:website", ""),
            "address": ", ".join(filter(None, [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:city", ""),
            ])) or tags.get("addr:full", ""),
            "emergency": tags.get("emergency") == "yes",
        })

    results.sort(key=lambda x: x["dist_m"])
    return results[:25]  # top 25 nearest


@nearby_bp.route("/nearby")
@login_required
def nearby_page():
    """Render the map page."""
    scheme_name = request.args.get("scheme", "")
    return render_template("nearby.html", scheme_name=scheme_name)


@nearby_bp.route("/api/nearby")
@login_required
def api_nearby():
    """
    Query Overpass API for hospitals/clinics near the given coordinates.
    GET /api/nearby?lat=17.38&lon=78.49&radius=5000
    """
    try:
        lat    = float(request.args.get("lat", 0))
        lon    = float(request.args.get("lon", 0))
        radius = min(int(request.args.get("radius", 5000)), 20000)  # max 20km
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates"}), 400

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return jsonify({"error": "Coordinates out of range"}), 400

    query = OVERPASS_QUERY.format(lat=lat, lon=lon, radius=radius)
    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=30,
            headers={"User-Agent": "SchemeMaxAI/1.0"}
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        return jsonify({"error": "Map service timed out. Please try again."}), 504
    except Exception as e:
        return jsonify({"error": f"Map service error: {str(e)[:80]}"}), 502

    facilities = _parse_overpass(data, lat, lon)
    return jsonify({"facilities": facilities, "count": len(facilities)})
