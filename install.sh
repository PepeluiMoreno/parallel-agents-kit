#!/usr/bin/env bash
#
# install.sh — instala el kit multi-agente en un repo destino.
#
# Copia los comandos de runtime + bootstrap a <destino>/.claude/commands/ y el propio kit
# (schema + plantillas) a <destino>/.claude/kit/. NO crea worktrees ni analiza nada: eso lo
# hace luego /analizar-proyecto y /desplegar-tinglado desde el chat.
#
# Uso:
#   ./install.sh /ruta/al/repo/destino
#   ./install.sh .                       # repo actual
#
# Idempotente: sobrescribe los ficheros del kit, respeta el resto de .claude/.

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${1:-}"

if [[ -z "$DEST" ]]; then
  echo "uso: $0 <ruta-repo-destino>" >&2
  exit 2
fi
DEST="$(cd "$DEST" && pwd)"

# Requisito duro: el aislamiento son git worktrees.
if ! git -C "$DEST" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "✗ $DEST no es un repositorio git. El tinglado necesita git (aislamiento por worktrees)." >&2
  echo "  Inicialízalo con:  git -C \"$DEST\" init" >&2
  exit 1
fi

echo "▸ Kit:     $KIT_DIR"
echo "▸ Destino: $DEST"

mkdir -p "$DEST/.claude/commands" "$DEST/.claude/kit"

# 1. Comandos (runtime + bootstrap) → donde Claude Code los descubre
cp "$KIT_DIR"/commands/*.md "$DEST/.claude/commands/"
echo "✓ comandos copiados a .claude/commands/"

# 2. El kit en sí (schema + plantillas) → referencia para analizar/desplegar
cp -r "$KIT_DIR/schema"    "$DEST/.claude/kit/"
cp -r "$KIT_DIR/templates" "$DEST/.claude/kit/"
echo "✓ schema + plantillas copiados a .claude/kit/"

cat <<EOF

════════════════════════════════════════════════════════════════════
 LISTO. En un chat de Claude Code abierto en $DEST:

   1. /analizar-proyecto    → el arquitecto escanea y propone la partición
   2. (revisas/ajustas .claude/kit/particion.json)
   3. /desplegar-tinglado   → crea worktrees, protocolo, bandejas
   4. /orquestar            → empieza a trabajar en modo 1-ventana
════════════════════════════════════════════════════════════════════
EOF
