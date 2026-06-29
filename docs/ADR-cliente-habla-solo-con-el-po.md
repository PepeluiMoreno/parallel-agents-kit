# ADR · El cliente vive en un solo chat: habla solo con el Product Owner

> Estado: **aceptada** · Fecha: 2026-06-29 · Ámbito: punto de entrada del usuario al equipo virtual
> Relacionada con `ADR-topologia-estrella-no-teams.md` (es la cara de cara-al-cliente de la estrella).

## Contexto

El kit tiene varios roles (arquitecto, Product Owner, integrador, unidades, buzón) y varios comandos.
Un usuario que quiere *usar* el equipo —no operarlo— no debería tener que saber cuál es cuál ni
cambiarse de sombrero. En particular, **no quiere ser el integrador**: no quiere lanzar subagentes,
mergear ramas ni vigilar worktrees. Quiere comportarse como el **cliente / dueño de negocio**: decir
en lenguaje natural qué debe hacer la aplicación y sus reglas, y que alguien del equipo se encargue.

Además, la observabilidad nativa de Claude Code refuerza esto: los subagentes son cajas opacas (solo
devuelven un resumen), y el panel multi-agente en vivo solo existe en agent teams —que este kit no
usa (ver el ADR de topología) y que además no funciona en la terminal integrada de VS Code, el
entorno del usuario—. Es decir, "vigilar la orquestación" no es una experiencia que el entorno
ofrezca bien; tiene más sentido que el cliente **no orqueste**.

## Decisión

**El punto de entrada del cliente es un único chat con el Product Owner (`/product-owner`). El cliente
no orquesta ni integra; valida y delega.** El PO es su interlocutor: recoge la petición en lenguaje
natural, le propone *cómo* implementarla y *a qué afecta*, y —con su visto bueno— se lleva el encargo
al integrador.

El diálogo cliente↔PO tiene **dos puntos de control explícitos** (dos "OK"), porque el cliente sigue
siendo un nodo de validación de la estrella, no un espectador pasivo:

1. **OK nº1 — el plan.** Antes de descomponer nada, el PO presenta un **análisis de impacto** legible:
   qué módulos/unidades toca, qué dependencias y orden implica, qué zonas calientes roza (las cablea
   el integrador), y riesgos/alternativas. El cliente aprueba *cómo* se va a hacer. Queda en la ficha
   ("Plan de implementación").
2. **OK nº2 — el arranque.** Tras encolar las tareas, el PO resume el encargo y pide luz verde para el
   integrador. **No es automático**: hasta el OK, el encargo queda preparado pero quieto. Con el OK, el
   PO deja un bloque `[ENCARGO]` en `integrador.md` y termina su parte.

A partir de ahí el trabajo fluye por artefactos, sin que el cliente cambie de rol: el integrador
recoge el `[ENCARGO]` (`/pull-tasks`), ejecuta e integra (`/apply-integration`), y lo marca
`[ENTREGADO]`. El PO mueve la ficha y, con el cliente, pasa a `/accept`.

## Por qué dos OK y no cero (desatendido) ni uno

- **Cero (todo fluye solo tras pedirlo)** maximiza la comodidad pero choca con las cautelas ya
  documentadas (`COMPARATIVA_AGENT_TEAMS.md` §4.bis): sin validación, los errores se propagan y el
  coste se dispara. El cliente perdería el control justo donde más barato es corregir (en el plan).
- **Uno (solo aprobar el plan, y que arranque solo)** es razonable, pero juntar "apruebo el diseño" y
  "lanza ya el gasto/los merges" en un mismo gesto borra la frontera entre *pensar* y *ejecutar*.
  Separarlos da al cliente una última parada barata antes de consumir tokens y mover ramas.
- **Dos** mantiene al cliente como punto de control en los dos momentos que importan —el diseño y el
  arranque— sin obligarle a operar nada entre medias. Es el mínimo de fricción compatible con no
  perder el control.

## Alternativas consideradas

- **Crear un rol nuevo "analista de negocio" por encima del PO.** Rechazada: el PO ya es, por
  definición, el puente entre la visión de producto y el equipo. Añadir un rol duplicaría
  responsabilidades y piezas a mantener. Se potencia el PO en su lugar.
- **Que el cliente sea el integrador (modo 1-ventana puro).** Es el modo que el kit ya soporta, pero
  obliga al usuario a orquestar. Sigue disponible para quien *quiera* operar; no es el camino para el
  cliente que solo quiere dirigir el producto.
- **Handoff totalmente desatendido (modo `pleno`).** Disponible como runtime, pero no es el flujo por
  defecto del cliente por las cautelas de arriba. El segundo OK es la red de seguridad.

## Consecuencias

**A favor:**
- El cliente tiene una experiencia simple y honesta: un chat, lenguaje natural, dos decisiones claras.
- Encaja con la opacidad de los subagentes y con VS Code: no se le pide observar una orquestación que
  el entorno no muestra bien.
- Refuerza la estrella: el cliente valida en el centro (vía PO), no negocia con las unidades.

**En contra / límites:**
- El PO carga ahora con el análisis de impacto, que exige que el mapa de ownership (`particion.json`)
  esté al día; si está desfasado, el impacto que presente será impreciso. Mitiga: `/sync-board`.
- Dos OK añaden fricción frente al desatendido. Aceptada: es deliberada, es la red de seguridad.

## Cómo revertir

Es una decisión de *flujo*, materializada en prompts, no en motor. Para volver a "el cliente opera":
quitar el handoff con segundo OK de `commands/product-owner.md` y el reconocimiento de `[ENCARGO]`
en `commands/pull-tasks.md` / `commands/apply-integration.md`. El resto (fichas, criterios, backlog)
no depende de esta decisión.
