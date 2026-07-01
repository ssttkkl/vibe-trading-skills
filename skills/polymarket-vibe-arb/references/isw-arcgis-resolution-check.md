# ISW ArcGIS resolution check for Ukraine territorial-control markets

Use this when a Polymarket market resolves from the ISW Ukraine StoryMap rather than generic news. It is especially useful for tail-end markets where the rule names a specific point/icon (rail station, town, bridge) and specific ISW layers.

## Workflow

1. Pull the Gamma market by exact slug and read the full rule text.
   - Record the exact qualifying layers, deadline, persistence rule, fallback sources, and any “icon partly shaded” wording.
   - Do not rely on event title alone; sibling markets can share an event with different dates.
2. Open the ISW StoryMap item data:
   - StoryMap: `https://www.arcgis.com/sharing/rest/content/items/<story_item_id>/data?f=json`
   - The Ukraine map used by ISW is usually a `webmap` resource inside the StoryMap, not directly visible in the HTML.
3. Pull the webmap data:
   - `https://www.arcgis.com/sharing/rest/content/items/<webmap_item_id>/data?f=json`
   - Identify layer titles matching the rule, e.g. `Assessed Russian Control`, `Assessed Russian Advances in Ukraine`, `Assessed Russian Gains in the Past 24 Hours`, and any explicitly excluded layer such as `Assessed Russian Infiltration Areas`.
4. Geocode or otherwise identify the target point. For Ukrainian rail stations, OSM/Nominatim may work better with Ukrainian names than English transliterations.
5. Query each relevant FeatureServer layer at the target point:

```python
import requests
lon, lat = 37.7295666, 48.5120088  # example: Kostyantynivka station
url = "https://services5.arcgis.com/.../FeatureServer/<layer>"
params = {
    "f": "json",
    "geometry": f"{lon},{lat}",
    "geometryType": "esriGeometryPoint",
    "inSR": "4326",
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "*",
    "returnGeometry": "false",
    "resultRecordCount": 5,
}
print(requests.get(url + "/query", params=params, headers={"User-Agent": "Mozilla/5.0"}).json())
```

## Interpretation pitfalls

- A point query is strong evidence but not perfect when the rule says **any part of an icon** is shaded. Mention residual edge/icon overlap risk.
- If the rule requires a change to persist through the next full ISW update cycle, do not treat a temporary layer/glitch as final.
- ISW StoryMap often includes a finalized-status text node like `frontline geometry as of ... finalized`; quote it when available.
- `Infiltration Areas` frequently look scary but may be explicitly excluded from qualification.
- Gamma `endDate` can differ from the rule’s written deadline/time zone. For resolution reasoning, prioritize the rule text and flag the mismatch as a timing/UMA risk.

## Reporting shape

Return: rule summary → current CLOB bid/ask + executable depth → ISW finalized status + layer query results → main tail risks → recommendation by price band. For this user, emphasize NO/YES executable price, expected edge, settlement/UMA risk, and avoid mixing this with unrelated geopolitical commentary.
