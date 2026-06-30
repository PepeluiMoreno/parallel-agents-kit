# Rama `feat/dashboard-lector`

> Documento maestro. Base: `master` (88be37c). Implementa el dashboard web como **lector de estado**.
> Cierra parcialmente §3 (métricas de flujo) y prepara §1 (consumo) del backlog de complementos.

## Resumen en una frase

Una consola web de solo lectura que pinta el estado del equipo —tablero Kanban, unidades, WIP,
integrador, consumo por modelo, cuello de botella— leyendo los ficheros que ya existen, sin demonio.

## Decisión de arquitectura

El kit no es un proceso de larga duración (es markdown + hooks dentro de Claude Code), así que **no**
puede servir streaming de terminal como tutti. Pero su estado ya vive en ficheros, de modo que el
dashboard correcto es un **lector**: un generador determinista serializa el estado a `state.json` y un
HTML estático lo pinta con polling. Cero backend, cero LLM en el camino de datos.

División de responsabilidades con las herramientas de chat (app de escritorio / CloudCLI):
- **Ellas** dan el chat con los opus y la vigilancia *en vivo* de cada coder (diffs, ficheros).
- **Este dashboard** da la capa *agregada* con el vocabulario del kit (unidad económico, WIP, regla
  de migración), que ninguna herramienta genérica conoce.

## Qué entra

- `scripts/build_dashboard_state.py` — generador determinista. Lee `particion.json`
  (unidades, `runtime.wip`, modelo por unidad), bandejas `.claude/inbox/*.md`
  (`[ABIERTO]`/`[EN CURSO]`/`[HECHO]`), `integrador.md` (cola, migración pendiente) y `ccusage`
  (gasto por modelo, si está). Escribe `.claude/dashboard/state.json`.
- `dashboard/index.html` — consola de turno. Lee `state.json` por fetch + polling cada 10 s;
  tablero Kanban, carril de unidades con LED de estado, hub del integrador, consumo por modelo,
  flujo. Color = modelo (violeta opus, teal sonnet, gris haiku). Estados vacíos con dirección.
- `commands/dashboard.md` — refresca el estado y explica cómo servirlo (`python3 -m http.server
  --bind 127.0.0.1` + túnel SSH, mismo patrón que Portainer).
- `pull-tasks.md` paso 8 — regenera `state.json` al cerrar cada ronda.
- `install.sh` — copia `scripts/` y `dashboard/` al desplegar.

## Cómo se prueba

```bash
# en un proyecto con el kit desplegado (.claude/kit/particion.json + bandejas)
python3 .claude/kit/scripts/build_dashboard_state.py     # genera state.json
cd .claude/dashboard && python3 -m http.server 8787 --bind 127.0.0.1
# desde tu portátil:  ssh -L 8787:127.0.0.1:8787 user@ubuntu-dev  →  http://localhost:8787
```
Validado end-to-end con un proyecto simulado (4 unidades, 2/4 WIP, migración pendiente detectada,
cuello de botella calculado, consumo vacío degradando con elegancia).

## Límites honestos (documentados en el propio comando)

- **Consumo por modelo, no por unidad.** ccusage agrega por modelo/sesión; el desglose por unidad
  exige OTel etiquetado por subagente (§1 del backlog). Por eso el panel dice "por modelo".
- **Flujo y cuello de botella son heurísticos** (longitud de colas), señal y no métrica exacta.
- **No es tiempo real:** se refresca por ronda / cada 10 s de polling. Para vivo, las herramientas
  de chat.

## Cómo revertir

Rama puramente aditiva (un script, un HTML, un comando, dos líneas en pull-tasks/install). `git revert`
de cualquier commit no afecta al resto del kit.
