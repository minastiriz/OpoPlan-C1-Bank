"""Build reviewed C1-01 packs from official Generalitat Valenciana PDFs.

The page ranges deliberately select the Spanish-language, turno libre questionnaire
from each bilingual source. Answer keys are read from the official key page and the
builder refuses to publish if numbering, options or answers are incomplete.
"""

from __future__ import annotations

import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF_ROOT = ROOT.parent / "tmp" / "pdfs" / "historical"


EXAMS = (
    {
        "id": "gva-c1-01-7-22",
        "version": 2,
        "title": "Convocatoria 7/22 - ejercicio único",
        "pdf": "7-8-22.pdf",
        "key_page": 0,
        "question_pages": range(3, 31),
        "count": 90,
        "published": "2023-02-20T00:00:00Z",
        "source_url": "https://www.gva.es/downloads/publicados/EP/plantilla_y_cuestionario_7_8_22.pdf",
    },
    {
        "id": "gva-c1-01-151-21",
        "version": 2,
        "title": "Convocatoria 151/21 - ejercicio único",
        "pdf": "151-21.pdf",
        "key_page": 0,
        "question_pages": range(2, 48),
        "count": 90,
        "published": "2024-05-13T00:00:00Z",
        "source_url": "https://sede.gva.es/descarregues/2024/05/65956-BPR_mas_ejercicios_151_21.pdf",
    },
    {
        "id": "gva-c1-01-27-24",
        "version": 2,
        "title": "Convocatoria 27/24 - primer ejercicio",
        "pdf": "27-24.pdf",
        "key_page": 0,
        "question_pages": range(30, 57),
        "count": 90,
        "published": "2025-01-27T00:00:00Z",
        "source_url": "https://sede.gva.es/descarregues/2025/01/97630-PLANTILLA_RESPUESTAS_Y_CUESTIONARIOS_27_24_TL.pdf",
    },
    {
        "id": "gva-c1-01-64-25",
        "version": 2,
        "title": "Convocatoria 64/25 - primer ejercicio",
        "pdf": "64-25-1.pdf",
        "key_page": 0,
        "question_pages": range(4, 29),
        "count": 110,
        "published": "2026-02-02T00:00:00Z",
        "source_url": "https://sede.gva.es/descarregues/2026/02/135758-Plantilla_de_respuestas_y_cuestionarios.pdf",
    },
)


def expand_topic_map(groups: dict[tuple[str, int], tuple[int, ...]], expected: range) -> dict[int, tuple[str, int]]:
    """Expand a manually reviewed map and refuse gaps or duplicate assignments."""
    result: dict[int, tuple[str, int]] = {}
    for topic, numbers in groups.items():
        for number in numbers:
            if number in result:
                raise ValueError(f"La pregunta {number} tiene dos temas asignados")
            result[number] = topic
    if set(result) != set(expected):
        missing = sorted(set(expected) - set(result))
        extra = sorted(set(result) - set(expected))
        raise ValueError(f"Mapa editorial incompleto; faltan {missing} y sobran {extra}")
    return result


# Revisión editorial contra el Anexo I de la Orden 26/2025 (DOGV 10135 bis).
# No se usa una palabra aislada para decidir el tema: las 110 preguntas del examen
# quedan asignadas explícitamente y cualquier hueco hace fallar la construcción.
TOPIC_MAP_64_25 = expand_topic_map({
    ("Parte especial", 1): (1, 2, 3, 4, 53),
    ("Parte especial", 2): (5, 6, 7, 54),
    ("Parte especial", 3): (8, 9, 10, 11, 12),
    ("Parte especial", 4): (13, 14, 15),
    ("Parte especial", 5): (16, 17, 18, 59, 60),
    ("Parte especial", 6): (19, 20, 21, 22, 23, 51, 55, 56),
    ("Parte especial", 7): (24, 25, 26, 57),
    ("Parte especial", 8): (27, 28, 29),
    ("Parte especial", 9): (30, 31, 32, 33, 34),
    ("Parte especial", 10): (35, 36, 37, 38, 52, 58, 61),
    ("Parte especial", 11): (39, 41, 44, 62),
    ("Parte especial", 12): (40, 42, 43, 45, 50, 63, 64, 65),
    ("Parte especial", 13): (46, 47),
    ("Parte especial", 14): (48, 49),
    ("Parte especial", 15): (66,),
    ("Parte especial", 16): (67, 78),
    ("Parte especial", 17): (68,),
    ("Parte especial", 18): (69, 70, 79),
    ("Parte especial", 19): (71, 72),
    ("Parte especial", 20): (73, 80),
    ("Parte especial", 21): (74,),
    ("Parte especial", 22): (75, 77),
    ("Parte especial", 23): (76,),
    ("Parte general", 1): (81, 82, 83, 84),
    ("Parte general", 2): (85, 86, 87, 88, 89, 90),
    ("Parte general", 3): (91, 92),
    ("Parte general", 4): (93, 94),
    ("Parte general", 5): (95, 96),
    ("Parte general", 6): (97, 98, 99),
    ("Parte general", 7): (100, 101, 102, 103),
    ("Parte general", 8): (104, 105),
    ("Parte general", 9): (106, 107),
    ("Parte general", 10): (108,),
    ("Parte general", 11): (109,),
    ("Parte general", 12): (110,),
}, range(1, 111))


