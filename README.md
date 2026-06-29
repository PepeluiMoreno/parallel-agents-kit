# parallel-agents-kit

Un kit portable para montar, en **cualquier** repositorio, un entorno donde **varios agentes de
Claude Code trabajan en paralelo sin pisarse**, coordinados por un integrador y alimentados por un
buzón. Lo que en un proyecto se teclea a mano (qué posee cada agente, qué es zona caliente), aquí
lo **infiere un agente arquitecto** analizando la estructura del proyecto, y lo despliega solo.

---

## ¿Qué es esto, en realidad? (léelo antes que nada)

El kit **no es un programa que se ejecuta.** No hay servidor, ni web, ni proceso de fondo. Son
**recetas**: ficheros de texto (comandos, plantillas, hooks, un esquema) que **configuran a Claude
Code** para que actúe como un equipo de varios agentes. Una analogía: el kit es una *receta y un
reparto de roles escritos en papel*; el papel no cocina — **Claude Code es el cocinero** que lee la
receta y la ejecuta.

De ahí salen tres consecuencias que conviene tener claras:

- **¿Dónde corre?** Donde corra Claude Code. Si trabajas en la extensión de VS Code, el equipo vive
  dentro de tu chat de Claude Code en VS Code. Lo mismo desde el `claude` de terminal. No hay nada
  desplegado en ningún servidor.
- **No hay daemon.** Si cierras el editor, no queda nada corriendo. **El estado del equipo vive en
  artefactos del repo** —las bandejas, las fichas de producto, las ramas de git—, no en memoria.
- **No va ninguna réplica a GitHub.** (Ver más abajo: *El `-wt` es un andamio, no una copia*.)

---

## La idea en una frase

Un **arquitecto** analiza tus carpetas/módulos → propone una **partición** del trabajo (un agente
por unidad, con ficheros disjuntos) → tú la validas → se **despliega** el scaffolding (worktrees,
protocolo, bandejas, comandos) → trabajas en **una sola ventana** lanzando subagentes.

---

## Topología: en estrella, no en malla

Los agentes **no se hablan entre sí** (como haría el *mailbox* de agent teams). Toda la coordinación
es **radial** y pasa por un centro —el **integrador**, más el contrato (`particion.json`) y el
backlog—.

¿Por qué basta la estrella y no hace falta la malla? Porque **el estado del equipo está
externalizado en artefactos** (el contrato, las bandejas, la rama de cada unidad) en vez de vivir
"en la cabeza" de cada agente. Cuando el estado es compartido y explícito, dos agentes no necesitan
negociar hablándose: cada uno trabaja contra el artefacto. Si una unidad necesita algo de otra, no
se lo pide a ella —lo expresa como **dependencia en el backlog**, o, si toca una zona caliente, con
`/request-integration` al integrador—.

Por eso el kit usa **subagents aislados por worktree + hooks** y **no** adopta agent teams: la malla
costaría el aislamiento por worktree (su mejor garantía) a cambio de un mailbox que esta
arquitectura apenas usaría. El razonamiento completo:
[`docs/ADR-topologia-estrella-no-teams.md`](docs/ADR-topologia-estrella-no-teams.md).

---

## El `-wt` es un andamio, no una copia (el malentendido nº1)

Al desplegar verás aparecer una carpeta hermana, `<proyecto>-wt/`. **NO es una réplica ni una copia
del proyecto.** Es un **git worktree**: git permite tener **varios directorios de trabajo
compartiendo un único `.git`** (un solo historial, una sola base de objetos), cada uno asomado a una
rama distinta a la vez.

- `miproyecto/` → directorio de trabajo en la rama base (`main`).
- `miproyecto-wt/frontend/` → **otro** directorio de trabajo, en `feature/frontend`, **usando el
  mismo `.git`**.

No se duplica el historial: se comparte. Por eso es barato — no es un `cp -r`, es "otra ventana al
mismo repo asomada a otra rama". Y es **el aislamiento físico que hace seguro el paralelismo**: cada
agente tiene su propia carpeta y su propia rama, así que literalmente no puede pisar el trabajo de
otro. Analogía: el `-wt` es el **andamio** de una obra —necesario mientras construyes, varias
cuadrillas en plantas distintas sin estorbarse—, pero no forma parte del edificio y se retira al
final.

**¿Qué va a GitHub?** Solo el resultado, nunca el andamio. Las ramas `feature/<unidad>` son
**locales y efímeras**: no se suben. El **integrador** mergea esas ramas a la base (`main`), y solo
la base ya integrada y limpia se hace `push`. GitHub jamás ve las carpetas `-wt` ni las ramas de
trabajo. (Lo fija el PROTOCOLO §5.bis del despliegue.)

---

## Conceptos

- **git worktree**: varios directorios de trabajo del mismo repo compartiendo un solo `.git`, cada
  uno en su rama. Cada agente trabaja en el suyo sin tocar el de los demás. Es lo que hace barato y
  seguro el paralelismo. **Por eso el kit exige git.** (Ver la sección del andamio, arriba.)
