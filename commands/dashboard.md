---
description: Genera/actualiza el estado del dashboard web y explica cómo servirlo (consola de turno del equipo)
---

El **dashboard** es una consola web de solo lectura que pinta el estado del equipo —tablero Kanban,
unidades, WIP, integrador, consumo y cuello de botella— leyendo los ficheros que ya existen. No es un
demonio ni vigila en tiempo real: es un **lector de estado** que se refresca por ronda. Para ver a los
coders en vivo (diffs, terminal) usa la app de escritorio de Claude Code o CloudCLI; esto es la capa
*agregada* con tu vocabulario, que ninguna herramienta genérica conoce.

## Qué hace este comando
1. **Refresca el estado:** ejecuta el generador determinista
   ```bash
   python3 .claude/kit/scripts/build_dashboard_state.py
   ```
   Lee `particion.json` (unidades, `runtime.wip`, modelo por unidad), las bandejas
   `.claude/inbox/*.md` (tareas `[ABIERTO]`/`[EN CURSO]`/`[HECHO]`), `integrador.md` (cola de merge,
   migración pendiente) y, si está disponible, `ccusage` (gasto por modelo). Escribe
   `.claude/dashboard/state.json`. No usa LLM: es puro parsing.
2. **Confírmale al usuario** el resumen que imprime el script (nº de unidades, WIP usado/límite).

## Cómo servirlo (una vez)
El dashboard es `dashboard/index.html` (en el kit) o `.claude/dashboard/index.html` tras desplegar;
lee `state.json` por fetch con polling cada 10 s. Sírvelo con cualquier estático:
```bash
cd .claude/dashboard && python3 -m http.server 8787 --bind 127.0.0.1
```
- **Bíndalo a 127.0.0.1**, no a 0.0.0.0: el tablero no debe quedar expuesto en la red.
- Desde otra máquina (p. ej. tu portátil contra el Ubuntu de dev), llega por **túnel SSH**, no
  abriendo el puerto:
  ```bash
  ssh -L 8787:127.0.0.1:8787 usuario@ubuntu-dev
  # luego abre http://localhost:8787 en tu navegador
  ```
  Mismo patrón que ya usas para Portainer: servicio en localhost + túnel.

## Mantenerlo al día
`/pull-tasks` ya regenera el `state.json` al cerrar cada ronda (paso 8). Si trabajas en modo clásico
(una ventana por unidad), vuelve a lanzar `/dashboard` cuando quieras una foto fresca. El HTML se
repinta solo cada 10 s; no hace falta recargar la página.

## Límites honestos
- **Consumo por modelo**, no por unidad: ccusage agrega por modelo/sesión. El desglose por unidad
  exige OTel etiquetado por subagente (ver `docs/POSIBLES_COMPLEMENTOS.md` §1) y queda pendiente.
- **Cuello de botella y flujo** son heurísticos (cola de unidades vs cola del integrador). Útiles
  como señal, no como métrica exacta.
- Si `state.json` no existe aún, el HTML lo dice y te recuerda correr este comando.

$ARGUMENTS
