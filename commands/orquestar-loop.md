---
description: (Modo desatendido — FRENO) Drena las bandejas en bucle con subagentes, pero PARA antes de mergear/migrar
---

Eres el **orquestador en bucle, modo FRENO**. Es `/orquestar` repetido en el tiempo hasta vaciar
las bandejas, PERO con un freno de seguridad: **drenas tareas de unidad con subagentes solo; te
DETIENES y pides OK antes de cualquier merge/cableado/migración** (la parte irreversible que toca
la BD y las zonas calientes). Pensado para soltarlo con `/loop`:

```
/loop /orquestar-loop
```

## Cada vuelta del bucle
1. **Confirma rol:** raíz, rama base. Si no, para.
2. **Mira las bandejas** `.claude/inbox/<unidad>.md`. Reúne las entradas `[ABIERTO]` por unidad.
3. **¿Hay tareas?**
   - **No** → no lances nada. Informa "bandejas vacías, nada que drenar" y **autodetente el bucle**
     (loop-until-dry: no tiene sentido seguir latiendo). Si usaste `/loop`, dilo para que el usuario
     lo pare; no programes otra vuelta tú.
   - **Sí** → continúa.
4. **Fan-out (igual que `/orquestar`):** lanza EN PARALELO un subagente por unidad con tareas, cada
   uno apuntado a su worktree, con el prompt de subagente de `/orquestar` (incluida la cláusula de
   **triaje desde subagentes** si el runtime la tiene activada: una unidad que tope con trabajo de
   otra lo deja en la bandeja de esa otra en vez de invadirla).
5. **Recoge resultados.** Las unidades commitean en SUS ramas (eso es seguro y reversible). Resume
   por unidad qué se cerró.
6. **FRENO — aquí PARAS.** NO mergees, NO apliques cableados, NO corras migraciones por tu cuenta.
   En su lugar:
   - Lista lo que está **listo para integrar**: ramas que avanzaron, cableados encolados en
     `integrador.md`, migraciones nuevas creadas (sin aplicar).
   - **Pide OK explícito al usuario** para integrar (`/integrar`). Solo si lo da, integras.
   - Si el usuario no está o no responde, **deja todo encolado** y termina la vuelta sin integrar.

## Por qué FRENO y no pleno
El drenaje de tareas en worktrees es seguro (cada subagente confinado a su unidad, commits en su
rama). Lo peligroso es la integración: merges, cableado de zonas calientes y `migración` sobre la
BD compartida son difíciles de revertir. En modo freno, el bucle automatiza lo seguro y **mantiene
al humano en el lazo justo para lo irreversible**. (El modo `pleno` integraría sin preguntar; este
kit no lo activa salvo que `runtime.loop=="pleno"` y aun así se desaconseja para BD compartida.)

## Cadencia
Vaciar bandejas no es vigilar algo externo: usa pacing dinámico (que el modelo decida cuándo
re-despertar) en vez de un intervalo fijo corto. Y recuerda autodetenerte cuando no quede nada.

$ARGUMENTS
