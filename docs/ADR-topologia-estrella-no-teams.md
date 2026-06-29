# ADR · Topología en estrella (vía integrador), no en malla (agent teams)

> Estado: **aceptada** · Fecha: 2026-06-29 · Ámbito: runtime de ejecución multi-agente
> Actualiza la postura de `COMPARATIVA_AGENT_TEAMS.md` (2026-06-27) y
> `ARQUITECTURA_pivote_nativo.md` (2026-06-28), que dejaban agent teams como destino "cuando madure"
> y trataban el mailbox/malla como una capacidad que al kit le faltaba.

## Contexto

El kit coordina varias unidades que trabajan en paralelo. Hay dos topologías posibles para esa
coordinación:

- **Malla (mesh):** los agentes se comunican **entre iguales** —es el modelo de agent teams nativo,
  con su *mailbox* y su *task list* compartida: un teammate le habla directamente a otro para
  negociar dependencias.
- **Estrella (radial):** toda la coordinación pasa por un **centro**. En este kit ese centro es el
  **integrador** (dueño único de las zonas calientes, único que mergea y migra), apoyado por dos
  artefactos también centrales: el **contrato** (`particion.json`, que define qué posee cada unidad
  y la frontera entre ellas) y el **backlog** (la cola priorizada de la que cada unidad tira).

Los documentos previos de arquitectura partían de una lectura razonable en su momento: «el mailbox
de teams es comunicación directa entre teammates, algo que nuestros subagentes NO hacen», y de ahí
inferían que el kit *echaba en falta* la malla y que adoptar teams era el destino natural una vez
dejara de ser experimental.

Al revisarlo a la luz del papel real del integrador, esa inferencia se invierte.

## Decisión

**La topología del kit es en estrella, con el integrador (y el contrato/backlog) como centro. No se
adopta agent teams, y no por inmadurez de la API, sino por diseño.**

La malla **no es una capacidad que al kit le falte**: es una capacidad que el modelo en estrella **no
necesita**, porque el estado del equipo está *externalizado* en artefactos —el contrato, el backlog,
las bandejas, la rama de cada unidad— en vez de vivir en la "cabeza" de cada agente. Cuando el estado
es compartido y explícito, no hace falta que dos agentes negocien hablándose: cada uno trabaja contra
el artefacto.

El único punto donde *parecería* hacer falta que dos unidades se hablen —una dependencia entre tareas
("económico necesita que membresía exponga X primero")— ya se resuelve mejor sin malla: **el
arquitecto descompone definiendo el contrato entre ambas**, y cada unidad trabaja contra ese contrato
sin verse. La dependencia se gestiona en el backlog (orden, bloqueos) y, si toca una frontera común,
en el integrador. Es coordinación radial, no negociación entre pares.

Consecuencia operativa, en tres tiempos (sin cambios respecto a lo ya implementado, ahora con su
*porqué* registrado):

1. **Ahora y por diseño:** subagents con `isolation: worktree` + hooks. La estrella la cierra el
   integrador. Cero agent teams.
2. **Si agent teams deja de ser experimental:** se reevalúa, pero entra **solo** donde su diferencial
   real —el mailbox malla entre teammates— aporte algo que la estrella por integrador no dé. Para
   este kit eso es poco; tendría que aparecer un flujo donde dos unidades necesiten negociar entre sí
   **sin** pasar por el integrador ni por el contrato. Hasta que ese caso exista, la estrella basta.
3. **Independiente de esta decisión:** `particion.json` como fuente de verdad, el arquitecto que
   infiere/reinfiere, y la capa de producto. Las tres son ortogonales al runtime de ejecución. Agent
   teams, si algún día entra, sería un **tercer backend de ejecución** bajo el mismo contrato —como
   hoy conviven los modos `off`/`freno`/`pleno`—, no un rediseño.

## Por qué la estrella es preferible aquí (no solo suficiente)

- **Aísla el ownership.** El diferencial más fuerte del kit es que dos unidades no se pisen, y eso lo
  garantiza el worktree disjunto + el hook de ownership. Agent teams **no aísla a los teammates en
  worktrees** (hay que particionar a mano); pivotar a malla cambiaría la mejor garantía del kit por
  un mailbox que el modelo apenas usa.
- **Evita la propagación de errores en dominó.** En malla, si un teammate dice "listo", el lead se lo
  cree y el error se propaga sin validación entre pasos (riesgo documentado en
  `COMPARATIVA_AGENT_TEAMS.md` §4.bis). La estrella mete un punto de validación central: el
  integrador al mergear y `/accept` contra criterios. La coordinación radial es una **red de
  seguridad**, no solo una topología.
- **Es más fiel al flujo Kanban del kit.** El corazón de Kanban (y de la metodología que el kit ya
  declara) es una **cola central** de la que se tira, no una conversación entre quienes ejecutan. La
  estrella encaja con eso de forma natural; la malla introduciría un canal lateral que el método no
  pide.
- **Coste y control.** Menos actores hablándose = menos tokens gastados en coordinación y un único
  dial de paralelismo (el WIP global) en el centro, en vez de tráfico difuso entre pares.

## Alternativas consideradas

- **Adoptar agent teams cuando salga de experimental (postura previa).** Rechazada como *destino por
  defecto*: regalaría el aislamiento por worktree —el mayor diferencial— a cambio de un mailbox que
  esta arquitectura casi no ejercita, porque su coordinación es radial, no en malla. Queda como
  opción futura **bajo vigilancia**, solo para un flujo concreto que hoy no existe (dos unidades que
  deban negociar sin pasar por el integrador).
- **Híbrido estrella + mailbox puntual.** Permitir malla solo para ciertas dependencias. Rechazada
  por ahora: toda dependencia que hoy se plantea se expresa como contrato (definido por el
  arquitecto) o como bloqueo en el backlog; añadir un canal entre pares duplicaría un mecanismo que
  ya es radial y reintroduciría el riesgo de coordinación sin validación.

## Consecuencias

**A favor:**
- La decisión "no teams" deja de leerse como timidez ante una API experimental y pasa a ser una
  elección de diseño con motivo técnico (ownership aislado + validación central + fidelidad a Kanban).
- El runtime queda conceptualmente simple: un centro, radios, y artefactos compartidos como memoria
  de equipo.

**En contra / límites:**
- El integrador es un cuello de botella consciente para todo lo irreversible (merge, cableado,
  migración). Aceptado: es el mismo punto donde ya se concentra la disciplina de zonas calientes y
  migraciones (ver `ADR-migraciones-zona-caliente.md`).
- Si en el futuro apareciera un flujo genuinamente entre-pares, habría que reabrir esta decisión. El
  ADR queda como el lugar donde hacerlo.

## Cómo revertir

Esta decisión es de *postura/arquitectura*, no de código: no hay un commit que deshacer para
"volver a la malla". Reabrirla significa documentar el flujo entre-pares que la justifique y, si se
materializa, añadir agent teams como tercer backend de ejecución bajo el mismo `particion.json`
(modos `off`/`freno`/`pleno` → más un modo `teams`). Los puntos a tocar serían `/generate-config` (que
ya contempla el camino nativo) y las cautelas de `COMPARATIVA_AGENT_TEAMS.md` §3.
