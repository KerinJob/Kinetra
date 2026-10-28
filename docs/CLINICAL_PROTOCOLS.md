# Protocolos clínicos y estado de validación

> Ningún protocolo está aprobado profesionalmente a la fecha.

## Pendientes clínicos (no decididos por el equipo técnico)
- Pruebas articulares finales.
- Convención de medición de cada prueba (p. ej. si se reporta θ geométrico o 180−θ).
- Error angular aceptable.
- Umbrales de calidad clínicamente aceptables.
- Número de pacientes, videos y repeticiones para validación.
- Condiciones de captura (plano, distancia, encuadre, vestimenta, iluminación).
- Canal definitivo de recepción de videos y posible cuenta de paciente.

## DEMO_FLEX_CODO_L / DEMO_FLEX_CODO_R — v0.1.0-demo
- **Estado:** DEMOSTRACIÓN TÉCNICA PENDIENTE DE VALIDACIÓN PROFESIONAL. No es una prueba clínica aprobada.
- Puntos MediaPipe: hombro (11/12) – codo (13/14, vértice) – muñeca (15/16).
- Espacio: 2D en píxeles (x·ancho, y·alto).
- Salida: ángulo geométrico (180° ≈ brazo extendido). Sin conversión clínica aplicada.
- Umbral técnico provisional: visibilidad mínima 0,5 en los tres puntos (no clínico).
- Uso: probar integración extremo a extremo del sistema.
