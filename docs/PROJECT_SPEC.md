# Especificación del proyecto Kinetra

Síntesis entregada por el autor (el documento académico original no está disponible para el agente).

## 1. Propósito
Sistema web de visión computacional para medir ángulos articulares de pacientes de fisioterapia del
Centro Kinesport Tarija (Bolivia). Reemplaza goniómetro + fichas físicas + coordinación por WhatsApp
con un registro integrado de pacientes, citas, sesiones, evaluaciones y mediciones.

Flujo principal: video de una prueba → detección de puntos corporales → cálculo angular →
almacenamiento por paciente y sesión → revisión del fisioterapeuta → comparación entre sesiones.

Usuarios iniciales: profesionales del centro. Apoya evaluaciones presenciales y controles
complementarios por video, posteriores a una evaluación presencial inicial y a criterio del fisioterapeuta.

## 2. Funciones de la aplicación final
- F01 Autenticación de profesionales y acceso autorizado a información y archivos.
- F02 Registro y consulta de datos básicos de pacientes.
- F03 Gestión de citas, diferenciadas de sesiones realizadas.
- F04 Registro de sesiones y evaluaciones.
- F05 Catálogo de pruebas (articulación, movimiento, lado, condiciones de captura, convención angular).
- F06 Carga privada de videos por un profesional.
- F07 Procesamiento real con modelo preentrenado de pose.
- F08 Mediciones angulares asociadas al tiempo del video.
- F09 Identificación de detecciones insuficientes y resultados inválidos.
- F10 Visualización del video y resultados para revisión profesional.
- F11 Registro del responsable de la evaluación y de su revisión.
- F12 Historial por paciente y comparación entre sesiones compatibles.
- F13 Extracción de datos para comparar mediciones automáticas con referencias del fisioterapeuta y evaluar tiempos.
- F14 Instalación reproducible, respaldo y recuperación de datos y videos.

## 3. Límites obligatorios
- MediaPipe con modelo de pose preentrenado; no entrenar modelos desde cero.
- PostgreSQL.
- Separación presentación / lógica de aplicación / procesamiento / persistencia.
- Sin diagnóstico automático, prescripción ni predicción de lesiones. La interpretación clínica es del fisioterapeuta.
- Solo pruebas seleccionadas y definidas con el profesional.
- Las coordenadas 3D estimadas no garantizan exactitud.
- No presentar resultados de investigaciones previas como precisión de esta aplicación.
- Equipo convencional, sin GPU obligatoria. Herramientas abiertas, bajo costo.
- Investigación: Kinesport Tarija, sep-2026 a mar-2027 (no limita fechas de uso).

## 4. Exclusiones iniciales
Integración automática con WhatsApp, chatbot, pagos, facturación, app móvil nativa, videollamadas,
portal de pacientes, medición en vivo, soporte multiclínica.

## 5. Reglas del motor de medición
- Ángulo en B: u=A−B, v=C−B, acos(clamp(u·v/(|u||v|),−1,1)) en grados.
- Rechazar vectores degenerados, puntos insuficientes y valores no finitos. Inválido ≠ 0.
- 2D: convertir normalizadas a píxeles (x·ancho, y·alto).
- Distinguir ángulo geométrico de convención clínica; no aplicar 180−θ de forma general.
- Distinguir ángulo instantáneo de ROM; no declarar ROM = máx−mín sobre cualquier video.
- Conservar marcas temporales, calidad, protocolo, configuración y versión de procesamiento.
- Gestionar ausencia de pose, baja visibilidad, oclusión, sujeto ambiguo. Confianza ≠ exactitud.
- Suavizado documentado y serie original conservada; no ocultar huecos largos con interpolación.

## 6. Comparación, seguridad, validación
- Comparar solo mediciones equivalentes (prueba, lado, magnitud, convención, condiciones, versión de protocolo).
- No clasificar diferencias como mejoría/deterioro.
- Proteger API, historiales y videos; nada de credenciales, datos reales o videos en Git/logs.
- Validar contenido, tamaño, duración y recursos de los archivos.
- Interfaz en español; citas presentadas en America/La_Paz; almacenamiento en UTC.
- Tres niveles separados: pruebas sintéticas, pruebas técnicas con videos reales autorizados,
  validación con referencias del fisioterapeuta. No fabricar videos, mediciones ni resultados.
- Evaluación final: pares sistema/referencia en condiciones equivalentes y tiempos manual vs digital;
  criterios de aceptación acordados antes del análisis; correlación ≠ concordancia.

## 7. Arquitectura técnica propuesta
FastAPI (Python), MediaPipe Tasks Pose Landmarker, OpenCV + NumPy, PostgreSQL + SQLAlchemy + Alembic,
React + TypeScript + Vite, pytest, Playwright, Docker Compose si el entorno lo permite.
Worker separado para video con estado en PostgreSQL, progreso consultable, recuperación sin duplicados.
Almacenamiento privado persistente de videos con metadatos en PostgreSQL.
Antes de fijar o cambiar versiones, verificar compatibilidad real SO/Python/MediaPipe/modelo y conservar archivos de bloqueo.
Si existe código aprovechable, inspeccionarlo y justificar cualquier reemplazo.

## 8. Forma de trabajo exigida por el autor
- Rol del agente: responsable técnico e implementador. Escribir código, ejecutar pruebas y producir una aplicación instalable, por etapas.
- El documento académico original no está disponible: **no pedirlo**. Esta especificación es la fuente de trabajo.
- Conservar el trabajo previo; recuperar el estado desde `docs/STATUS.md` sin releer todo el proyecto.
- Un agente por defecto. Si la delegación es útil: máximo **dos ejecutores simultáneos**, con tareas y archivos separados, y un responsable que integra.
- Resolver solo las decisiones técnicas reversibles y documentarlas en `DECISIONS.md`. Consultar al autor cuando falte una decisión clínica imprescindible o una autorización externa (video, credenciales).
- Ante un bloqueo parcial, identificarlo con exactitud, dejar preparado lo posible y continuar con otras tareas. **Nunca simular una ejecución exitosa.**
- Evitar logs extensos y ciclos de intentos idénticos.
- Actualizar `STATUS.md` al terminar **cada** tarea, sin esperar a agotar el contexto. Registrar evidencias en `VALIDATION.md` y `TRACEABILITY.md`.
- No entregar solo un plan: implementar y verificar hasta donde permitan los recursos.
- Al cerrar cada sesión, informar al autor de forma breve: qué funciona, comandos ejecutados y resultados, qué quedó bloqueado, el siguiente paso y los comandos para ejecutar lo disponible.
- El autor no es experto en el entorno. Cualquier acción que requiera sus credenciales debe darse como un script que ejecute él, sin que el agente vea la contraseña (ver `scripts/setup_db.ps1`).

## 9. Documentos a mantener
`AGENTS.md`, `README.md`, `docs/PROJECT_SPEC.md`, `DECISIONS.md`, `CLINICAL_PROTOCOLS.md`, `BACKLOG.md`, `TRACEABILITY.md`, `STATUS.md`, `VALIDATION.md`.
