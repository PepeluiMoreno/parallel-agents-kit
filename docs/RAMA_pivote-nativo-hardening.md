# Rama `feature/pivote-nativo-hardening`

> Documento maestro de la rama. Resume qué entra, por qué, cómo probarlo y cómo revertirlo.
> Base: `master`. Autoría: PepeluiMoreno + Claude Opus 4.8. Fecha: 2026-06-28.

## Resumen en una frase

Endurece el kit en dos frentes derivados del análisis de `COMPARATIVA_AGENT_TEAMS.md`: **(a)** cierra
los puntos débiles del motor actual (migraciones, deriva de la partición, validación de tareas) y
**(b)** abre el camino del pivote a config nativa de Claude Code, conservando sólo el diferencial
real del kit.

## Por qué

La comparativa ya había concluido que el núcleo de orquestación del kit es nativo y que el valor
propio son dos cosas: el **arquitecto que infiere la partición** y la **capa de producto**. Esta
rama actúa sobre esa conclusión sin tirar nada que hoy funcione: refuerza el diferencial y prepara el
relevo del motor manual, dejándolo para cuando agent teams deje de ser experimental.

## Los cuatro cambios

### 1. Migraciones como zona caliente *de escritura* — `refactor(protocolo)`
**Problema:** la regla previa dejaba que cada unidad creara su migración en su rama; al integrar dos
ramas que tocaron esquema en paralelo aparecían **dos heads de Alembic** colgando del mismo padre, y
reconciliarlos es trabajo manual del DAG (no un merge de texto).
**Cambio:** la unidad commitea sólo el **modelo**; el **integrador redacta y aplica una única
migración** sobre el estado ya integrado → nace con un solo head, nada que reconciliar.
**Ficheros:** `pull-tasks.md`, `apply-integration.md`, `request-integration.md`,
`design-board.md`, `PROTOCOLO.md.tmpl`. Decisión y reversión en
`docs/ADR-migraciones-zona-caliente.md`.

### 2. `/sync-board` — `feat(sync-board)`
**Problema:** el arquitecto infiere la partición una vez, pero el repo deriva y `particion.json` se
desincroniza en silencio (globs huérfanos, código nuevo sin dueño, solapamientos).
**Cambio:** comando que hace diff entre la partición vigente y `git ls-files`, clasifica la deriva por
severidad y propone un parche (con diff) para validar. No despliega.
**Ficheros:** `commands/sync-board.md`.

### 3. Pivote a config nativa — `feat(generate-config)`
**Problema:** mantener un motor de orquestación propio reimplementa lo que Claude Code ya da.
**Cambio:** `/generate-config` traduce `particion.json` (que sigue siendo la fuente de verdad) a
subagent-definitions (`.claude/agents/<unidad>.md` con `isolation: worktree`) + hooks. El ownership
pasa a imponerlo un **hook PreToolUse** (`check-ownership.sh`), no la disciplina del prompt.
**Ficheros:** `commands/generate-config.md`, `templates/hooks/check-ownership.sh`,
`docs/ARQUITECTURA_pivote_nativo.md`.

### 4. Gate test SPEC en el Product Owner — `feat(product-owner)`
**Problema:** una tarea mal definida encolada arruina el fan-out (agentes a tiempos dispares, merges
conflictivos); y "si un agente dice listo, el lead se lo cree".
**Cambio:** ninguna tarea entra al backlog sin pasar el test **SPEC** (Específica · Programáticamente
evaluable · alcance Explícito · aCotada); los criterios de aceptación deben ser evaluables, no
subjetivos.
**Ficheros:** `commands/product-owner.md`.

## Qué NO toca esta rama

- No borra el motor manual (`/pull-tasks`, bandejas, `_peticiones.md`): queda operativo y estable
  (sin flag). El pivote lo marca "legacy"; su retirada es una decisión posterior.
- No regenera el manual PDF (`docs/manual/`). **Pendiente:** regenerar con `gen_pdf.py` para reflejar
  `/sync-board` y `/generate-config` en la tabla de comandos y la nueva sección de pivote.
- No modifica el schema `particion.schema.json`: los cambios son de protocolo/runtime, no de datos.

## Cómo probarlo (en SIGA como piloto)

1. `git switch feature/pivote-nativo-hardening` en el repo del kit.
2. `./install.sh /opt/docker/apps/SIGA` para refrescar `.claude/` con los comandos nuevos.
3. `/sync-board` sobre SIGA → confirma que la partición vigente cubre el repo (o ver el parche).
4. `/generate-config` → genera `.claude/agents/*.md` + hooks; revisa que `check-ownership.sh` rechaza
   una escritura fuera de unidad (prueba: en una rama `feature/economico`, intenta editar un fichero
   de `membresia` → exit 2).
5. Un ciclo de `/product-owner` → comprueba que rechaza una tarea vaga hasta reescribirla.

## Cómo revertir

Cada cambio es independiente y revertible por commit:
```
git revert <hash>        # uno de los 4, sin tocar los demás
```
La reversión del cambio 1 (migraciones) está detallada en su ADR. Los cambios 2–4 sólo añaden
ficheros o amplían comandos; revertirlos no afecta al motor existente.

## Commits

```
refactor(protocolo): migraciones como zona caliente de escritura
feat(sync-board): comando para resincronizar la partición con el repo
feat(generate-config): genera config nativa (subagents + hooks) desde la partición
feat(product-owner): gate test SPEC en la descomposición de tareas
```
