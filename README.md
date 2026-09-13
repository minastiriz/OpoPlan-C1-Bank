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
- 90 preguntas oficiales de la convocatoria 12/23, C1-01.
- Total: 130 preguntas oficiales verificadas.

## Fuentes vigiladas

La automatización semanal comprueba cambios en las páginas oficiales registradas en `sources.json`. Un cambio hace fallar la ejecución para que sea revisado; no genera ni publica preguntas automáticamente.

## Reutilización

Los metadatos y scripts de este repositorio se publican bajo CC0-1.0. Los cuestionarios conservan la atribución y las condiciones indicadas por su organismo de origen.
