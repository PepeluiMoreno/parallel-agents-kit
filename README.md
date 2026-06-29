# parallel-agents-kit

Un kit portable para montar, en **cualquier** repositorio, un entorno donde **varios agentes de
Claude Code trabajan en paralelo sin pisarse**, coordinados por un integrador y alimentados por un
buzón. Un agente **arquitecto** analiza el proyecto e infiere qué posee cada agente y qué zonas son
compartidas; tú lo validas y se despliega solo.

## Qué es

El kit es un conjunto de **comandos, plantillas, hooks y un esquema** que se instalan en el `.claude/`
de tu repositorio y configuran a Claude Code para que actúe como un equipo de desarrollo. No es un
servicio ni un proceso de fondo: el equipo "corre" dentro de tu sesión de Claude Code (terminal o
extensión de VS Code), y todo su estado vive en **artefactos del repo** —el contrato, las bandejas,
las fichas de producto y las ramas de git—.

## La idea en una frase

Un **arquitecto** analiza tus carpetas/módulos → propone una **partición** del trabajo (un agente por
unidad, con ficheros disjuntos) → tú la validas → se **despliega** el andamiaje (worktrees, protocolo,
bandejas) → trabajas en **una sola ventana** lanzando subagentes que el **integrador** integra.

## Conceptos

- **Unidad**: el trozo de proyecto que posee un agente (un dominio o una capa). Su ownership son
  **globs de ficheros disjuntos** respecto a las demás unidades.
- **Zona caliente**: fichero que tocan muchas unidades (router/schema raíz, migraciones, design
  system, config global…). Dueño único: el **integrador**. Nadie más lo edita; se solicita con
  `/request-integration`.
- **Integrador**: el centro de la coordinación. Único que edita zonas calientes, mergea las ramas de
  unidad y redacta/aplica las migraciones. Toda la coordinación pasa por él y por los artefactos
  compartidos (contrato y bandejas); las unidades no se comunican entre sí.
- **git worktree**: varios directorios de trabajo del mismo repo compartiendo un único `.git`, cada
  uno en su propia rama. Cada agente trabaja en el suyo (`<proyecto>-wt/<unidad>`, rama
  `feature/<unidad>`) sin tocar el de los demás. Es el aislamiento que hace seguro el paralelismo —y
  por lo que el kit **exige git**—. Las ramas `feature/*` y los worktrees son locales y temporales:
  solo la rama base, ya integrada, se sube al remoto.
- **Agente vs subagente**: un *agente* es un chat de Claude Code; un *subagente* es uno que otro
  agente lanza por debajo. El modo 1-ventana usa subagentes: un solo chat (el integrador) lanza uno
  por unidad y luego integra, sin abrir N ventanas.

## El contrato `particion.json`

Datos puros (schema en `schema/particion.schema.json`), editable a mano. Modela:

- **unidades** (`nombre`, globs `posee`, `repo`),
- **zonas calientes**,
- **roles transversales** (`integrador`, `buzon`, opcional `product_owner`),
- **runtime**: `modo`, `loop`, `triaje_desde_subagentes`, y `wip` (`global` y `por_unidad`).

El motor solo lee este mapa; no ejecuta lógica del proyecto. Las unidades en otro repo
(`repo != "self"`) se gestionan como **externas** (rama + PR normal, fuera del fan-out de worktrees).

## Instalación

```bash
./install.sh /ruta/a/tu/repo      # copia comandos + kit a .claude/ del repo
```

Luego, en un chat de Claude Code abierto en ese repo:

```
/design-board      # el arquitecto propone la partición (revisa/edita .claude/kit/particion.json)
/deploy-team       # materializa worktrees, protocolo y bandejas
/pull-tasks        # trabaja en modo 1-ventana (o /inbox por unidad en modo N-ventanas)
```

Si el repositorio está **vacío**, `/design-board` entra en **modo greenfield**: te hace un
cuestionario (tipo de app, stack, ORM, dominios) y genera un scaffold mínimo del stack sobre el que
particionar.

## Comandos

