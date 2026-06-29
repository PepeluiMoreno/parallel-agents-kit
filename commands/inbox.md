---
description: Lee tu bandeja de unidad y empieza a trabajar las tareas abiertas
---

Eres un agente de **unidad**. Atiende tu bandeja:

1. Lee `.claude/AGENTE.local.md` para saber tu `UNIDAD`. Si no existe o tu ROL no es `unidad`,
   dilo y para (este comando es solo para agentes de unidad).
2. Confirma que estás en tu worktree y rama: `git status` debe mostrar `feature/<UNIDAD>`.
3. Lee `.claude/inbox/<UNIDAD>.md`. Lista las entradas `[ABIERTO]`/`[EN CURSO]` con asunto y
   prioridad. Si está vacía, dilo y pregunta al usuario qué hacer.
4. Si hay tareas, propón orden (prioridad alta primero) y empieza por la primera:
   - cámbiala a `[EN CURSO]`,
   - resuélvela **solo en ficheros de tu unidad** (ownership en `.claude/PROTOCOLO_MULTIAGENTE.md`),
   - si necesitas una zona caliente, NO la edites: usa `/request-integration`,
   - al terminar, commitea con `tipo(<UNIDAD>): …`, marca `[HECHO]` y añade
     `**Resuelto:** <hash> · <qué hiciste>`.
5. Reglas duras: no mergeas, no aplicas migraciones, no arrancas tu propio stack. Eso es del integrador.

$ARGUMENTS
