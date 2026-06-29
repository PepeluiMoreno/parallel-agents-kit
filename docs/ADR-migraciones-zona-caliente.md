# ADR · Las migraciones son zona caliente *de escritura* (las redacta el integrador)

> Estado: **aceptada** · Fecha: 2026-06-28 · Ámbito: protocolo de coordinación multi-agente
> Reemplaza la regla previa "una unidad puede *crear* una migración en su rama, pero no aplicarla".

## Contexto

El kit aísla a cada unidad en su propio worktree y rama `feature/<unidad>`. Eso hace seguro el
paralelismo **a nivel de ficheros de código**: dos unidades con globs `posee` disjuntos no se pisan.

Las migraciones de base de datos no encajan en ese modelo. Una migración de Alembic (igual Prisma,
Liquibase…) no es un fichero independiente: es un **nodo de un DAG** encadenado por `down_revision`.
Cada migración declara de qué `revision` anterior parte. El conjunto de migraciones tiene, en estado
sano, **un único head** (la punta de la cadena).

La regla anterior permitía que cada unidad *creara* su migración en su rama (sin aplicarla) y que el
integrador la *aplicara* al integrar. El problema aparece al integrar dos ramas que crearon
migración en paralelo:

- la unidad A, partiendo del head `abc`, crea `def` (`down_revision = abc`);
- la unidad B, partiendo **del mismo** head `abc`, crea `ghi` (`down_revision = abc`).

Al mergear ambas ramas, el árbol de versiones tiene **dos heads** (`def` y `ghi`) colgando del mismo
padre. Alembic se niega a aplicar con multiples heads. Reconciliarlo **no es un merge de texto**: hay
que crear una migración de fusión (`alembic merge`) o reescribir el `down_revision` de una de ellas
para serializarlas, decidiendo a mano el orden correcto cuando las dos tocan tablas relacionadas. Es
precisamente el tipo de trabajo manual, frágil y propenso a error que el kit existe para evitar. Con
Supabase/Postgres y FKs entre módulos (p.ej. económico ↔ membresía en SIGA) el riesgo es real, no
teórico.

## Decisión

**El directorio de versiones de migraciones es zona caliente de _escritura_, no solo de
aplicación.** Las unidades **no crean migraciones**: commitean sólo el **modelo** (la clase ORM, el
schema) en su rama. El **integrador**, una vez mergeadas todas las ramas sobre la base, **autogenera
una única migración** sobre el estado de modelos ya unido y la aplica una sola vez.

Flujo resultante para un cambio de esquema:

1. La unidad dueña del modelo crea/modifica la clase ORM en su rama y la commitea.
2. Deja un bloque `[PENDIENTE]` en `integrador.md` describiendo el cambio de esquema
   (`/request-integration`).
3. El integrador mergea la(s) rama(s), **autogenera una migración** contra los modelos integrados,
   la revisa, y la aplica una vez (`/apply-integration`, paso 4).

Como la migración se redacta **después** del merge, sobre un único estado de modelos, **nace con un
solo head**. No hay nada que reconciliar.

## Alternativas consideradas

- **Mantener "cada unidad crea su migración" + reconciliar al integrar.** Maximiza la autonomía de
  la unidad, pero traslada al integrador el trabajo manual de fusionar heads divergentes de Alembic
  en cada integración con cambios de esquema en ≥2 unidades. Rechazada: convierte el caso común
  (varias unidades tocan esquema en un sprint) en el caso doloroso.
- **Una unidad transversal `migraciones`, dueña única de `versions/`, que serializa.** Equivalente
  funcional a esta decisión, pero añade un rol más y una ronda de coordinación. El integrador ya es
  el dueño único de las zonas calientes y ya redacta el cableado: darle también la migración no
  añade un actor nuevo. Por eso se pliega sobre el integrador en vez de crear un rol aparte.

## Consecuencias

**A favor:**
- El árbol de migraciones nunca diverge: no hay `alembic merge` manual ni reordenado de
  `down_revision`.
- Una sola migración por integración, coherente con el conjunto, más fácil de revisar y revertir.
- La unidad razona sobre su dominio (el modelo), no sobre la mecánica global del DAG.

**En contra / límites:**
- La unidad **no puede probar su migración de forma aislada** en su worktree antes de integrar (no
  la tiene). Mitiga: el integrador valida el stack tras aplicar (paso 5 de `/apply-integration`),
  y la autogeneración desde modelos correctos es de bajo riesgo.
- Concentra un paso más en el integrador. Aceptable: ya es el cuello de botella consciente para todo
  lo irreversible (merge, cableado, migración, stack).

## Cómo revertir

Si en un proyecto concreto se prefiere el modelo anterior (autonomía total de la unidad), revertir
es local a estos puntos, sin tocar el motor:
- `templates/PROTOCOLO.md.tmpl` §1 y §6,
- `commands/pull-tasks.md` (prompt del subagente y paso 2),
- `commands/apply-integration.md` (paso 4),
- `commands/request-integration.md` (paso 2),
- `commands/design-board.md` (paso 2).

Devuelve a las unidades el permiso de crear migraciones y al integrador el de reconciliar heads.
