import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "tmp" / "pdfs" / "EXAMEN_C1_CAST.txt"
KEY = ROOT.parent / "tmp" / "pdfs" / "PLANTILLA-respuesta_C1.txt"
OUTPUT = ROOT / "packs" / "gva-c1-01-edu-23-v1.json"

text = SOURCE.read_text(encoding="utf-8").replace("\\n", "\n")
answer_text = KEY.read_text(encoding="utf-8")
answers = {int(number): ord(letter) - ord("A") for number, letter in re.findall(r"(\d+)\s+([ABCD])", answer_text)}

question_matches = list(re.finditer(r"(?m)^(\d+)\.\s+", text))
topic_map = {
    **{n: ("Parte general", 3) for n in range(1, 7)},
    **{n: ("Parte general", 6) for n in range(7, 13)},
    13: ("Parte especial", 1), 14: ("Parte especial", 3), 15: ("Parte especial", 3),
    16: ("Parte especial", 3), 17: ("Parte especial", 1), 18: ("Parte especial", 3),
    19: ("Parte especial", 1), 20: ("Parte especial", 1), 21: ("Parte especial", 1),
    22: ("Parte especial", 1),
    **{n: ("Parte especial", 9) for n in range(23, 29)},
    **{n: ("Parte especial", 10) for n in range(29, 33)},
    33: ("Parte general", 10), 34: ("Parte general", 10),
    **{n: ("Parte especial", 19) for n in range(35, 39)},
    39: ("Parte especial", 18), 40: ("Parte especial", 18),
}

questions = []
for index, match in enumerate(question_matches):
    number = int(match.group(1))
    if not 1 <= number <= 40:
        continue
    end = question_matches[index + 1].start() if index + 1 < len(question_matches) else len(text)
    block = text[match.end():end]
    options = list(re.finditer(r"(?m)^([ABCD])\)\s+", block))
    if len(options) != 4:
        raise ValueError(f"La pregunta {number} tiene {len(options)} opciones")
    prompt = " ".join(block[:options[0].start()].split())
    values = []
    for option_index, option in enumerate(options):
        option_end = options[option_index + 1].start() if option_index + 1 < 4 else len(block)
        value = " ".join(block[option.end():option_end].split())
        value = re.sub(r"\s+\d+$", "", value)
        values.append(value)
    part, topic = topic_map[number]
    questions.append({
        "id": f"gva-c1-01-edu-23-q{number:02d}",
        "part": part,
        "topicNumber": topic,
        "prompt": prompt,
        "options": values,
        "correctIndex": answers[number],
        "explanation": f"Respuesta {chr(65 + answers[number])} según la plantilla oficial publicada por la Generalitat Valenciana.",
        "isTheoreticalPractical": number >= 35,
    })

if len(questions) != 40 or len(answers) != 40:
    raise ValueError(f"Esperadas 40 preguntas y respuestas; obtenidas {len(questions)} y {len(answers)}")

pack = {
    "schemaVersion": 1,
    "id": "gva-c1-01-edu-23",
    "version": 1,
    "title": "C1-01-EDU/23 - ejercicio único",
    "origin": "official_exam",
    "sourceTitle": "Generalitat Valenciana - cuestionario y plantilla C1-01-EDU/23",
    "sourceURL": "https://www.gva.es/descarregues/2023/05/25992-EXAMEN_C1_CAST.pdf",
    "answerKeyURL": "https://www.gva.es/descarregues/2023/05/25990-PLANTILLA-respuesta_C1.pdf",
    "sourceLicense": "Documento público de la Generalitat Valenciana; fuente y fecha identificadas conforme a las condiciones de reutilización del sector público.",
    "sourcePublishedAt": "2023-05-15T00:00:00Z",
    "verifiedAt": "2026-09-13T00:00:00Z",
    "questions": questions,
}
OUTPUT.write_text(json.dumps(pack, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(f"Generado {OUTPUT} con {len(questions)} preguntas")
