"""Monitor known sources and discover new official C1-01 calls/documents."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
import pathlib
import re
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "sources.json"
BASELINE_PATH = ROOT / "discovery-baseline.json"
USER_AGENT = "OpoPlan-C1-Official-Source-Monitor/2.0"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def plain(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def parse_catalog(body: str, base_url: str) -> list[dict]:
    pattern = re.compile(
        r'<div class="opposition[^>]*>.*?href="([^"]*id_emp=(\d+)[^"]*)".*?'
        r'<div class="title medium">(.*?)</div>',
        re.IGNORECASE | re.DOTALL,
    )
    results = []
    for relative_url, employment_id, title_fragment in pattern.findall(body):
        title = plain(title_fragment)
        if not re.search(r"\bC1[\s-]*01\b", title, re.IGNORECASE):
            continue
        results.append({
            "employmentId": int(employment_id),
            "title": title,
            "url": f"https://sede.gva.es/es/detall-ocupacio-publica?id_emp={employment_id}",
        })
    return results


def parse_stages(body: str, employment_id: int) -> list[dict]:
    pattern = re.compile(
        r'<p name="?(\d+)"? class="font-weight-bold">(.*?)</p>\s*'
        r'.*?<p class="fecha-etapa">.*?</span>\s*([^<]+)</p>',
        re.IGNORECASE | re.DOTALL,
    )
    stages = []
    for stage_id, title_fragment, published in pattern.findall(body):
        title = plain(title_fragment)
        if not re.search(
            r"cuestionario|qüestionari|plantilla\s+(?:de\s+)?(?:respuestas|respostes)",
            title,
            re.IGNORECASE,
        ):
            continue
        stages.append({
            "employmentId": employment_id,
            "stageId": int(stage_id),
            "title": title,
            "published": plain(published),
            "url": f"https://sede.gva.es/es/detall-ocupacio-publica?id_emp={employment_id}&id_etapa={stage_id}",
        })
    return stages


def parse_documents(body: str) -> list[str]:
    documents = set()
    for raw_url, label_fragment in re.findall(
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.IGNORECASE | re.DOTALL
    ):
        url = html.unescape(raw_url)
        label = plain(label_fragment)
        if not re.search(r"\.pdf(?:$|[?#])", url, re.IGNORECASE):
            continue
        if re.search(r"plantill|cuestion|examen|ejercici|BPR", url + " " + label, re.IGNORECASE):
            documents.add(url)
    return sorted(documents)


def discover(registry: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    calls_by_id: dict[int, dict] = {}
    for catalog in registry["discovery"]["catalogs"]:
        try:
            body = fetch(catalog["url"])
            for call in parse_catalog(body, catalog["url"]):
                calls_by_id[call["employmentId"]] = call
        except Exception as error:
            errors.append(f"catálogo {catalog['id']}: {error}")

    calls = sorted(calls_by_id.values(), key=lambda item: item["employmentId"])

    def inspect_call(call: dict) -> tuple[list[dict], list[str], list[str]]:
        local_errors: list[str] = []
        try:
            body = fetch(call["url"])
            stages = parse_stages(body, call["employmentId"])
        except Exception as error:
            return [], [], [f"convocatoria {call['employmentId']}: {error}"]
        documents: set[str] = set()
        for stage in stages:
            try:
                documents.update(parse_documents(fetch(stage["url"])))
            except Exception as error:
                local_errors.append(f"etapa {call['employmentId']}/{stage['stageId']}: {error}")
        return stages, sorted(documents), local_errors

    stages: list[dict] = []
    documents: set[str] = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for local_stages, local_documents, local_errors in executor.map(inspect_call, calls):
            stages.extend(local_stages)
            documents.update(local_documents)
            errors.extend(local_errors)

    snapshot = {
        "schemaVersion": 1,
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "calls": calls,
        "stages": sorted(stages, key=lambda item: (item["employmentId"], item["stageId"])),
        "documents": sorted(documents),
    }
    return snapshot, errors


def compare(snapshot: dict, baseline: dict) -> dict:
    known_calls = {item["employmentId"] for item in baseline.get("calls", [])}
    known_stages = {
        (item["employmentId"], item["stageId"], item["published"])
        for item in baseline.get("stages", [])
    }
    known_documents = set(baseline.get("documents", []))
    return {
        "calls": [item for item in snapshot["calls"] if item["employmentId"] not in known_calls],
        "stages": [
            item for item in snapshot["stages"]
            if (item["employmentId"], item["stageId"], item["published"]) not in known_stages
        ],
        "documents": [url for url in snapshot["documents"] if url not in known_documents],
    }


def check_known_sources(registry: dict) -> list[str]:
    failures = []
    for source in registry["sources"]:
        try:
            body = fetch(source["url"])
            if source["expectedText"].casefold() not in body.casefold():
                failures.append(f"{source['id']}: no aparece el marcador esperado")
        except Exception as error:
            failures.append(f"{source['id']}: {error}")
    return failures


def write_github_outputs(path: str | None, discoveries: dict, failures: list[str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as output:
        output.write(f"discoveries={'true' if any(discoveries.values()) else 'false'}\n")
        output.write(f"failures={'true' if failures else 'false'}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="discovery-report.json")
    parser.add_argument("--refresh-baseline", action="store_true")
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    source_failures = check_known_sources(registry)
    snapshot, discovery_failures = discover(registry)
    failures = source_failures + discovery_failures

    if args.refresh_baseline:
        if failures:
            for failure in failures:
                print(f"::warning::{failure}")
            print("No se actualiza la línea base porque la exploración quedó incompleta.")
            return 1
        BASELINE_PATH.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"Línea base actualizada: {len(snapshot['calls'])} convocatorias C1-01, "
            f"{len(snapshot['stages'])} etapas de examen y {len(snapshot['documents'])} documentos."
        )
        return 0

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    discoveries = compare(snapshot, baseline)
    report = {
        "checkedAt": snapshot["generatedAt"],
        "needsReview": any(discoveries.values()),
        "discoveries": discoveries,
        "failures": failures,
        "summary": {
            "catalogCalls": len(snapshot["calls"]),
            "examStages": len(snapshot["stages"]),
            "officialDocuments": len(snapshot["documents"]),
        },
    }
    pathlib.Path(args.report).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_github_outputs(args.github_output, discoveries, failures)

    for failure in failures:
        print(f"::warning::{failure}")
    if report["needsReview"]:
        print(
            "Novedades para revisión: "
            f"{len(discoveries['calls'])} convocatorias, "
            f"{len(discoveries['stages'])} etapas y {len(discoveries['documents'])} documentos."
        )
    else:
        print(
            f"Sin novedades: {len(snapshot['calls'])} convocatorias C1-01 y "
            f"{len(snapshot['documents'])} documentos oficiales rastreados."
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
