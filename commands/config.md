---
description: Aplica los parámetros del equipo (WIP, loop, modelos, plan de Claude) que produce la página de ajustes
---

La página de ajustes del dashboard (`settings.html`) es un **editor**: produce un JSON pero no escribe
nada (es estática, sin backend). Este comando lo **persiste** en su sitio, de forma determinista y
validada contra `params.manifest.json`.

## Uso
1. El usuario te pega el JSON que generó la página, con esta forma:
   ```json
   { "project": { "runtime.wip.global": 4, "runtime.loop": "freno" },
     "user": { "plan": "max20x" } }
   ```
2. Aplícalo con el script (no edites los JSON a mano):
   ```bash
   echo '<el JSON pegado>' | python3 .claude/kit/scripts/apply_config.py
   ```
   El script:
   - valida cada valor contra el manifiesto (rango de `int`, opciones de `enum`),
   - escribe las claves `project` en `.claude/kit/particion.json` (por ruta con puntos),
   - escribe las claves `user` en `~/.claude/kit-config.json` (ámbito usuario: el plan es el mismo
     en todos tus repos, por eso NO se versiona en el proyecto).
3. Resúmele al usuario qué cambió (el script lo imprime) y recuérdale:
   - si tocó WIP/loop/modelos → afecta a la **próxima** ronda de `/pull-tasks`;
   - corre `/dashboard` para refrescar el estado y los relojes de cuota.

## Notas
- **Dos ámbitos, dos destinos.** Operativos del proyecto (WIP, loop, modo, triaje, modelo por
  defecto) → `particion.json`. Tu cuenta (plan) → config de usuario. La página ya los separa; el
  script respeta esa separación.
- **Validación.** Un valor fuera de rango o un enum inválido aborta sin escribir nada. Si una clave
  no está en el manifiesto, se ignora con aviso (no se cuela basura en el contrato).
- Si no existe `particion.json`, el script para: primero `/design-board`.
- Para **añadir** un parámetro editable nuevo, basta con añadir su entrada en
  `dashboard/params.manifest.json`: la página lo renderiza y este comando lo valida sin tocar código.

$ARGUMENTS
