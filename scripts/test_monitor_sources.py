import unittest

import monitor_sources


class MonitorParsingTests(unittest.TestCase):
    def test_catalog_stage_document_and_comparison(self):
        catalog = '''
        <div class="opposition d-flex"><a href="/detall-ocupacio-publica?id_emp=12345">
        <div class="title medium">Convocatoria 99/26. Administrativo, C1-01</div></a></div>
        <div class="opposition d-flex"><a href="/detall-ocupacio-publica?id_emp=777">
        <div class="title medium">Convocatoria A2-01</div></a></div>
        '''
        calls = monitor_sources.parse_catalog(catalog, "https://sede.gva.es/es/cercador")
        self.assertEqual([12345], [item["employmentId"] for item in calls])

        detail = '''
        <p name="8" class="font-weight-bold">Plantilla de respuestas del ejercicio</p>
        <p class="fecha-etapa"><span>Fecha publicación:</span> 01-09-2026</p>
        '''
        stages = monitor_sources.parse_stages(detail, 12345)
        self.assertEqual(8, stages[0]["stageId"])

        stage = '''<a href="https://sede.gva.es/descarregues/2026/09/CUESTIONARIO_C1-01.pdf">Web</a>'''
        documents = monitor_sources.parse_documents(stage)
        self.assertEqual(1, len(documents))

        snapshot = {"calls": calls, "stages": stages, "documents": documents}
        changes = monitor_sources.compare(snapshot, {"calls": [], "stages": [], "documents": []})
        self.assertEqual(1, len(changes["calls"]))
        self.assertEqual(1, len(changes["stages"]))
        self.assertEqual(1, len(changes["documents"]))


if __name__ == "__main__":
    unittest.main()