| Comando | Rol | Qué hace |
|---|---|---|
| `/design-board` | arquitecto | Infiere la partición y la propone para validar. Repo vacío → modo greenfield (cuestionario + scaffold mínimo del stack) |
| `/sync-board` | arquitecto | Compara la partición vigente con el repo actual y propone un parche para resincronizarla |
| `/deploy-team` | desplegador | Materializa worktrees, protocolo y bandejas desde el contrato |
| `/generate-config` | arquitecto | Traduce la partición a configuración nativa de Claude Code (subagents `isolation: worktree` + hooks) |
| `/pull-tasks` | integrador | Modo 1-ventana: lanza un subagente por unidad y luego integra |
| `/pull-loop` | integrador | Modo desatendido (freno): drena bandejas en bucle, para antes de mergear/migrar. Úsalo con `/loop /pull-loop` |
| `/inbox` | unidad | Lee su bandeja y trabaja sus tareas (modo N-ventanas) |
| `/request-integration` | unidad | Encola una petición de zona caliente al integrador |
| `/apply-integration` | integrador | Mergea ramas, aplica cableados, reconcilia y aplica migraciones |
| `/add-request` | buzón | Clasifica una nota del usuario y la encola en la bandeja correcta |
| `/product-owner` | product owner | Propone funcionalidad, la diseña contigo (con análisis de impacto) y, con tu doble OK, la encola y se la lleva al integrador |
| `/accept` | product owner | Valida una funcionalidad terminada contra sus criterios de aceptación |

Los nombres van en inglés con léxico Kanban; la documentación, en español.

## Metodología: Kanban continuo

El equipo opera **por flujo, no por sprints**. El trabajo entra en una cola priorizada (las bandejas),
cada unidad **tira** (pull) de la suya, y un **límite de WIP** acota cuánto corre a la vez. El
"release" de una funcionalidad es cruzar sus criterios de aceptación (`/accept`), no el fin de una
iteración.

Dos límites de WIP (en `runtime.wip`):
- **global** — cuántos subagentes corren en paralelo por ronda (default 4),
- **por unidad** — tareas `[EN CURSO]` a la vez por unidad (default 1: terminar antes de empezar).

## Roles transversales

- **Integrador** — centro de la coordinación (ver *Conceptos*).
- **Buzón** (`/add-request`) — reactivo: clasifica notas sueltas del usuario (bugs, peticiones) y las
  encola en la bandeja correcta. No edita código.
- **Product Owner** (`/product-owner`, `/accept`) — proactivo: propone y diseña funcionalidad nueva
  en diálogo contigo, con análisis de impacto por módulo, y la encola con tu doble visto bueno (al
  plan y al arranque). Vive en `.claude/producto/` (backlog + ficha de dominio). No escribe código:
  reutiliza el equipo.

Como cliente puedes trabajar **solo a través del Product Owner**: describes en lenguaje natural qué
debe hacer la aplicación, validas el plan que te propone, das luz verde, y el equipo lo construye.

## Observabilidad

Los subagentes devuelven un resumen al terminar. Para seguir el avance en vivo, el kit mantiene un
**tablero de progreso** en `.claude/inbox/_progreso.md`: cada subagente anota un checkpoint al
empezar una tarea, al cambiar de foco y al cerrarla. Abre ese fichero en una pestaña del editor y se
actualiza solo según los agentes avanzan.

## Modos de autonomía (`runtime.loop`)

- **off** — `/pull-tasks` es un disparo único; tú decides cuándo.
- **freno** — `/loop /pull-loop` drena las bandejas en bucle, pero **para y pide OK antes de
  mergear/cablear/migrar**. Se autodetiene cuando no queda nada que drenar.
- **pleno** — integra sin preguntar hasta vaciar. Desaconsejado con BD compartida.

## Decisiones de diseño

Las decisiones de arquitectura están registradas como ADR en `docs/`:

- `ADR-topologia-estrella-no-teams.md` — coordinación radial vía integrador.
- `ADR-migraciones-zona-caliente.md` — las migraciones las redacta solo el integrador.
- `ADR-cliente-habla-solo-con-el-po.md` — el cliente opera a través del Product Owner.
- `ADR-greenfield-scaffold-minimo.md` — generación de scaffold mínimo en proyectos desde cero.
