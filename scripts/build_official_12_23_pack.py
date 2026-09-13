import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "tmp" / "pdfs" / "GVA-C1-01-12-23-es-ocr.txt"
OUTPUT = ROOT / "packs" / "gva-c1-01-12-23-v1.json"

answer_letters = (
    "CDDABCB CBA".replace(" ", "")
    + "DACBDDBBBA"
    + "DCBCDDDBBC"
    + "BCABBCACDC"
    + "DDBACBDC A C".replace(" ", "")
    + "BACDADACDA"
    + "BCCABABCCA"
    + "DCACBDABDC"
    + "BCCBCCBBAB"
)
if len(answer_letters) != 90:
    raise ValueError(f"La plantilla debe contener 90 respuestas, no {len(answer_letters)}")
answers = {number: ord(letter) - ord("A") for number, letter in enumerate(answer_letters, start=1)}


def topic(number):
    if number == 1 or number == 6:
        return "Parte especial", 1
    if number in {3, 4, 5, 7, 8, 9, 10}:
        return "Parte especial", 2
    if number in {2, 11, 12, 13, 14, 15}:
        return "Parte especial", 3
    if 16 <= number <= 17:
        return "Parte especial", 4
    if 18 <= number <= 21:
        return "Parte especial", 5
    if 22 <= number <= 25:
        return "Parte especial", 7
    if 26 <= number <= 31:
        return "Parte especial", 6
    if 32 <= number <= 34:
        return "Parte especial", 8
    if 35 <= number <= 37:
        return "Parte especial", 9
    if 38 <= number <= 42:
        return "Parte especial", 10
    if 43 <= number <= 50:
        return "Parte especial", 11
    if 51 <= number <= 54:
        return "Parte especial", 12
    if 55 <= number <= 56:
        return "Parte especial", 13
    if 57 <= number <= 59:
        return "Parte general", 1
    if 60 <= number <= 62:
        return "Parte general", 2
    if 63 <= number <= 65:
        return "Parte general", 3
    if number in {66, 67, 68, 70}:
        return "Parte general", 4
    if number in {69, 71}:
        return "Parte general", 5
    if 72 <= number <= 73:
        return "Parte general", 9
    if 74 <= number <= 78:
        return "Parte general", 6
    if 79 <= number <= 80:
        return "Parte general", 7
    if 81 <= number <= 82:
        return "Parte general", 8
    if 83 <= number <= 84:
        return "Parte general", 10
    if 85 <= number <= 86:
        return "Parte general", 11
    if 87 <= number <= 90:
        return "Parte general", 12
    raise ValueError(f"La pregunta {number} no tiene tema asignado")


text = SOURCE.read_text(encoding="utf-8")
text = re.sub(r"\bcorrecto\b", "CORRECTO", text, flags=re.IGNORECASE)
text = re.sub(r"\bincorrecto\b", "INCORRECTO", text, flags=re.IGNORECASE)
text = text.replace("título IIl", "título III").replace("sin qué en ningún caso", "sin que en ningún caso")

question_matches = list(re.finditer(r"(?m)^(\d{1,2})\s*\.\s*-\s*", text))
numbers = [int(match.group(1)) for match in question_matches]
if numbers != list(range(1, 91)):
    raise ValueError(f"Numeración inesperada: {numbers}")

questions = []
for index, match in enumerate(question_matches):
    number = int(match.group(1))
    end = question_matches[index + 1].start() if index + 1 < len(question_matches) else len(text)
    block = text[match.end():end]
    options = list(re.finditer(r"(?m)^\s*([ABCD])\)\s*", block))
    if [option.group(1) for option in options] != list("ABCD"):
        raise ValueError(f"Opciones inesperadas en la pregunta {number}")

    prompt = " ".join(block[:options[0].start()].split())
    values = []
    for option_index, option in enumerate(options):
        option_end = options[option_index + 1].start() if option_index + 1 < 4 else len(block)
        values.append(" ".join(block[option.end():option_end].split()))

    part, topic_number = topic(number)
    questions.append({
        "id": f"gva-c1-01-12-23-q{number:02d}",
        "part": part,
        "topicNumber": topic_number,
        "prompt": prompt,
        "options": values,
        "correctIndex": answers[number],
        "explanation": f"Respuesta {answer_letters[number - 1]} según la plantilla oficial publicada por la Generalitat Valenciana.",
        "isTheoreticalPractical": False,
    })

pack = {
    "schemaVersion": 1,
    "id": "gva-c1-01-12-23",
    "version": 1,
    "title": "Convocatoria 12/23 - ejercicio único",
    "origin": "official_exam",
    "sourceTitle": "Generalitat Valenciana - cuestionario y plantilla de la convocatoria 12/23, C1-01",
    "sourceURL": "https://www.gva.es/descarregues/2023/12/48690-PLANTILLA_Y_CUESTIONARIO_CONV._12_23_ADMON_GENERAL.pdf",
    "answerKeyURL": "https://www.gva.es/descarregues/2023/12/48690-PLANTILLA_Y_CUESTIONARIO_CONV._12_23_ADMON_GENERAL.pdf",
    "sourceLicense": "Documento público de la Generalitat Valenciana; fuente y fecha identificadas conforme a las condiciones de reutilización del sector público.",
    "sourcePublishedAt": "2023-12-18T00:00:00Z",
    "verifiedAt": "2026-09-13T00:00:00Z",
    "questions": questions,
}
OUTPUT.write_text(json.dumps(pack, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(f"Generado {OUTPUT} con {len(questions)} preguntas")