- **Unidad**: el trozo de proyecto que posee un agente (un dominio, una capa, lo que el arquitecto
  decida). Su ownership son **globs de ficheros disjuntos** respecto a las demás unidades.
- **Zona caliente**: fichero que tocan muchas unidades (router/schema raíz, migraciones, design
  system…). Dueño único: el **integrador**. Nadie más lo edita; se pide con `/request-integration`.
- **Agente vs subagente**: un *agente* es un chat de Claude Code. Un *subagente* es un agente que
  otro agente lanza por debajo (herramienta Agent). El modo 1-ventana usa subagentes: un solo chat
  (el integrador) lanza un subagente por unidad y luego integra → no abres N ventanas.
- **Loop** (opcional): repetir un comando en bucle. `/loop /pull-tasks` drena las bandejas sola.
  Es ortogonal a los subagentes: estos paralelizan en el espacio (N unidades a la vez), el loop
  repite en el tiempo. Se componen.

---

## Cómo decide el arquitecto el eje de partición

Es lo más importante que hace el arquitecto. Tiene **una regla maestra**: particiona por la
dimensión que **minimiza el solapamiento de ficheros** entre agentes y **maximiza la independencia
de las tareas**. ¿Por qué *ficheros*? Porque el aislamiento es el worktree, y un worktree aísla por
**carpetas/ficheros**: dos unidades solo corren en paralelo sin pisarse si sus globs `posee` son
**disjuntos**.

No hay un eje "correcto" universal; depende del repo. Los tres posibles:

- **Por dominio / feature (vertical):** una unidad = una funcionalidad completa (back + front).
  Gana cuando el repo ya está organizado por dominio (carpetas hermanas `pedidos/`, `usuarios/`…).
  Es el ideal: las tareas caen enteras dentro de una unidad → casi sin coordinación.
- **Por capa técnica (horizontal):** una unidad = una capa (`backend`, `frontend`, `datos`). Gana
  cuando el repo está organizado por función (`services/`, `etl/`, `tasks/`) y los dominios están
  entremezclados. El precio: más dependencias entre unidades.
- **Mixto:** lo habitual en proyectos reales — el frontend como unidad vertical (carpeta nítida) y
  el backend por capas.

Pistas que mira para decidir: modularidad natural (carpetas hermanas repetidas), emparejamiento
back↔front por nombre, sub-repos (`.git` anidados → unidad cross-repo), y el stack (¿hay
migraciones? ¿design system? ¿router raíz?). Al final aplica el **test de disjunción**: si dos
unidades comparten un glob, lo reparte o —si lo tocan todas— lo saca a **zona caliente**. Lo que no
se puede repartir limpiamente, no se reparte: lo custodia el integrador.

---

## Observabilidad: saber por dónde van (sin tmux)

Mientras un subagente trabaja, es una **caja cerrada** por diseño de Claude Code: no emite nada
hasta que termina y devuelve su resumen. No existe un "va por el 60%" en streaming. El panel
multi-agente en vivo solo lo da agent teams, que además necesita tmux (y tmux no funciona en la
terminal integrada de VS Code).

La solución del kit, fiel a la topología en estrella, es el **tablero de progreso**
(`.claude/inbox/_progreso.md`): cada subagente escribe **un checkpoint** al empezar una tarea, al
cambiar de foco y al cerrarla (su *intención*: "voy a tocar X para Y"). Abres ese fichero en una
pestaña del editor y lo ves **latir** —el editor recarga al cambiar—. Es el "tablero de estado"
equivalente al de agent teams, pero sobre subagentes aislados, sin tmux y sin perder el worktree.
**Late por hitos, no es streaming continuo:** ves *qué tarea* hace cada unidad y cuándo cambia —lo
justo para detectar un desvío y cortar la ronda—.

---

## Si eres el cliente, hablas solo con el Product Owner

No tienes que orquestar nada. En un único chat con `/product-owner` dices en lenguaje natural qué
debe hacer la app y sus reglas; el PO:

1. te propone **cómo** lo implementará y **a qué módulos afecta** (análisis de impacto) → **tu OK al
   plan**,
2. descompone en tareas y te resume el encargo → **tu luz verde al arranque (segundo OK)**,
3. con tu OK, deja el encargo al integrador y se encarga del resto.

Nunca te pones el sombrero de integrador: validas dos veces —el plan y el arranque— y el trabajo
fluye por artefactos. El porqué: [`docs/ADR-cliente-habla-solo-con-el-po.md`](docs/ADR-cliente-habla-solo-con-el-po.md).

---

## Instalación

```bash
./install.sh /ruta/a/tu/repo      # copia comandos + kit a .claude/ del repo
```
Luego, en un chat de Claude Code abierto en ese repo:
```
/design-board      # arquitecto: escanea y PROPONE la partición (no despliega)
                   #   revisas/editas .claude/kit/particion.json
/deploy-team       # materializa worktrees, protocolo, bandejas
/pull-tasks        # trabaja en modo 1-ventana (o /inbox por unidad en modo N-ventanas)
```

---

