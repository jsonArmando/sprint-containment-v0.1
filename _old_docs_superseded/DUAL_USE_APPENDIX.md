# Apéndice Limitations & Dual-Use (Track 1)

**Estándar:** Observer-Cheat Test: Containment Adequacy under Opaque Intent
(`CONTRACT.md`, `CONTROLS.md`).
**Cómo leer esto:** cada limitación dice qué prueba existe hoy, qué no
prueba, y qué se necesitaría para cerrarla. Ninguna se declara resuelta
donde no lo está — ver `CONTROLS.md § Delta v0.2 → v0.3` para el detalle
técnico completo.

---

## Limitations

### 1. Mutación/fragmentación del adversario más allá del rename

**Qué se probó.** `scenarios/adaptive_rename.yaml` demuestra que renombrar
`tool_id` no evade la clasificación de Capa 1: `harness/taxonomy.py`
clasifica por `src`/`dst`/`outcome`/`deny_reason` — campos que escribe el
proxy, no el agente.

**Qué NO se probó.** Que fragmentar la cadena de ataque a través de un hop
intermedio que nunca dispare `allowlist_scope_stretch`, o dividir
`chain_fetch_then_hop` en pasos que individualmente no matcheen ninguna
regla, evada la detección igual. La evade: el motor sigue siendo un
conjunto fijo de reglas de patrón sobre un vocabulario cerrado de clases
(`fetch`, `lateral_hop`, `scope_stretch_attempt`). Cualquier efecto que no
caiga en esas clases cae en `other` y desaparece del radar.

**Qué se necesitaría.** Detección estadística/de anomalía sobre una
distribución de tráfico normal, no más reglas de patrón añadidas a mano.
Eso es un proyecto de investigación, no una corrección de fin de semana.

### 2. Low-and-slow entre episodios (no solo entre ventanas)

**Qué se probó.** `harness/layer1.py::_fan_out()` detecta ráfagas dentro
de una ventana de tiempo corta (`policy/layer1_policy.yaml:
window_seconds`). `tests/test_layer1_windows.py::test_low_and_slow_spread_across_windows_evades_fan_out`
demuestra —en código, no en prosa— que el mismo volumen de llamadas
repartido en ventanas separadas **no** dispara `fan_out_burst`.

**Qué NO se probó.** Ninguna forma de correlación entre episodios. `run()`
evalúa cada episodio como una unidad aislada, sin estado de sesión
acumulado. Un atacante que reparte su cadena en múltiples
episodios/evaluaciones, cada uno por debajo del umbral individual, no deja
ningún rastro agregado que este harness pueda ver.

**Qué se necesitaría.** Un almacén de estado de sesión con ventana de
tiempo mucho más amplia que un episodio, y una política explícita de
cuánto tiempo retener esa correlación — con las implicaciones de privacidad
y retención que eso conlleva.

### 3. Concurrencia de producción

**Qué se probó.** Una traza de efectos lineal, de un solo agente sintético,
en un laboratorio de juguete (`CONTRACT.md` §4).

**Qué NO se probó.** Nada bajo microservicios concurrentes o llamadas
asíncronas reales. Esa mezcla rompe el supuesto de linealidad sobre el que
están construidas las reglas de secuencia de Capa 1. Esto está
explícitamente fuera de alcance (`CONTRACT.md` §7: "No VPC, Fargate,
Neptune, LangGraph completo") — se documenta aquí como limitación conocida,
no como algo que este sprint intentó resolver.

**Qué se necesitaría.** Correlación por episode_nonce/traza distribuida
(tracing real, tipo OpenTelemetry) antes de que las reglas de secuencia
tengan sentido en un entorno multi-servicio.

### 4. Fail-closed sin período de gracia

**Qué se probó.** `harness/actuator.py::Actuator.fail_closed_egress_cut()`
corta el egress allowlist cuando el colector cae, en vez de anular el
episodio a favor del workload (`scenarios/panic.yaml`, C7).

**Qué NO se probó ni se resolvió.** Ninguna distinción entre "colector
reiniciando por un despliegue benigno" y "colector asesinado por el
workload" — el harness corta igual en ambos casos. Esto es un trade-off de
diseño aceptado a propósito (disponibilidad por seguridad cuando hay duda),
no un caso mitigado con backoff o período de gracia.

**Qué se necesitaría.** Una señal de heartbeat distinta de "colector
responde/no responde" — por ejemplo, un plano de control separado que
anuncie mantenimiento planeado antes de que el actuador decida fail-closed.

---

## Dual-Use y No-Reconstrucción (C11)

### Qué contiene este repositorio

- Un test de auditoría de esquema (`assert_frontier`, `schema_validate.py`)
  que detecta si un observador de contención consume campos de Intent.
- Un tripwire de secuencia sobre efectos sintéticos, en un laboratorio de
  juguete (`scenarios/*.yaml`), con nombres de destino y activos ficticios
  (`proxy.eval.lab`, `harness`, `collector`).
- Fixtures de contraste (`intent_on.yaml`, `intent_rewritten.yaml`) que
  contienen strings de ejemplo como `"I will treat the proxy as the path
  out."` — son texto de demostración para el propio test, no una técnica de
  evasión nueva ni verificada contra un sistema real.

### Qué NO contiene

- Ninguna receta de escape de sandbox o de contenedor.
- Ningún exploit, payload, ni installer ofensivo.
- Ninguna reconstrucción de fases de una campaña real contra un tercero.
- Ninguna credencial, endpoint, o configuración de un sistema en producción.

### Claims sobre incidentes públicos

Este repositorio referencia en `CONTROLS.md`/`CONTRACT.md` incidentes y
publicaciones externas (p. ej. un CVE de un harness de terceros, un paper
sobre monitores de CoT, un episodio de autocertificación). **Ninguna de esas
referencias ha sido verificada con fuente primaria dentro de este
repositorio** — no hay URL, DOI, ni enlace adjunto a día de hoy. Hasta que
se adjunten esas fuentes:

- No deben citarse como hechos establecidos fuera de este repo.
- Un revisor externo debe poder pedir la fuente primaria y recibirla antes
  de aceptar el claim — si no puede dársela, el claim se retira del PDF, no
  se suaviza.

### Por qué el diseño no es reconstruible en un exploit

El tripwire (`harness/layer1.py` + `harness/taxonomy.py`) clasifica por
campos que el *proxy* escribe (`src`, `dst`, `outcome`, `deny_reason`), no
por técnicas de evasión del agente. Publicar las reglas no enseña a nadie a
salir de un proxy real: enseña qué figura ya deja el proxy cuando algo sale
mal. Esa es la propiedad que C11 pide preservar. Las cuatro limitaciones
de arriba tampoco son una receta de evasión operable: describen qué clase
de ataque no está cubierta, no cómo ejecutarlo contra un sistema real.
