# Rama `feature/wip-kanban`

> Documento maestro de la rama. Base: `master` (8a29b52). Fecha: 2026-06-28.
> Implementa el §2 del backlog `docs/POSIBLES_COMPLEMENTOS.md` y fija la metodología del kit.

## Resumen en una frase

Da al kit el control de **Work In Progress** que le faltaba para operar de verdad en **Kanban
continuo**, y declara esa metodología como el propósito explícito del proyecto.

## Por qué

El kit ya era Kanban continuo de hecho (flujo por bandejas, pull por unidad, estados explícitos),
pero sin la pieza central del método: el **límite de WIP**. En un equipo de agentes ese límite no es
higiene de proceso, es el dial que ata **paralelismo ↔ coste ↔ riesgo de merge** (el coste es lineal
con el nº de agentes) y la regla que **expone los cuellos de botella** en vez de esconderlos tras
tareas a medias.

## Qué entra

**Dos límites, configurables en el contrato (`runtime.wip`):**
- **global** (default 4) — nº de unidades/subagentes en paralelo por ronda. Si hay más unidades con
  trabajo, se sirven por prioridad y el resto espera. Es el freno de gasto y de cola de integración.
- **por_unidad** (default 1) — tareas `[EN CURSO]` por agente a la vez. 1 = terminar antes de
  empezar. Una unidad puede sobreescribirlo con su propio campo `wip`.

**Declaración de metodología:** Kanban continuo, escrito en el README (propósito del proyecto) y en
la cabecera del PROTOCOLO (contrato de trabajo del equipo). Sin sprints; el "release" es cruzar
criterios de aceptación en `/aceptar`.

## Cambios por commit

```
feat(schema):    runtime.wip { global, por_unidad } + override wip por unidad
docs(ejemplo):   runtime.wip en la partición de ejemplo
feat(protocolo): declara Kanban continuo + política de WIP (§7) con placeholders
                 {{WIP_GLOBAL}}/{{WIP_POR_UNIDAD}}; desplegar-equipo los rellena
feat(coordinar): enforcement — WIP por unidad (paso 3) y WIP global (paso 4)
docs:            propósito Kanban en README + defaults en /inferir-organizacion + esta nota
```

## Cómo se impone

- **WIP por unidad:** `/coordinar` paso 3 — no asigna más de N tareas a una unidad por ronda ni le
  lanza nada si ya tiene una `[EN CURSO]`.
- **WIP global:** `/coordinar` paso 4 — no lanza más de `wip.global` subagentes a la vez; el exceso
  espera a la ronda siguiente.
- El arquitecto (`/inferir-organizacion`) rellena los defaults (4/1); `/desplegar-equipo` los vuelca
  al PROTOCOLO concreto.

## Qué NO toca

- No añade enforcement por hook (el límite vive en `/coordinar`, que es quien hace el fan-out). Un
  hook de presupuesto por tokens —complementario, §1 del backlog— queda pendiente y se apoyaría en
  este mismo `wip`.
- No regenera el manual PDF (`docs/manual/`). **Pendiente:** reflejar la metodología Kanban y la
  política de WIP.

## Cómo probarlo

1. `/inferir-organizacion` sobre un repo → confirma que el `particion.json` trae `runtime.wip {4,1}`.
2. `/desplegar-equipo` → el PROTOCOLO §7 muestra los límites concretos.
3. Encola `[ABIERTO]` en 6 unidades con `wip.global=4` → `/coordinar` lanza 4 y deja 2 en cola.
4. Da 2 tareas a una unidad con `por_unidad=1` → `/coordinar` le asigna 1 y deja la otra.

## Cómo revertir

Cada commit es independiente; `git revert <hash>`. El schema es retrocompatible: `runtime.wip` es
opcional y los consumidores aplican defaults si falta, así que revertir el enforcement no rompe
contratos existentes.