## El contrato `particion.json`

Datos puros (schema en `schema/particion.schema.json`), editable a mano. Modela: unidades
(nombre + globs `posee` + `repo`), zonas calientes, roles transversales y flags de runtime
(`modo`, `loop`, `triaje_desde_subagentes`, `wip`). El motor solo lee este mapa; no ejecuta lógica
del proyecto. Las unidades en otro repo (`repo != "self"`) se marcan **externas** en v1 (rama+PR
normal, fuera del fan-out de worktrees).

---

## Comandos

| Comando | Rol | Qué hace |
|---|---|---|
| `/design-board` | arquitecto | Infiere la partición y la propone para validar. **Repo vacío → modo greenfield**: cuestionario (stack, ORM, dominios…) + genera un scaffold mínimo del stack sobre el que particionar (ver `docs/ADR-greenfield-scaffold-minimo.md`) |
| `/sync-board` | arquitecto | Compara la partición vigente con el repo actual y propone un parche para resincronizarla |
| `/deploy-team` | desplegador | Materializa worktrees, protocolo, bandejas desde el contrato |
| `/generate-config` | arquitecto | Traduce la partición a config nativa de Claude Code (subagents `isolation: worktree` + hooks) en vez del motor propio |
| `/pull-tasks` | integrador | Modo 1-ventana: lanza un subagente por unidad y luego integra |
| `/pull-loop` | integrador | Modo desatendido **freno**: drena bandejas en bucle, PARA antes de mergear/migrar. Úsalo con `/loop /pull-loop` |
| `/inbox` | unidad | Lee su bandeja y trabaja sus tareas (modo N-ventanas) |
| `/request-integration` | unidad | Encola una petición de zona caliente al integrador |
| `/apply-integration` | integrador | Mergea ramas, aplica cableados, reconcilia y aplica migraciones |
| `/add-request` | buzón | Clasifica una nota del usuario y la encola en la bandeja correcta |
| `/product-owner` | product owner | Propone funcionalidad, la diseña contigo (con análisis de impacto), y con tu doble OK la encola y se la lleva al integrador |
| `/accept` | product owner | Valida una funcionalidad terminada contra sus criterios de aceptación y te resume para el visto bueno |

> Los nombres están en **inglés con léxico Kanban** (pull, board…), por coherencia con Claude Code;
> la documentación va en español y los cita por su nombre en inglés.

---

## Metodología: Kanban continuo

El equipo virtual opera **por flujo, no por sprints**. El trabajo entra en una cola priorizada (las
bandejas), cada unidad **tira** (pull) de la suya, y un **límite de WIP** acota cuánto corre a la
vez —que en un equipo de agentes es control directo de coste y de cuellos de botella—. El "release"
de una funcionalidad es cruzar sus criterios de aceptación (`/accept`), no el fin de una iteración.

Dos límites de WIP (en `runtime.wip`): **global** (cuántos subagentes en paralelo por ronda; default
4) y **por unidad** (tareas `[EN CURSO]` a la vez; default 1 = terminar antes de empezar).

---

## Capa de producto: el Product Owner

Además de construir, el kit puede **decidir qué construir**. El rol **product owner**
(`/product-owner`) es un agente proactivo que propone funcionalidad (a partir de una *ficha de
dominio* que apruebas), la diseña en diálogo contigo —alcance, flujos, UI, reglas, **análisis de
impacto**, criterios de aceptación—, y con tu doble OK la descompone en tareas y las encola. Al
terminar, valida lo entregado contra los criterios (`/accept`).

Vive en `.claude/producto/` (backlog de fichas + ficha de dominio), paralelo a `.claude/inbox/`.
Es a la funcionalidad lo que el buzón es al desarrollo: el **buzón** (`/add-request`) es reactivo
(bugs/quejas), el **PO** es proactivo (producto nuevo). No escribe código; reutiliza el equipo.

---

## Modos de autonomía (`runtime.loop`)

- **off**: `/pull-tasks` es un disparo único; tú decides cuándo.
- **freno** (recomendado para desatendido): `/loop /pull-loop` drena las bandejas en bucle con
  subagentes, pero **para y pide OK antes de mergear/cablear/migrar** (lo irreversible). Se
  autodetiene cuando no queda nada que drenar.
- **pleno**: integraría sin preguntar hasta vaciar. Desaconsejado con BD compartida.

---

## Estado

v1: un repo principal con worktrees; cross-repo modelado pero gestionado como "externo". Loop
(off/freno/pleno) y triaje-desde-subagentes disponibles como flags de `runtime` en el contrato.

**Pivote a nativo (en curso):** Claude Code ya trae de serie el núcleo de orquestación (subagents
con `isolation: worktree`, hooks como gate). El kit conserva sólo su diferencial real —el arquitecto
que infiere la partición y la capa de producto— y, con `/generate-config`, genera la maquinaria de
orquestación como config nativa desde el mismo `particion.json`. Detalle y razones en
`docs/COMPARATIVA_AGENT_TEAMS.md` y `docs/ARQUITECTURA_pivote_nativo.md`.
