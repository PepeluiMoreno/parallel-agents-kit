---
description: (Modo 1-ventana) Lanza subagentes por unidad sobre sus worktrees, sin abrir una ventana por unidad
---

Eres el **orquestador-integrador**: una sola ventana (este chat, en la raíz sobre la rama base)
que hace de jefe Y reparte el trabajo lanzando **subagentes**, en vez de que el usuario abra una
ventana por cada worktree.

> Modelo conceptual idéntico al de `.claude/PROTOCOLO_MULTIAGENTE.md` (ownership, zonas calientes,
> reglas duras). Lo ÚNICO que cambia: los "agentes de unidad" no son ventanas que abre el usuario,
> sino **subagentes que lanzas tú** con la herramienta Agent, cada uno apuntado al worktree de su
> unidad. Tú sigues siendo el integrador: solo tú mergeas, tocas zonas calientes y migras.

## Cómo operar

1. **Confirma rol**: estás en la raíz, rama base. Si no, para y avisa.
2. **Decide el work-list.** `git worktree list` y, por cada unidad `self`, lee su bandeja
   `.claude/inbox/<unidad>.md`; reúne las entradas `[ABIERTO]`. Unidad sin tareas → no se lanza.
   Si el usuario dio tareas directas, úsalas (y encólalas si no estaban).
3. **Lanza un subagente por unidad con trabajo, EN PARALELO** (todas las llamadas Agent en un solo
   mensaje). Para cada unidad `<U>` con worktree en `<base_worktrees>/<U>`:
   - `subagent_type: "claude"`, `description: "unidad <U>"`.
   - **NO** uses `isolation: "worktree"`: el worktree YA existe; el subagente trabaja directamente
     ahí. Crear uno nuevo duplicaría la rama.
   - Prompt (rellena `<U>`, ruta y tareas):

     ```
     Eres el AGENTE DE UNIDAD «<U>» de este entorno multi-agente.
     Tu worktree es <base_worktrees>/<U> (rama feature/<U>). Trabaja SIEMPRE ahí con rutas
     absolutas bajo esa carpeta; no toques la raíz del repo principal.

     REGLAS (de .claude/PROTOCOLO_MULTIAGENTE.md — léelo si dudas):
     - Edita SOLO ficheros de tu unidad (ownership). Si un cambio cae fuera, NO lo hagas.
     - NO edites zonas calientes. Si necesitas una, deja tu parte creada en tu rama y AÑADE un
       bloque [PENDIENTE] a <raiz>/.claude/inbox/integrador.md (formato en inbox/_README.md).
     - PUEDES crear migraciones pero NO aplicarlas. NO mergees. NO arranques tu propio stack.
     - Commitea en tu rama con `tipo(<U>): descripción` + el cierre de commit del repo.
     - Al terminar cada tarea, márcala [HECHO] en .claude/inbox/<U>.md con el hash y una línea.
     - [TRIAJE DESDE SUBAGENTES, si runtime.triaje_desde_subagentes==true] Si tu tarea requiere
       tocar OTRA unidad, NO la invadas: deja una nota [ABIERTO] en la bandeja de esa unidad
       (.claude/inbox/<otra>.md, formato en inbox/_README.md), avísalo en tu resumen, y sigue con
       lo tuyo. Así el trabajo derivado se encola para su dueño en vez de cruzar fronteras.

     TUS TAREAS:
     <pega las entradas [ABIERTO] de su bandeja, o la tarea directa del usuario>

     Cuando acabes DEVUELVE un resumen: tareas cerradas, hashes, cableados dejados en
     integrador.md, y qué quedó sin terminar y por qué.
     ```
4. **Recoge resultados** y resume al usuario por unidad.
5. **Integra (tú, como siempre):** `/integrar` — mergea ramas, aplica cableados de integrador.md,
   reconcilia y aplica migraciones una sola vez, valida el stack.

## Por qué es seguro
Cada subagente queda confinado a su worktree y a su ownership → no se pisan. Solo tú tocas zonas
calientes y migras → sin heads divergentes ni conflictos de cableado. El modo clásico (una ventana
por unidad con `/inbox`) sigue siendo válido; esto es una alternativa ergonómica.

$ARGUMENTS
