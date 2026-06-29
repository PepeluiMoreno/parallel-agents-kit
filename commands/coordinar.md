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
2. **Encamina las peticiones pendientes entre miembros.** Lee `.claude/inbox/_peticiones.md`: es la
   bandeja donde los agentes dejan peticiones de trabajo que cae en OTRA unidad (sin tener que
   adivinar el destinatario). Para cada entrada `[POR ENCAMINAR]`:
   - decide la unidad dueña usando el mapa de ownership de `.claude/PROTOCOLO_MULTIAGENTE.md` §2
     (tú tienes el mapa completo; el emisor puede no tenerlo),
   - copia la petición como `[ABIERTO]` en `.claude/inbox/<unidad-dueña>.md`,
   - marca la entrada original `[ENCAMINADO → <unidad>]`.
   Si una petición es de zona caliente pura (router/schema raíz, redactar/aplicar migración…), va a
   `integrador.md`, no a una unidad. **Caso típico: un cambio de esquema.** Si la unidad X necesita
   tablas nuevas cuyo modelo vive en otra unidad (p.ej. `core`/modelos), la petición se encamina a
   esa unidad dueña del modelo: ella diseña y commitea el **modelo** en su rama y deja una petición
   de cableado describiendo el cambio de esquema. **La migración la redacta y aplica SOLO el
   integrador**, una única vez al integrar, para no acabar con dos heads de Alembic en paralelo (ver
   `docs/ADR-migraciones-zona-caliente.md`).
3. **Decide el work-list.** `git worktree list` y, por cada unidad `self`, lee su bandeja
   `.claude/inbox/<unidad>.md` (ya incluye lo recién encaminado); reúne las entradas `[ABIERTO]`.
   Unidad sin tareas → no se lanza. Si el usuario dio tareas directas, úsalas (y encólalas si no
   estaban).
   - **Auto-desbloqueo de dependencias (radial).** Una tarea `[ABIERTO]` con línea
     `**Depende de:** <ids>` **NO es elegible** hasta que TODAS esas tareas estén `[HECHO]` (búscalas
     por id en las bandejas de cualquier unidad). Si alguna sigue pendiente, **sáltala esta ronda** y
     anótalo al usuario (`tarea X esperando a Y`). El desbloqueo lo arbitras tú, el integrador, al
     leer el estado del backlog —no lo negocian las unidades entre sí (estrella, no malla;
     `docs/ADR-topologia-estrella-no-teams.md`)—. `**Depende de:** —` o sin línea = sin dependencias.
     Cautela: si detectas un ciclo (X espera a Y e Y espera a X, directa o transitivamente), no lo
     lances; repórtalo como descomposición a corregir, porque ninguna de las dos se desbloquearía.
   - **Aplica el WIP por unidad** (`runtime.wip.por_unidad`, o el `wip` propio de la unidad;
     default 1): de las tareas **ya elegibles**, a cada unidad le asignas en esta ronda como mucho ese
     nº, y no le lanzas nada si ya tiene una `[EN CURSO]` sin cerrar. Termina antes de empezar.
4. **Lanza un subagente por unidad con trabajo, EN PARALELO** (todas las llamadas Agent en un solo
   mensaje), **hasta el límite de WIP global** (`runtime.wip.global`, default 4). Si hay más unidades
   con `[ABIERTO]` que ese límite, lanza solo las `wip.global` de mayor prioridad y deja el resto en
   cola para la ronda siguiente (anótalo al usuario). Es el dial coste↔riesgo: no abanicas 8 agentes
   porque puedas. Para cada unidad `<U>` con worktree en `<base_worktrees>/<U>`:
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
     - NO crees migraciones. Si tu cambio toca el esquema (tablas/campos/índices nuevos), deja el
       MODELO commiteado en tu rama y solicita al integrador, vía bloque [PENDIENTE] en
       integrador.md, que redacte la migración (es zona caliente de escritura: redactarla en
       paralelo produce heads divergentes de Alembic). NO mergees. NO arranques tu propio stack.
     - Commitea en tu rama con `tipo(<U>): descripción` + el cierre de commit del repo.
     - Al terminar cada tarea, márcala [HECHO] en .claude/inbox/<U>.md con el hash y una línea.
     - [TRIAJE DESDE SUBAGENTES, si runtime.triaje_desde_subagentes==true] Si tu tarea requiere
       trabajo que cae en OTRA unidad, NO la invadas y NO adivines quién es el dueño: deja una
       entrada [POR ENCAMINAR] en .claude/inbox/_peticiones.md (formato en inbox/_README.md)
       describiendo QUÉ hace falta y POR QUÉ; el orquestador la encaminará a la unidad correcta en
       la siguiente ronda. Si lo sabes con certeza, puedes sugerir destinatario, pero no es
       obligatorio. Caso típico: necesitas tablas/campos nuevos cuyo MODELO vive en otra unidad
       (p.ej. core) → deja la petición describiendo las tablas/campos; la unidad dueña del modelo
       creará el MODELO. La migración la redactará el integrador. Tú NO creas modelos de otra unidad
       ni migraciones de ninguna.

     TUS TAREAS:
     <pega las entradas [ABIERTO] de su bandeja, o la tarea directa del usuario>

     Cuando acabes DEVUELVE un resumen: tareas cerradas, hashes, cableados dejados en
     integrador.md, peticiones dejadas en _peticiones.md, y qué quedó sin terminar y por qué.
     ```
5. **Recoge resultados** y resume al usuario por unidad. Si algún subagente dejó nuevas peticiones
   en `_peticiones.md`, anótalo: se encaminarán en la próxima ronda (o, si quieres cerrarlas ya,
   vuelve al paso 2 y lanza otra ronda para las unidades recién encargadas).
6. **Integra (tú, como siempre):** `/aplicar-integracion` — mergea ramas, aplica cableados de integrador.md,
   reconcilia, redacta y aplica la migración una sola vez, valida el stack.

## Por qué es seguro
Cada subagente queda confinado a su worktree y a su ownership → no se pisan. Solo tú tocas zonas
calientes y migras → sin heads divergentes ni conflictos de cableado. El modo clásico (una ventana
por unidad con `/inbox`) sigue siendo válido; esto es una alternativa ergonómica.

$ARGUMENTS
