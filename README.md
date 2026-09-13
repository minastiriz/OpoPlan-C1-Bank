# OpoPlan C1 - Banco de preguntas

Repositorio público de contenido para OpoPlan C1. No contiene el código de la aplicación ni datos personales.

## Criterios editoriales

- Un paquete `official_exam` reproduce un cuestionario y una plantilla de respuestas publicados por una administración pública.
- Un paquete `verified_legislation` contiene preguntas redactadas a partir de una norma oficial y nunca se presenta como examen oficial.
- Toda pregunta incluye procedencia, fecha de publicación, fecha de verificación y condiciones de reutilización.
- Ningún paquete llega a la aplicación sin revisión humana, SHA-256 y firma ECDSA P-256.
- Una actualización puede corregir o desactivar preguntas, pero la app conserva los resultados históricos del usuario.

El manifiesto público está en `manifest.json`. La aplicación descarga únicamente versiones superiores a las ya instaladas y sigue funcionando sin conexión.

## Contenido actual

- 40 preguntas oficiales del ejercicio C1-01-EDU/23.
- 90 preguntas oficiales de la convocatoria 7/22, C1-01.
- 90 preguntas oficiales de la convocatoria 12/23, C1-01.
- 90 preguntas oficiales de la convocatoria 151/21, C1-01.
- 90 preguntas oficiales de la convocatoria 27/24, C1-01.
- 110 preguntas oficiales del primer ejercicio de la convocatoria 64/25, C1-01.
- Total: 510 preguntas oficiales verificadas.

La versión 2 del paquete 64/25 incorpora una asignación editorial explícita de sus
110 preguntas al temario oficial de la Orden 26/2025. La construcción falla si una
pregunta queda sin tema o recibe dos, evitando que una heurística silenciosa la envíe
por defecto a E1 o G1.

Los paquetes históricos reproducen la redacción y respuesta oficial de la fecha del examen. La normativa puede haber cambiado después; conservar el origen y la fecha permite distinguir entrenamiento histórico de contenido vigente.

## Fuentes vigiladas

La automatización local diaria `Vigilar C1-01 GVA` consulta el buscador oficial de empleo público con varias búsquedas C1-01, descubre identificadores de convocatorias, inspecciona sus etapas de cuestionario/plantilla y registra los PDF oficiales. Se ejecuta desde el equipo autorizado porque la Sede GVA no responde a las direcciones de red de GitHub Actions. La línea base actual cubre 66 resultados C1-01, 25 etapas de examen y 24 documentos. Solo una novedad real o un fallo persistente genera un aviso en Codex; nunca se generan ni publican preguntas automáticamente.

El script `scripts/build_historical_packs.py` vuelve a construir los cuatro paquetes históricos a partir de sus PDF oficiales y se detiene si falta numeración, alguna opción o una respuesta de plantilla. `scripts/validate_release.py` exige al menos 500 preguntas, texto completo, identificadores únicos, SHA-256 y firma ECDSA válida.

## Reutilización

Los metadatos y scripts de este repositorio se publican bajo CC0-1.0. Los cuestionarios conservan la atribución y las condiciones indicadas por su organismo de origen.
