# Posibles complementos del kit

> Backlog de mejoras **consideradas y no implementadas**. Cada una es opcional: el kit funciona sin
> ellas. Se anotan aquí para no perderlas, no como compromiso. Orden por afinidad, no por prioridad.

---

## 1. Medición de consumos (observabilidad de coste)

**Idea.** Visibilidad del gasto de tokens y coste del equipo virtual, desglosado **por unidad/agente
y por modelo** (cuánto quema el arquitecto en Opus frente a las unidades en Sonnet, qué unidad es la
más cara, etc.).

**Por qué NO es un agente.** La medición es una tarea determinista, y montarla como subagente LLM es
el patrón equivocado por tres razones: (a) medir consumiría tokens para contar tokens; (b) un LLM es
no-determinista y malo agregando números; (c) Claude Code **ya emite el dato de serie**. No hay que
construir un termómetro: hay que recogerlo. Es instrumentación, no un miembro del equipo. Coherente
con la regla del kit: lo determinista va en hook/script, no en prompt.

**Lo que Claude Code ya da.** Telemetría nativa vía OpenTelemetry (opt-in con
`CLAUDE_CODE_ENABLE_TELEMETRY=1` + exporters OTLP): tokens de entrada/salida/creación de
caché/lectura de caché, coste estimado, actividad de herramientas y salud de sesión. El gasto se
puede desglosar por usuario, por modelo y **por subagente** — justo el corte que interesa en un
equipo multi-agente.

**Tres niveles, según cuánto se quiera montar:**
- **`ccusage`** — CLI que lee los ficheros JSON locales de Claude Code y saca informes por día/
  semana/mes, todo local, cero setup. Para empezar mañana.
- **Monitor en vivo** (p.ej. Claude-Code-Usage-Monitor) — tasa de quemado en tiempo real durante un
  fan-out.
- **Stack OTel** → colector + Prometheus + Grafana, o SigNoz — histórico, dashboards por unidad,
  alertas de gasto. Hay stacks listos con Docker Compose (`claude-code-otel`, `cc-metrics`). Encaja
  en vps2.

**Dónde sí cabe "algo tipo agente": el hook de presupuesto.** No mide, **actúa** sobre la medición.
Un hook que lee el burn rate o el acumulado y **para el fan-out** de una unidad que cruza su
presupuesto. Mismo patrón que `check-ownership.sh`: consulta la métrica → `exit 2`. Es el "presupuesto
de tokens por agente" del §4.ter del informe, materializado como enforcement determinista.

**Atadura al contrato.** Un campo `presupuesto` (y/o `wip`, ver §2) por unidad en `particion.json`
haría el límite configurable por proyecto en vez de hardcodeado.

**Cautela técnica.** Claude Code **no** pasa las variables `OTEL_*` a los subprocesos que spawnea
(Bash, hooks, MCP, language servers). La telemetría del proceso principal sí cubre a sus subagentes
—por eso existe el desglose por subagente—, pero una app que un agente lance vía Bash no hereda el
endpoint y habría que instrumentarla aparte. Para medir el consumo *de los agentes*, basta el proceso
principal.

**Referencia de magnitud.** El uso de Claude Code ronda los ~6 USD por desarrollador y día a precio
de API; multiplicado por N agentes en paralelo, el dato deja de ser decorativo.

**Estado:** idea. No implementado. Prerrequisito natural: el límite de WIP (§2), que da el sitio
donde colgar el presupuesto.

---

## 2. Límite de WIP (work in progress) — Kanban

El corazón que hoy le falta al Kanban continuo del kit. Dos niveles:
- **WIP global** = nº de agentes/worktrees en paralelo. Es el dial que ata paralelismo, coste y
  riesgo de merges conflictivos (sweet spot ~3-5; coste lineal).
- **WIP por unidad** = idealmente 1 tarea `[EN CURSO]` por agente: terminar antes de empezar, que es
  lo que en Kanban expone los cuellos de botella.

**Implementación esbozada:** campo `wip` en `particion.schema.json` + sección de política en el
PROTOCOLO + enforcement ligero en `/coordinar` (no spawnear más de N subagents; no asignar segunda
tarea a una unidad que ya tiene una en curso).

**Estado:** esbozado, candidato a próxima rama. Habilita el hook de presupuesto del §1.

---

## 3. Métricas de flujo Kanban

Cycle time (de `[ABIERTO]` a `[HECHO]`) y detección de cuello de botella (qué unidad acumula cola).
Derivable de los timestamps de `_triage_log.md` y de los estados de las bandejas, sin instrumentación
nueva. Refinamiento de Kanban maduro, no esencial para operar.

**Estado:** idea.

---

## 4. Gate de cierre — `check-cierre.sh`

`/emitir-nativo` **describe** pero no incluye el hook `SubagentStop`/`TaskCompleted` que rechaza el
cierre de una tarea (`exit 2`) si el diff de la rama tocó una zona caliente sin pasar por integrador
o introdujo una migración. Es la red de seguridad del **lado de salida**, complementaria al test SPEC
del lado de entrada (`/productor`).

**Estado:** descrito en `commands/emitir-nativo.md`; el script no está escrito.

---

## 5. Retirada del motor legacy

Cuando agent teams deje de ser experimental: jubilar `/coordinar`, `/coordinar-bucle`, `/inbox`, las
bandejas `.claude/inbox/` y `_peticiones.md` — su función la dan la task list + el mailbox nativos.
Se conserva el diferencial: `particion.json`, el arquitecto (`/inferir-organizacion`, `/reinferir`)
y la capa de producto. El pivote (`/emitir-nativo`) ya deja esto preparado; sería la retirada final.

**Estado:** pendiente de que agent teams madure.

---

## 6. Adopción de agent teams — en espera

Aparcado por decisión consciente, no por timidez: agent teams **no aísla a los teammates en
worktrees** (perderíamos el ownership disjunto, la mejor garantía del kit) y nuestra coordinación es
en **estrella** (todo pasa por el integrador/arquitecto), no en malla, así que el mailbox entre
iguales aporta poco aquí. Refuerzan la espera las cautelas del §4.bis del informe (sin validación
entre pasos los errores se propagan en dominó; coste real elevado; el lead tiende a no delegar).

**Reevaluar** cuando salga de experimental, y solo si aparece un flujo que de verdad necesite que dos
unidades negocien entre sí sin pasar por el integrador. Hasta entonces, subagents `isolation:
worktree` + hooks (estables, sin flag) son el camino.

**Estado:** vigilancia.

---

## Considerado y descartado

- **Sprints de Scrum.** Se evaluó añadir un artefacto `sprint` con planning/review/cierre temporal.
  Descartado al elegir **Kanban continuo**: Scrum es también un patrón en estrella (centro = backlog,
  no un canal entre agentes), así que no aportaba topología nueva, solo cajas temporales que encajan
  mal con el flujo continuo de un equipo de agentes. El "release" es cruzar criterios de aceptación
  en `/aceptar`, no el fin de una iteración.