# Revisión editorial del cuestionario 7/22 contra las mismas materias del temario
# vigente. Se conserva literalmente el examen histórico y solo se normaliza el
# tema al que aporta evidencia dentro de la aplicación.
TOPIC_MAP_7_22 = expand_topic_map({
    ("Parte general", 1): (1,),
    ("Parte general", 2): (2, 3, 4, 5, 8),
    ("Parte general", 3): (6, 7, 9),
    ("Parte general", 4): (10,),
    ("Parte general", 5): (11, 12),
    ("Parte general", 6): (13, 14),
    ("Parte general", 7): (15, 16, 18),
    ("Parte general", 8): (17, 19),
    ("Parte general", 9): (20, 21),
    ("Parte general", 10): (22, 23, 24, 25, 26),
    ("Parte general", 11): (27, 28, 29, 30),
    ("Parte general", 12): (31, 32, 33, 34),
    ("Parte especial", 1): (35, 36, 37, 38),
    ("Parte especial", 2): (39, 40, 41, 42, 43),
    ("Parte especial", 3): (44, 45, 46, 47, 48, 49, 50),
    ("Parte especial", 4): (51, 52, 53),
    ("Parte especial", 5): (55, 56, 57),
    ("Parte especial", 6): (58, 59, 60, 61, 62, 63),
    ("Parte especial", 7): (64, 65),
    ("Parte especial", 8): (66, 67, 68),
    ("Parte especial", 9): (69, 70, 71),
    ("Parte especial", 10): (72, 73, 74, 75, 76, 77),
    ("Parte especial", 11): (54, 78, 79, 80, 81, 82, 85),
    ("Parte especial", 12): (83, 84, 86, 87, 88),
    ("Parte especial", 13): (89, 90),
}, range(1, 91))


TOPIC_MAP_151_21 = expand_topic_map({
    ("Parte especial", 1): (1, 2, 3),
    ("Parte especial", 2): (4, 5, 6, 7, 8, 9),
    ("Parte especial", 3): (10, 11, 12, 13, 14, 15, 16),
    ("Parte especial", 4): (17, 18, 19),
    ("Parte especial", 5): (20, 21, 22),
    ("Parte especial", 6): (23, 24, 25, 26, 27, 28),
    ("Parte especial", 7): (29, 30, 31),
    ("Parte especial", 8): (32, 33, 34),
    ("Parte especial", 9): (35, 36, 37),
    ("Parte especial", 10): (38, 39, 40, 41, 42, 43),
    ("Parte especial", 11): (44, 45, 46, 47, 48, 49),
    ("Parte especial", 12): (50, 51, 52, 53, 54),
    ("Parte especial", 13): (55, 56),
    ("Parte general", 1): (57, 58),
    ("Parte general", 2): (59, 60),
    ("Parte general", 3): (61, 62, 63),
    ("Parte general", 4): (64, 65, 66),
    ("Parte general", 5): (67, 68, 69),
    ("Parte general", 6): (70, 71, 72, 73, 74),
    ("Parte general", 7): (75, 76, 77),
    ("Parte general", 8): (78, 79),
    ("Parte general", 9): (80, 81),
    ("Parte general", 10): (82, 83, 84),
    ("Parte general", 11): (85, 86),
    ("Parte general", 12): (87, 88, 89, 90),
}, range(1, 91))


