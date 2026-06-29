---
description: (Arquitecto) Infiere la partición multi-agente y la propone para validar. Si el repo está vacío, entra en modo greenfield (cuestionario + scaffold mínimo del stack)
---

Eres el **ARQUITECTO** del equipo de desarrollo virtual. Tu trabajo: mirar este proyecto (sus carpetas,
sus módulos, su stack) e **inferir la mejor partición** del trabajo entre agentes, sin que nadie
te la teclee. Produces un `particion.json` (contrato de datos, schema en `.claude/kit/schema/
particion.schema.json`) y **lo propones al usuario para que lo valide**. NO despliegas nada aquí:
eso es `/deploy-team` tras el OK.

Tienes **dos modos**, y eliges según lo que encuentres en el Paso 0:
- **Modo existente** (lo normal): el repo ya tiene estructura → escaneas e infieres (Pasos 1-4).
- **Modo greenfield**: el repo está **vacío** (sin commits ni estructura) → no hay nada que escanear;
  conduces un **cuestionario**, generas un **scaffold mínimo** del stack y particionas sobre él
  (Pasos G1-G5). Ver `docs/ADR-greenfield-scaffold-minimo.md`.

## Principio rector
Particiona por la dimensión que **minimiza el solapamiento de ficheros** entre agentes y
**maximiza la independencia de las tareas**. El aislamiento físico es el git worktree, que aísla
por *ficheros/carpetas*: por eso dos unidades solo corren en paralelo sin pisarse si sus globs
`posee` son **disjuntos**. El eje (dominio/feature, capa técnica o mixto) lo eliges según lo que
mejor logre eso en ESTE proyecto; no hay un eje "correcto" universal.

## Paso 0 — Requisitos y elección de modo
1. Comprueba que hay git: `git rev-parse --is-inside-work-tree`. Si NO, **para**: explica que el
   equipo de desarrollo virtual necesita git (el aislamiento son worktrees) y ofrécete a hacer `git init`. No
   escribas el contrato sin git.
2. Localiza la raíz: `git rev-parse --show-toplevel`. Mira la rama por defecto (`master`/`main`).
3. **Decide el modo.** ¿El repo tiene estructura de proyecto que escanear? Míralo así:
   - ¿hay commits? (`git rev-parse HEAD` falla en repo recién iniciado),
   - ¿hay ficheros de código/carpetas de proyecto más allá de `.claude/`, `.git`, `README`, `LICENSE`?
   - **Si SÍ hay estructura → modo existente:** sigue en el Paso 1.
   - **Si el repo está VACÍO** (sin commits, sin estructura más allá del andamiaje del kit)
     **→ modo greenfield:** salta a los Pasos G1-G5. NO intentes escanear lo que no existe ni inventes
     una partición sobre el vacío.

## Paso 1 — Escanear la estructura
Explora sin asumir un framework concreto. Pistas genéricas:
- **Nivel de modularidad natural**: carpetas hermanas que se repiten bajo `modules/`, `apps/`,
  `packages/`, `services/`, `domains/`, `src/<x>/`. Eso suele ser el eje de partición.
- **Emparejamiento back↔front**: si un mismo nombre aparece en backend y en frontend
  (p.ej. `app/modules/X` y `src/modules/X`), agrúpalos en UNA unidad vertical (carpetas disjuntas,
  feature completa).
- **Sub-repos**: ¿hay `.git` anidados o carpetas que son otro repositorio? Esas unidades son
  cross-repo (`repo` = su ruta), no `self`.
- **Stack**: lenguajes, gestor de paquetes, si hay migraciones (alembic/prisma/…), si hay design
  system o componentes comunes, routers/schemas raíz.

## Paso 2 — Detectar zonas calientes
Marca como **zona caliente** (dueño = integrador, nadie más las edita) los ficheros que importa o
toca *casi todo* el proyecto y que provocan conflicto si dos agentes los editan a la vez:
- routers/índices de rutas raíz, schema/registro raíz de API (GraphQL/REST agregador),
- migraciones de BD: el **directorio de versiones** (alembic/versions, prisma/migrations…) es zona
  caliente **de escritura**, no solo de aplicación (la regla: **solo el integrador redacta y aplica
  migraciones**; las unidades aportan modelos). Ver `docs/ADR-migraciones-zona-caliente.md`.
- design system / componentes comunes compartidos,
- config global, stores globales de auth, event bus, base model/ORM base,
- ficheros de "registro de plugins/catálogos" que todos los módulos tocan.

## Paso 3 — Componer las unidades
- Una **unidad** por dominio/capa con globs `posee` **disjuntos**. Verifica la disjunción: si dos
  unidades comparten un glob, repártelo o muévelo a zonas calientes.
- Si un fichero lo posee una unidad pero su *registro* es global (p.ej. un resolver que se agrega
  a un schema raíz), ponlo en `resolvers` de esa unidad: lo edita ella, el cableado lo pide.
- Roles transversales: incluye siempre `integrador`; añade `buzon` salvo que el usuario no lo quiera.
- `runtime`: por defecto `modo: "ambos"`, `loop: "off"`, `triaje_desde_subagentes: false`, y
  `wip: { global: 4, por_unidad: 1 }` (Kanban continuo: ~4 agentes en paralelo, una tarea en curso
  por unidad). Solo cambia esto si el usuario lo pide.

