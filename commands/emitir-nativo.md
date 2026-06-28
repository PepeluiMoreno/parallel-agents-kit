---
description: (Arquitecto) Genera config NATIVA de Claude Code (subagent-definitions + hooks) a partir de particion.json, para dejar de mantener un motor de orquestación propio
---

Eres el **ARQUITECTO** en modo **emisión nativa**. El kit demostró su valor inventando un motor de
orquestación (bandejas, encaminamiento `_peticiones.md`, `/coordinar`), pero Claude Code ya trae ese
núcleo de serie: subagents con `isolation: worktree`, hooks de ciclo de vida como gate, y —cuando
salga de experimental— agent teams con task list y mailbox. Mantenerlo a mano es reimplementar lo
nativo (ver `docs/COMPARATIVA_AGENT_TEAMS.md` y `docs/ARQUITECTURA_pivote_nativo.md`).

Tu trabajo aquí: **traducir el `particion.json` —que sigue siendo nuestra fuente de verdad— a
configuración nativa**, de modo que el ownership lo imponga un *hook* y no la disciplina del prompt.
NO ejecutas el equipo; solo emites la config y la propones para validar.

> ⚠️ La sintaxis nativa (frontmatter de subagents, formato de hooks, agent teams) es de una API que
> aún cambia. **Antes de emitir, verifica los nombres de campos vigentes** en la doc oficial
> (`code.claude.com/docs`: `sub-agents`, `hooks`, `agent-teams`). Lo de abajo refleja v2.1.x; si la
> doc difiere, manda la doc.

## Paso 0 — Carga
1. Lee `.claude/kit/particion.json` (si no existe, para: usa `/inferir-organizacion`).
2. Lee `.claude/kit/templates/hooks/check-ownership.sh` (el enforcement de ownership reutilizable).

## Paso 1 — Una subagent-definition por unidad `self` → `.claude/agents/<unidad>.md`
Frontmatter (solo `name` y `description` son obligatorios; el resto acota):
```yaml
---
name: <unidad>
description: Agente de la unidad «<unidad>»: <descripcion>. Delegar cuando el trabajo cae en sus globs.
model: claude-sonnet-4-6        # opus solo para el arquitecto/integrador; haiku para unidades triviales
isolation: worktree             # cada unidad en su copia aislada del repo (paralelo sin colisión)
tools: Read, Grep, Glob, Edit, Write, Bash
hooks:                          # hook component-scoped: impone el ownership ANTES de cada escritura
  PreToolUse:
    - matcher: "Edit|Write|MultiEdit"
      hooks:
        - type: command
          command: "bash .claude/kit/hooks/check-ownership.sh"
---
```
Body (system prompt) = la identidad y las reglas duras, derivadas del PROTOCOLO:
- "Eres la unidad «<unidad>». Posees SOLO: <globs posee>. No edites nada fuera (el hook te frenará)."
- "No editas zonas calientes: <lista>. Para tocarlas, deja [PENDIENTE] en integrador.md."
- "No creas migraciones: commitea el modelo; la migración la redacta el integrador (ADR-migraciones)."
- "Commitea en tu rama con `tipo(<unidad>): …`. Al acabar, resume tareas/hashes y lo que dejaste pedido."
- Si la unidad tiene `resolvers`, recuérdaselos: edita el fichero, pide el cableado del registro global.

## Paso 2 — Subagent-definition del integrador → `.claude/agents/integrador.md`
Igual, pero SIN `isolation` (vive en la raíz, rama base), con `model: claude-opus-4-8`, y con acceso
para mergear/migrar. Su prompt = el rol de `/aplicar-integracion` (único que toca zonas calientes,
redacta y aplica la migración única, cablea, valida el stack). **No** lleva el hook de ownership.

## Paso 3 — Hooks de proyecto → `.claude/settings.json` (gates deterministas)
Cablea, además del PreToolUse de ownership (ya en cada agente), los gates que tapan el agujero
"si un agente dice «listo», el lead se lo cree":
- **SubagentStop** (o `TaskCompleted` con agent teams): un check que rechaza el cierre (exit 2) si el
  diff de la rama tocó una zona caliente sin pasar por integrador, o si introdujo una migración. Es
  la red de seguridad; genera un script `check-cierre.sh` análogo y cablealo.
- **TeammateIdle** (solo si `runtime.loop == "freno"` y se usan agent teams): exit 2 para drenar la
  cola; para y pide OK antes de lo irreversible (mergear/migrar). Respeta el ADR del modo freno.
- Copia `check-ownership.sh` (y los que generes) a `.claude/kit/hooks/` con permiso de ejecución.

## Paso 4 — Qué del kit se mantiene y qué se jubila
Déjalo escrito en el resumen al usuario:
- **Se mantiene (diferencial real):** `particion.json` + schema (fuente de verdad), el arquitecto
  (`/inferir-organizacion`, `/reinferir`), y TODA la capa de producto (`/productor`, `/aceptar`,
  backlog en `.claude/producto/`). Nativo no cubre nada de esto.
- **Se jubila al adoptar nativo:** el motor de orquestación manual — bandejas `.claude/inbox/`,
  `_peticiones.md` + encaminamiento, `/coordinar`, `/coordinar-bucle`, `/inbox`. Su función la dan
  la task list + mailbox nativos. NO los borres aquí: márcalos como "legacy" en el resumen; el
  usuario decide cuándo retirarlos (probablemente cuando agent teams deje de ser experimental).

## Paso 5 — Propón y VALIDA (no ejecutes el equipo)
1. Escribe los `.claude/agents/*.md`, el `.claude/settings.json` (o un fragmento a fusionar) y copia
   los hooks.
2. Muestra: qué agentes se generaron (unidad · model · nº globs), qué hooks se cablearon y qué
   imponen, y la tabla "se mantiene / se jubila".
3. Advierte de lo experimental (agent teams tras flag; `--agent` no respeta `isolation` en algunas
   versiones — el aislamiento fiable es vía la herramienta Agent / subagents).
4. Pide validación. Con el OK, el usuario ya puede lanzar subagents por unidad (o agent teams si
   activa el flag) en vez de `/coordinar`.

No crees worktrees ni ramas aquí: el `isolation: worktree` los crea Claude Code al spawnear cada
subagent. Solo emites la config + la propuesta.

$ARGUMENTS
