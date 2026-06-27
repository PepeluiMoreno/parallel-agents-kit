---
description: Formaliza una petición de cableado al integrador (tocar una zona caliente)
---

Necesitas que el **integrador** toque una zona caliente que tú no puedes editar (router/índice de
rutas raíz, schema/registro raíz de API, migración, componente común, config global, etc. — lista
en `.claude/PROTOCOLO_MULTIAGENTE.md`).

NO edites la zona caliente. En su lugar:

1. Lee `.claude/AGENTE.local.md` para tu `UNIDAD`, y `git rev-parse --abbrev-ref HEAD` para tu rama.
2. Asegúrate de que TU parte ya está hecha y commiteada en tu rama (la vista, el resolver, el
   modelo, la migración generada sin aplicar…). El integrador parte de tu rama.
3. Añade (append) un bloque a `.claude/inbox/integrador.md` con este formato:

   ```markdown
   ## [PENDIENTE] <fecha ISO> · de:<UNIDAD> · rama:feature/<UNIDAD>
   **Necesito en zona caliente:**
   - <fichero>: <qué cambio concreto> (estado en mi rama: …)
   **Contexto:** <por qué, qué desbloquea>
   **Tras mergear mi rama**, aplica estos cableados.
   ---
   ```

   Sé MUY concreto: fichero exacto, símbolo/ruta a añadir, y dónde está ya hecho lo tuyo. El
   integrador no debe adivinar.
4. Usa `date -Iseconds` para la fecha real.
5. Avisa al usuario de que la petición quedó encolada para el integrador.

$ARGUMENTS
