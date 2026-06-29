# parallel-agents-kit

Un kit portable para montar, en **cualquier** repositorio, un entorno donde **varios agentes de
Claude Code trabajan en paralelo sin pisarse**, coordinados por un integrador y alimentados por un
buzón. Lo que en un proyecto se teclea a mano (qué posee cada agente, qué es zona caliente), aquí
lo **infiere un agente arquitecto** analizando la estructura del proyecto, y lo despliega solo.

**Topología: en estrella, no en malla.** Los agentes no se hablan entre sí (como haría el *mailbox*
de agent teams): toda la coordinación es **radial** y pasa por un centro —el **integrador**, más el
contrato (`particion.json`) y el backlog—. El estado del equipo vive en esos artefactos compartidos,
no en conversaciones entre pares, así que la malla no hace falta. Por eso el kit usa subagents
aislados por worktree + hooks y **no** adopta agent teams. El porqué, en
[`docs/ADR-topologia-estrella-no-teams.md`](docs/ADR-topologia-estrella-no-teams.md).

**Metodología: Kanban continuo.** El equipo virtual opera por flujo, no por sprints. El trabajo
entra en una cola priorizada (las bandejas), cada unidad **tira** de la suya, y un **límite de WIP**
acota cuánto corre a la vez —que en un equipo de agentes es control directo de coste y de cuellos de
botella—. El "release" de una funcionalidad es cruzar sus criterios de aceptación, no el fin de una
iteración.

## La idea en una frase
Un **arquitecto** analiza tus carpetas/módulos → propone una **partición** del trabajo (un agente
por unidad, con ficheros disjuntos) → tú la validas → se **despliega** el scaffolding (worktrees,
protocolo, bandejas, comandos) → trabajas en **una sola ventana** lanzando subagentes.

## Conceptos
- **git worktree**: copias de trabajo del mismo repo en carpetas distintas, compartiendo un solo
  `.git`. Cada agente trabaja en su worktree (rama propia) sin tocar el de los demás. Es lo que
  hace barato y seguro el paralelismo. **Por eso el kit exige git.**
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

## Instalación
```bash
./install.sh /ruta/a/tu/repo      # copia comandos + kit a .claude/ del repo
```
Luego, en un chat de Claude Code abierto en ese repo:
```
/design-board     # arquitecto: escanea y PROPONE la partición (no despliega)
                       # revisas/editas .claude/kit/particion.json
/deploy-team    # materializa worktrees, protocolo, bandejas
/pull-tasks             # trabaja en modo 1-ventana (o /inbox por unidad en modo N-ventanas)
```

## El contrato `particion.json`
Datos puros (schema en `schema/particion.schema.json`), editable a mano. Modela: unidades
(nombre + globs `posee` + `repo`), zonas calientes, roles transversales y flags de runtime
(`modo`, `loop`, `triaje_desde_subagentes`). El motor solo lee este mapa; no ejecuta lógica del
proyecto. Las unidades en otro repo (`repo != "self"`) se marcan **externas** en v1 (rama+PR
normal, fuera del fan-out de worktrees).

## Comandos
| Comando | Rol | Qué hace |
|---|---|---|
| `/design-board` | arquitecto | Escanea la estructura, infiere la partición, la propone para validar |
| `/sync-board` | arquitecto | Compara la partición vigente con el repo actual y propone un parche para resincronizarla |
| `/deploy-team` | desplegador | Materializa worktrees, protocolo, bandejas desde el contrato |
| `/generate-config` | arquitecto | Traduce la partición a config nativa de Claude Code (subagents `isolation: worktree` + hooks) en vez del motor propio |
| `/pull-tasks` | integrador | Modo 1-ventana: lanza un subagente por unidad y luego integra |
| `/pull-loop` | integrador | Modo desatendido **freno**: drena bandejas en bucle, PARA antes de mergear/migrar. Úsalo con `/loop /pull-loop` |
| `/inbox` | unidad | Lee su bandeja y trabaja sus tareas (modo N-ventanas) |
| `/request-integration` | unidad | Encola una petición de zona caliente al integrador |
| `/apply-integration` | integrador | Mergea ramas, aplica cableados, reconcilia y aplica migraciones |
| `/add-request` | buzón | Clasifica una nota del usuario y la encola en la bandeja correcta |
| `/product-owner` | product owner | Propone funcionalidad, la diseña en diálogo contigo y, con tu OK, la descompone en tareas y las encola |
| `/accept` | product owner | Valida una funcionalidad terminada contra sus criterios de aceptación y te resume para el visto bueno |

## Capa de producto: el Product Owner
Además de construir, el kit puede **decidir qué construir**. El rol **product owner** (`/product-owner`)
es un agente proactivo que:
1. propone funcionalidad con criterio (a partir de una *ficha de dominio* que apruebas),
2. la diseña **en diálogo contigo** —alcance, flujos, UI, reglas, criterios de aceptación—,
   pidiendo tu OK en cada paso,
3. con tu visto bueno, la **descompone en tareas por unidad** y las **encola** en las bandejas
   (con especificación rica + trazabilidad),
4. y al terminar, valida lo entregado contra los criterios (`/accept`).

Vive en `.claude/producto/` (backlog de fichas + ficha de dominio), paralelo a `.claude/inbox/`.
Es a la funcionalidad lo que el buzón es al desarrollo: el **buzón** es reactivo (bugs/quejas), el
**PO** es proactivo (producto nuevo). No escribe código; reutiliza el equipo de desarrollo existente.

## Modos de autonomía (`runtime.loop`)
- **off**: `/pull-tasks` es un disparo único; tú decides cuándo.
- **freno** (recomendado para desatendido): `/loop /pull-loop` drena las bandejas en bucle con
  subagentes, pero **para y pide OK antes de mergear/cablear/migrar** (lo irreversible). Se
  autodetiene cuando no queda nada que drenar.
- **pleno**: integraría sin preguntar hasta vaciar. Desaconsejado con BD compartida.

## Estado
v1: un repo principal con worktrees; cross-repo modelado pero gestionado como "externo". Loop
(off/freno/pleno) y triaje-desde-subagentes disponibles como flags de `runtime` en el contrato.

**Pivote a nativo (en curso):** Claude Code ya trae de serie el núcleo de orquestación (subagents
con `isolation: worktree`, hooks como gate, agent teams). El kit conserva sólo su diferencial real
—el arquitecto que infiere la partición y la capa de producto— y, con `/generate-config`, genera la
maquinaria de orquestación como config nativa desde el mismo `particion.json`. Detalle y razones en
`docs/COMPARATIVA_AGENT_TEAMS.md` y `docs/ARQUITECTURA_pivote_nativo.md`.
