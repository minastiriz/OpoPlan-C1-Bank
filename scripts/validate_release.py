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
    if not all(len(question["options"]) == 4 and 0 <= question["correctIndex"] < 4 for question in pack["questions"]):
        raise ValueError(f"Opciones inválidas: {filename}")

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
