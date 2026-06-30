# Rama `feat/dashboard-lector`

> Documento maestro. Base: `master` (88be37c). Implementa el dashboard web como **lector de estado**.
> Cierra parcialmente §3 (métricas de flujo) y prepara §1 (consumo) del backlog de complementos.

## Resumen en una frase

Una consola web de solo lectura que pinta el estado del equipo —tablero Kanban, unidades, WIP,
integrador, **cuota** (no €) y cuello de botella— leyendo los ficheros que ya existen, con una
**página de ajustes** para los parámetros editables (WIP, loop, modelos, plan de Claude).

## Cuota en vez de coste (lo que importa con suscripción)

Con Pro/Max el dinero está pagado; lo que limita es la **cuota** (ventana de 5 h + tope semanal, con
buckets Opus/Sonnet independientes en Max). Por eso el panel "consumo €" se sustituye por uno de
cuota: plan y su multiplicador, ritmo por modelo (proxy de la ventana, de ccusage), recordatorio de
que los teammates en *plan mode* queman ~7×, y enlace a Settings > Usage para el saldo oficial.
Honesto: el saldo real vive en la cuenta y se **enlaza**; el dashboard calcula **ritmo**, no saldo.
El plan se lee de `~/.claude/kit-config.json` (ámbito usuario).

## Página de parámetros (ajustes)

`dashboard/params.manifest.json` declara qué es editable (WIP global/por unidad, loop, modo, triaje,
modelo por defecto, plan) con rango, default y **ámbito**. `dashboard/settings.html` lo renderiza como
formulario, precarga los valores vigentes (`config.json`, que exporta el generador) y emite un JSON.
No escribe (es estática): `/config` lo persiste con `scripts/apply_config.py`, validando y mandando
cada valor a su destino — operativos del proyecto → `particion.json`; tu cuenta (plan) →
`~/.claude/kit-config.json`. Añadir un parámetro futuro = una entrada en el manifiesto, sin tocar la
página ni el código.

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
