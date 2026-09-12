import json
import pathlib
import sys
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
failures = []

for source in registry["sources"]:
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "OpoPlan-C1-Source-Monitor/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8", errors="replace")
        if source["expectedText"].casefold() not in text.casefold():
            failures.append(f"{source['id']}: no aparece el marcador esperado")
    except Exception as error:
        failures.append(f"{source['id']}: {error}")

if failures:
    for failure in failures:
        print(f"::warning::{failure}")
    print("Revisión humana necesaria; no se ha publicado contenido.")
    sys.exit(1)

print(f"{len(registry['sources'])} fuentes oficiales accesibles; sin incidencias estructurales.")