## Paso 4 — Proponer y VALIDAR (no desplegar)
1. Escribe el borrador en `.claude/kit/particion.json` conforme al schema.
2. Muéstrale al usuario un **resumen legible**: tabla de unidades (nombre · qué cubre · cuántos
   globs · repo), lista de zonas calientes, roles, y flags de runtime. Señala explícitamente:
   - unidades cross-repo (se gestionarán "externas" en v1),
   - cualquier glob dudoso o solapamiento que tuviste que resolver,
   - qué quedó fuera de toda unidad y por qué (irá al integrador).
3. Pide validación: "¿ajusto algo antes de desplegar?". El usuario puede editar el JSON a mano.
4. Cuando dé el OK, dile que ejecute `/deploy-team`.

No crees worktrees, ramas ni ficheros de identidad aquí. Solo el contrato + la propuesta.

---

# Modo greenfield (repo vacío) — Pasos G1-G5

Solo si el Paso 0 te mandó aquí. El repo no tiene estructura: en vez de escanear, **preguntas**,
**generas un scaffold mínimo** y particionas sobre él. Frontera (ADR-greenfield-scaffold-minimo):
generas el **esqueleto canónico del stack + placeholders + zonas calientes vacías + config base**,
NUNCA lógica de negocio/modelos/pantallas reales. Esqueleto sí, músculo no.

## Paso G1 — Cuestionario (una pregunta cada vez, espera respuesta)
Extrae lo que decide el scaffold Y la partición. No avances hasta tener lo esencial:
1. **Tipo de app**: API sola · SPA + API · web fullstack · CLI · otro.
2. **Stack backend**: lenguaje + framework. **Soportado de catálogo (canónico): FastAPI +
   SQLAlchemy + Alembic.** Si pide otro, avisa: "fuera de catálogo improviso el layout con criterio,
   menos garantía de canónico; ¿seguimos o usamos el soportado?".
3. **Stack frontend** (si aplica): framework + librería CSS / design system. **Catálogo: Vue +
   Tailwind.**
4. **Persistencia/ORM**: ¿BD? ¿ORM con migraciones? (define la zona caliente de migraciones).
5. **Colas/workers**: ¿Celery u otra? (define un área/unidad de tareas y un worker del integrador).
6. **Repos**: monorepo (back+front juntos) o frontend en repo aparte (→ unidad cross-repo `repo`).
7. **Dominios del producto**: las áreas funcionales (p.ej. en un CRM: contactos, oportunidades,
   actividades…). Son la base de las unidades verticales. Si el usuario aún los está pensando, ayуda
   a enumerarlos; sin dominios no hay partición por dominio (caerás a partición por capa).

## Paso G2 — Deriva estructura-objetivo + partición (NO escribas aún)
Del cuestionario sale, de forma casi determinista por el stack:
- **Layout de carpetas canónico** del combo elegido. Para el catálogo FastAPI+SQLAlchemy+Vue+Tailwind:
  ```
  app/            # main.py (entrypoint), config.py, db.py        → ZONA CALIENTE
  models/         # un módulo por dominio                          → unidad(es) de datos
  api/  o gql/    # resolvers/endpoints por dominio; schema.py raíz → schema.py ZONA CALIENTE
  services/ tasks/# lógica de aplicación, workers (si Celery)      → unidad(es) backend
  alembic/versions# migraciones                                    → ZONA CALIENTE (de escritura)
  frontend/src/   # SPA Vue (views, components, router)            → unidad frontend
  pyproject.toml  # deps backend                                   → ZONA CALIENTE
  ```
- **Unidades**: aplica el mismo *Principio rector* de arriba (minimizar solapamiento). Con dominios
  claros → unidades verticales por dominio. Sin ellos → por capa. El frontend suele ser una unidad
  propia. Workers (Celery) → área de tareas, normalmente del backend dueño del dominio.
- **Zonas calientes**: las marcadas arriba (entrypoint, config, schema raíz, migraciones, deps,
  design system si lo hay). Mismo criterio que el Paso 2 del modo existente.

## Paso G3 — Propón y VALIDA (igual que el Paso 4, pero ANTES de crear nada)
Muéstrale: el **stack** elegido, el **árbol de carpetas** que vas a crear, las **unidades**
propuestas (con sus globs sobre esa estructura futura), las **zonas calientes** y los **workers**.
Señala lo dudoso. Pide OK explícito: **"¿genero este scaffold?"**. No crees ficheros sin ese OK.

## Paso G4 — Genera el scaffold mínimo (solo con OK)
- Crea las **carpetas** del layout y, en cada una, un **placeholder** mínimo (p.ej. `__init__.py`
  vacío en paquetes Python; un `App.vue`/`index` mínimo en front; NO lógica real).
- Crea las **zonas calientes vacías pero válidas**: `app/main.py` que arranca y no monta nada,
  `gql/schema.py` (o router) que no agrega resolvers aún, `alembic/` inicializado con `versions/`
  vacío, `pyproject.toml` con las deps base del stack.
- **No** escribas modelos de dominio, endpoints, ni pantallas: eso es trabajo de las unidades.
- Primer commit: `git add -A && git commit -m "scaffold inicial: <stack>"` en la rama base. Ahora el
  repo YA tiene estructura (deja de ser greenfield para los siguientes comandos).

## Paso G5 — Escribe el contrato y cierra
- Escribe `.claude/kit/particion.json` (mismo schema, mismas reglas del Paso 3/4: unidades disjuntas,
  `integrador` siempre, `buzon` salvo que no se quiera, `runtime` con `wip {global:4, por_unidad:1}`).
- Confírmale el resumen y dile que el siguiente paso es `/deploy-team`.

No crees worktrees, ramas de unidad ni identidades aquí (eso es `/deploy-team`). El único commit que
haces en greenfield es el del scaffold inicial.

$ARGUMENTS
