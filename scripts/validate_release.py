import base64
import hashlib
import json
import pathlib
import os
import shutil
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
if manifest["schemaVersion"] != 1:
    raise ValueError("Versión de manifiesto no compatible")

all_question_ids = set()
total_questions = 0
expected_topics = (
    {("Parte general", number) for number in range(1, 13)}
    | {("Parte especial", number) for number in range(1, 24)}
)
topic_counts = {topic: 0 for topic in expected_topics}
for descriptor in manifest["packs"]:
    filename = pathlib.Path(descriptor["url"]).name
    path = ROOT / "packs" / filename
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != descriptor["sha256"]:
        raise ValueError(f"SHA-256 incorrecto: {filename}")

    pack = json.loads(data)
    if pack["id"] != descriptor["id"] or pack["version"] != descriptor["version"]:
        raise ValueError(f"Identidad/versión incorrecta: {filename}")
    if len(pack["questions"]) != descriptor["questionCount"]:
        raise ValueError(f"Número de preguntas incorrecto: {filename}")
    ids = [question["id"] for question in pack["questions"]]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Identificadores duplicados: {filename}")
    duplicated_across_packs = all_question_ids.intersection(ids)
    if duplicated_across_packs:
        raise ValueError(f"Identificadores repetidos entre paquetes: {sorted(duplicated_across_packs)}")
    all_question_ids.update(ids)
    total_questions += len(ids)
    if not all(len(question["options"]) == 4 and 0 <= question["correctIndex"] < 4 for question in pack["questions"]):
        raise ValueError(f"Opciones inválidas: {filename}")
    if not all(question["prompt"].strip() and all(option.strip() for option in question["options"]) for question in pack["questions"]):
        raise ValueError(f"Texto vacío: {filename}")
    if any("�" in question["prompt"] or any("�" in option for option in question["options"]) for question in pack["questions"]):
        raise ValueError(f"Caracteres de extracción dañados: {filename}")
    for question in pack["questions"]:
        topic = (question["part"], question["topicNumber"])
        if topic not in expected_topics:
            raise ValueError(f"Tema fuera del temario vigente en {filename}: {topic}")
        topic_counts[topic] += 1

    openssl = shutil.which("openssl")
    if openssl:
        with tempfile.NamedTemporaryFile() as signature_file:
            signature_file.write(base64.b64decode(descriptor["signature"]))
            signature_file.flush()
            subprocess.run(
                [openssl, "dgst", "-sha256", "-verify", str(ROOT / "public-key.pem"),
                 "-signature", signature_file.name, str(path)],
                check=True,
            )
    elif os.name == "nt":
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ROOT / "scripts" / "verify_signature.ps1"),
             "-DataPath", str(path), "-SignatureBase64", descriptor["signature"],
             "-PublicKeyPath", str(ROOT / "public-key.pem")],
            check=True,
        )
    else:
        raise RuntimeError("OpenSSL no está disponible para comprobar la firma")
    print(f"OK {filename}: {len(ids)} preguntas, SHA-256 y firma válidos")

if total_questions < 500:
    raise ValueError(f"El banco debe mantener al menos 500 preguntas revisadas; contiene {total_questions}")
missing_topics = [topic for topic, count in topic_counts.items() if count == 0]
if missing_topics:
    raise ValueError(f"Hay temas sin preguntas disponibles: {sorted(missing_topics)}")
low_coverage = sorted(
    ((part, number, count) for (part, number), count in topic_counts.items() if count < 5),
    key=lambda item: (item[0], item[1]),
)
print(f"OK banco completo: {total_questions} preguntas oficiales revisadas")
print(f"OK cobertura: {len(topic_counts)} temas con preguntas; cobertura baja (<5): {low_coverage}")