TOPIC_MAP_27_24 = expand_topic_map({
    ("Parte especial", 1): (1, 2, 3, 4),
    ("Parte especial", 2): (5, 6, 7, 8, 9),
    ("Parte especial", 3): (10, 11, 12, 13, 14, 15),
    ("Parte especial", 4): (16, 17),
    ("Parte especial", 5): (18, 19, 20),
    ("Parte especial", 6): (21, 22, 23, 24, 25, 26),
    ("Parte especial", 7): (27, 28),
    ("Parte especial", 8): (29, 30, 31),
    ("Parte especial", 9): (32, 33),
    ("Parte especial", 10): (34, 35, 36, 37, 38),
    ("Parte especial", 11): (39, 40, 41, 42, 43, 44),
    ("Parte especial", 12): (45, 46, 47, 48, 49, 50, 51),
    ("Parte especial", 13): (52, 53),
    ("Parte especial", 14): (54, 55, 56),
    ("Parte general", 1): (57, 58, 59),
    ("Parte general", 2): (60, 61, 62),
    ("Parte general", 3): (63, 65),
    ("Parte general", 4): (64, 66, 67, 68),
    ("Parte general", 5): (69, 70, 71),
    ("Parte general", 6): (72, 73, 74),
    ("Parte general", 7): (75, 76, 77),
    ("Parte general", 8): (78, 79, 80),
    ("Parte general", 9): (81, 82),
    ("Parte general", 10): (83, 84, 85),
    ("Parte general", 11): (86, 87),
    ("Parte general", 12): (88, 89, 90),
}, range(1, 91))


MANUAL_TOPIC_MAPS = {
    "gva-c1-01-7-22": TOPIC_MAP_7_22,
    "gva-c1-01-151-21": TOPIC_MAP_151_21,
    "gva-c1-01-27-24": TOPIC_MAP_27_24,
    "gva-c1-01-64-25": TOPIC_MAP_64_25,
}


