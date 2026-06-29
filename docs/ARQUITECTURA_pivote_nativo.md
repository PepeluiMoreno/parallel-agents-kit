# Arquitectura del pivote a nativo — del motor propio a config generada

> Complementa `COMPARATIVA_AGENT_TEAMS.md` (el *por qué*) con el *cómo*. Lo materializa
> `/emitir-nativo`. Fecha: 2026-06-28.
>
> **⚠️ Actualización (2026-06-29).** Donde este doc dice que el camino a agent teams (mailbox real
> entre teammates) «espera a que madure» (tabla §"Mapeo", fila *Bandejas + encaminamiento*; y
> §"Estado y cautelas"), léase a la luz de `ADR-topologia-estrella-no-teams.md`: la malla **no es el
> destino aplazado**. La topología es en **estrella** (integrador + contrato + backlog) por diseño;
> las bandejas/encaminamiento se jubilan a favor de subagents `isolation: worktree` + hooks, **no**
> a favor del mailbox de teams. El resto del *cómo* (mapeo contrato→nativo, ownership por hook) es
> correcto y no cambia.

## Idea

El kit nació reimplementando a mano una orquestación que Claude Code ya trae nativa. La comparativa
concluyó que sólo dos cosas son diferencial nuestro: **el arquitecto que infiere la partición** y la
**capa de producto**. El pivote consiste en **conservar esas dos** y dejar de mantener el resto,
generando la maquinaria de orquestación como **configuración nativa** a partir del mismo
`particion.json` que ya producimos.

Clave del diseño: `particion.json` no cambia. Sigue siendo la fuente de verdad, editable a mano,
versionada. Lo que cambia es su *consumidor*: antes `/desplegar-equipo` materializaba protocolo +
bandejas + worktrees a mano; ahora `/emitir-nativo` lo traduce a subagent-definitions + hooks.

## Mapeo contrato → nativo

| Concepto del contrato | Artefacto nativo generado | Quién lo impone |
|---|---|---|
| Unidad `self` + `posee` | `.claude/agents/<unidad>.md` con `isolation: worktree` | Claude Code crea el worktree al spawnear |
| Ownership (globs disjuntos) | hook **PreToolUse** `check-ownership.sh` en cada agente | el hook (exit 2 si el path no es suyo) |
| Zonas calientes | mismo hook PreToolUse (bloquea) + rol integrador | el hook + el integrador como único dueño |
| Rol integrador | `.claude/agents/integrador.md` (opus, sin `isolation`, sin hook de ownership) | definición del agente |
| Migración = zona caliente de escritura | regla en el prompt del integrador + gate SubagentStop | ADR-migraciones + hook de cierre |
| Criterios de aceptación | hook **SubagentStop**/`TaskCompleted` (exit 2 = no cierra) | el hook |
| `runtime.loop: freno` | hook **TeammateIdle** (exit 2 = sigue; para antes de lo irreversible) | el hook |
| Bandejas + encaminamiento | **task list + mailbox nativos** (agent teams) | Claude Code |

## Por qué el ownership va en un hook y no en el prompt

Decir "edita solo tus ficheros" en el system prompt es una norma que el modelo *puede* saltarse. Un
**PreToolUse** que devuelve exit 2 es un muro: la escritura no ocurre. El script deriva la unidad de
la rama (`feature/<unidad>`), lee sus globs de `particion.json`, y rechaza cualquier path fuera o en
zona caliente. Enforcement por configuración, no por confianza — que es justo lo que la comparativa
echaba en falta en agent teams ("no impone ownership; queda en el prompt").

## Qué se mantiene y qué se jubila

**Se mantiene (no existe nativo):**
- `particion.json` + schema.
- Arquitecto: `/inferir-organizacion`, `/reinferir`.
- Capa de producto: `/productor`, `/aceptar`, backlog en `.claude/producto/`.

**Se jubila al adoptar nativo (lo da la task list + mailbox):**
- Bandejas `.claude/inbox/`, `_peticiones.md` + encaminamiento.
- `/coordinar`, `/coordinar-bucle`, `/inbox`.

`/emitir-nativo` **no borra** lo jubilado: lo marca legacy. La retirada se hace cuando agent teams
deje de ser experimental, no antes (hoy el motor de subagents estables sigue siendo el camino sin
flag).

## Estado y cautelas

- **Agent teams es experimental** (flag `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`). El pivote a
  subagents `isolation: worktree` + hooks **no** necesita el flag y es estable hoy. El de agent teams
  (mailbox real entre teammates) espera a que madure.
- `--agent <name>` no respeta `isolation: worktree` en algunas versiones (bug conocido): el
  aislamiento fiable es vía la herramienta Agent (subagent spawneado), no como agente principal.
- La sintaxis de hooks/frontmatter puede cambiar: `/emitir-nativo` verifica la doc vigente antes de
  emitir.
