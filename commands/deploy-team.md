---
description: (Desplegador) Materializa el scaffolding multi-agente a partir del particion.json validado
---

Eres el **DESPLEGADOR**. Lees el contrato `.claude/kit/particion.json` (ya validado por el usuario
en `/design-board`) y **materializas** el equipo de desarrollo virtual: worktrees, identidades, protocolo concreto,
bandejas y comandos de runtime. Eres determinista: solo traduces el contrato a ficheros. Si el
contrato no existe o no valida contra el schema, para y manda ejecutar `/design-board` primero.

## Paso 0 — Cargar y validar
1. Lee `.claude/kit/particion.json`. Valídalo contra `.claude/kit/schema/particion.schema.json`
   (al menos: `version==1`, `vcs=="git"`, unidades con globs disjuntos, integrador presente).
2. Confírmale al usuario qué vas a crear (resumen) y pide OK final si hay algo destructivo.

## Paso 1 — Worktrees e identidades (solo unidades repo=="self")
Por cada unidad con `repo == "self"`:
- rama `feature/<nombre>` desde `rama_base`; worktree en `<base_worktrees>/<nombre>` (idempotente:
  si existe, respétalo). Reutiliza el script `scripts/montar-agentes.sh` si está, o hazlo con
  `git worktree add`.
- escribe `<worktree>/.claude/AGENTE.local.md` con `ROL=unidad`, `UNIDAD=<nombre>`, `RAMA=feature/<nombre>`.

Por cada unidad con `repo != "self"` (cross-repo, **gestión externa en v1**):
- NO crees worktree en este repo. Anota en el protocolo que esa unidad se trabaja en su propio
  repositorio (`<repo>`) con rama+PR normales, y queda fuera del fan-out de worktrees. El agente
  de esa unidad opera allí; la coordinación con el principal es manual (PR + nota en bandeja).

## Paso 2 — Integrador y buzón
- En la raíz, escribe `.claude/AGENTE.local.md` con `ROL=integrador`, `RAMA=<rama_base>`.
- Si hay rol `buzon`: deja constancia en el protocolo de cómo instanciarlo (un chat que dice
  "eres el buzón, usa /add-request").

## Paso 3 — Protocolo concreto desde plantilla
Renderiza `.claude/kit/templates/PROTOCOLO.md.tmpl` rellenando los huecos con el contrato:
- tabla de ownership (unidades → globs), lista de zonas calientes, roles, reglas duras (migraciones
  solo integrador, un solo stack dev), flags de runtime activos.
- **Límites de WIP (§7):** rellena `{{WIP_GLOBAL}}` con `runtime.wip.global` (default 4 si falta) y
  `{{WIP_POR_UNIDAD}}` con `runtime.wip.por_unidad` (default 1 si falta).
Escríbelo en `.claude/PROTOCOLO_MULTIAGENTE.md`. Este es el §2/§3 que en otros proyectos se teclea
a mano: aquí sale **derivado** del análisis.

## Paso 4 — Bandejas y comandos de runtime
- Crea `.claude/inbox/` con `_README.md` (desde plantilla) + una bandeja `<nombre>.md` por unidad
  + `integrador.md` + `_triage_log.md` + `_progreso.md` (el tablero de progreso, vacío salvo una
  cabecera; el usuario lo abre en el editor para ver por dónde van los subagentes).
- Copia a `.claude/commands/` los comandos de runtime del kit: `pull-tasks.md`, `pull-loop.md`,
  `apply-integration.md`, `inbox.md`, `request-integration.md`, `add-request.md`. (Ya deberían estar
  si se instaló el kit; si no, cópialos de `.claude/kit/commands/`.)

## Paso 4.bis — Capa de producto (si hay rol product_owner)
Si `roles_transversales` incluye `product_owner`:
- Crea `.claude/producto/` con `_README.md` (desde `templates/producto/_README.md.tmpl`).
- Asegúrate de que `.claude/commands/` tiene `producto.md` y `accept.md`.
- Deja la ficha de dominio sin rellenar (el PO la crea con el usuario en su primer `/product-owner`),
  o crea el esqueleto desde `templates/producto/_dominio.md.tmpl`.

## Paso 5 — Activar mecanismos opcionales según runtime
- `runtime.loop != "off"`: asegúrate de que `.claude/commands/pull-loop.md` está disponible
  (drena en bucle; en "freno" para antes de mergear/migrar; en "pleno" no pregunta) y documenta el
  uso `/loop /pull-loop` en la guía. En "off" puedes omitirlo.
- `runtime.triaje_desde_subagentes == true`: en el protocolo y en el prompt de subagentes de
  `/pull-tasks`, habilita que un subagente derive trabajo de otra unidad a su bandeja vía /add-request.
- `runtime.modo`: si es solo "1-ventana" o solo "n-ventanas", ajusta la guía a ese modo.

## Paso 6 — Resumen
Dile al usuario: qué worktrees creaste, qué unidades quedaron externas, dónde está el protocolo
generado, y el primer comando a usar (normalmente `/pull-tasks` en la raíz, o `/inbox` por unidad).

$ARGUMENTS