def clean(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.replace("\u00ad", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    value = re.sub(r"(?<=\w)\s+(?=[,.;:?!])", "", value)
    return " ".join(value.split()).strip()


def extract_answers(text: str, expected_count: int) -> dict[int, int]:
    pairs = re.findall(r"(?<!\d)(\d{1,3})\s+([ABCD])(?!\w)", text)
    answers: dict[int, int] = {}
    for raw_number, letter in pairs:
        number = int(raw_number)
        if 1 <= number <= expected_count:
            answers[number] = ord(letter) - ord("A")
    expected = set(range(1, expected_count + 1))
    if set(answers) != expected:
        missing = sorted(expected - set(answers))
        raise ValueError(f"Plantilla incompleta; faltan respuestas: {missing}")
    return answers


def classify(exam_id: str, number: int, prompt: str) -> tuple[str, int]:
    if manual_map := MANUAL_TOPIC_MAPS.get(exam_id):
        return manual_map[number]

    # The official exams change order between calls. These boundaries keep every
    # question attached to a valid current syllabus topic without changing its text.
    general_starts = {
        "gva-c1-01-7-22": (1, 35),
        "gva-c1-01-151-21": (58, 91),
        "gva-c1-01-27-24": (57, 91),
        "gva-c1-01-64-25": (81, 111),
    }
    start, end = general_starts[exam_id]
    is_general = start <= number < end
    folded = unicodedata.normalize("NFKD", prompt).encode("ascii", "ignore").decode().casefold()

    if is_general:
        if "union europea" in folded or "tratado de funcionamiento" in folded:
            return "Parte general", 9
        if "violencia de genero" in folded:
            return "Parte general", 11
        if "igualdad" in folded or "lgtbi" in folded:
            return "Parte general", 10
        if "transparencia" in folded or "informacion publica" in folded:
            return "Parte general", 12
        if "estatuto de autonomia" in folded:
            return "Parte general", 6
        if "consell" in folded or "president de la generalitat" in folded:
            return "Parte general", 7
        if "tribunal constitucional" in folded or "poder judicial" in folded:
            return "Parte general", 4
        if "comunidades autonomas" in folded or "organizacion territorial" in folded:
            return "Parte general", 5
        if "cortes generales" in folded or "corona" in folded or "elaboracion de las leyes" in folded:
            return "Parte general", 2
        return "Parte general", 1

    if "excel" in folded:
        return "Parte especial", 20
    if "word" in folded:
        return "Parte especial", 19
    if "outlook" in folded or "correo" in folded:
        return "Parte especial", 18
    if "phishing" in folded or "navegador" in folded or "vpn" in folded:
        return "Parte especial", 22
    if "inteligencia artificial" in folded or "prompt" in folded:
        return "Parte especial", 23
    if "contratos del sector publico" in folded:
        return "Parte especial", 6
    if "proteccion de datos" in folded or "administracion electronica" in folded:
        return "Parte especial", 7
    if "funcion publica" in folded or "personal funcionario" in folded or "empleado publico" in folded:
        return "Parte especial", 8
    if "presupuesto" in folded or "hacienda publica" in folded:
        return "Parte especial", 11
    if "subvencion" in folded:
        return "Parte especial", 5
    if "ley 40/2015" in folded or "competencia" in folded or "organo administrativo" in folded:
        return "Parte especial", 4
    if "recurso" in folded or "revision" in folded or "procedimiento" in folded:
        return "Parte especial", 3
    if "acto administrativo" in folded or "notificacion" in folded:
        return "Parte especial", 2
    return "Parte especial", 1


def extract_questions(text: str, expected_count: int) -> list[tuple[int, str, list[str]]]:
    # Printed page numbers are extracted as standalone lines and otherwise become
    # part of the preceding option D.
    text = re.sub(r"(?m)^[ \t]*\d{1,3}[ \t]*$", "", text)
    starts = list(re.finditer(r"(?m)^[ \t]*(\d{1,3})[ \t]*[.\-][ \t]*(?=\S)(?!\d)", text))
    by_number = {int(match.group(1)): match for match in starts if 1 <= int(match.group(1)) <= expected_count}
    if set(by_number) != set(range(1, expected_count + 1)):
        missing = sorted(set(range(1, expected_count + 1)) - set(by_number))
        raise ValueError(f"Numeración incompleta; faltan preguntas: {missing}")

    ordered = [by_number[number] for number in range(1, expected_count + 1)]
    questions = []
    for index, match in enumerate(ordered):
        number = index + 1
        end = ordered[index + 1].start() if index + 1 < len(ordered) else len(text)
        block = text[match.end():end]
        options = list(re.finditer(r"(?m)^\s*([ABCD])\)\s*", block))
        if [option.group(1) for option in options] != list("ABCD"):
            raise ValueError(f"Opciones inesperadas en la pregunta {number}: {[o.group(1) for o in options]}")
        prompt = clean(block[:options[0].start()])
        values = []
        for option_index, option in enumerate(options):
            option_end = options[option_index + 1].start() if option_index + 1 < 4 else len(block)
            values.append(clean(block[option.end():option_end]))
        if not prompt or any(not option for option in values):
            raise ValueError(f"Texto vacío en la pregunta {number}")
        questions.append((number, prompt, values))
    return questions


def build(exam: dict) -> pathlib.Path:
    import pdfplumber

    pdf_path = PDF_ROOT / exam["pdf"]
    with pdfplumber.open(pdf_path) as reader:
        answers = extract_answers(
            reader.pages[exam["key_page"]].extract_text(x_tolerance=2, y_tolerance=3) or "",
            exam["count"],
        )
        question_text = "\n".join(
            reader.pages[index].extract_text(x_tolerance=2, y_tolerance=3) or ""
            for index in exam["question_pages"]
        )
    extracted = extract_questions(question_text, exam["count"])

    questions = []
    for number, prompt, options in extracted:
        part, topic_number = classify(exam["id"], number, prompt)
        letter = chr(ord("A") + answers[number])
        questions.append({
            "id": f"{exam['id']}-q{number:03d}",
            "part": part,
            "topicNumber": topic_number,
            "prompt": prompt,
            "options": options,
            "correctIndex": answers[number],
            "explanation": f"Respuesta {letter} según la plantilla oficial publicada por la Generalitat Valenciana.",
            "isTheoreticalPractical": exam["id"] == "gva-c1-01-64-25" and 53 <= number <= 81,
        })

    pack = {
        "schemaVersion": 1,
        "id": exam["id"],
        "version": exam.get("version", 1),
        "title": exam["title"],
        "origin": "official_exam",
        "sourceTitle": f"Generalitat Valenciana - cuestionario y plantilla de {exam['title']}",
        "sourceURL": exam["source_url"],
        "answerKeyURL": exam["source_url"],
        "sourceLicense": "Documento público de la Generalitat Valenciana; fuente y fecha identificadas conforme a las condiciones de reutilización del sector público.",
        "sourcePublishedAt": exam["published"],
        "verifiedAt": "2026-09-13T00:00:00Z",
        "questions": questions,
    }
    output = ROOT / "packs" / f"{exam['id']}-v{pack['version']}.json"
    output.write_text(json.dumps(pack, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    for definition in EXAMS:
        path = build(definition)
        print(f"Generado {path.name} con {definition['count']} preguntas oficiales")
