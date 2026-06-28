#!/usr/bin/env bash
#
# check-ownership.sh — hook PreToolUse que IMPONE el ownership de la partición.
#
# Lo invoca Claude Code antes de un Edit/Write/MultiEdit. Lee por stdin el JSON del tool input
# (que incluye el path a escribir), deriva la unidad activa de la rama git actual (feature/<unidad>),
# busca los globs `posee` de esa unidad en particion.json y RECHAZA (exit 2) si el path no le
# pertenece o si cae en una zona caliente. Así el ownership lo enforced la configuración, no la
# buena voluntad del prompt.
#
# Instalación: lo despliega /emitir-nativo y lo cablea como hook PreToolUse (matcher Edit|Write|
# MultiEdit) en .claude/settings.json. Requiere: jq, git.
#
# Contrato del hook (Claude Code):
#   - stdin: JSON con .tool_input.file_path (Edit/Write) o .tool_input.edits (MultiEdit).
#   - exit 0  → permite.
#   - exit 2  → bloquea y devuelve el stderr al modelo como motivo.

set -euo pipefail

PARTICION="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}/.claude/kit/particion.json"

# Sin contrato o sin jq → no bloqueamos (fail-open: el hook nunca debe romper una sesión legítima).
command -v jq >/dev/null 2>&1 || exit 0
[[ -f "$PARTICION" ]] || exit 0

# 1. Unidad activa = sufijo de la rama feature/<unidad>. El integrador (rama base) no se filtra aquí:
#    él SÍ puede tocar zonas calientes; este hook solo confina a las unidades.
RAMA="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
case "$RAMA" in
  feature/*) UNIDAD="${RAMA#feature/}" ;;
  *)         exit 0 ;;   # no estamos en una rama de unidad → no aplicamos confinamiento
esac

# 2. Path objetivo del tool (relativo a la raíz).
INPUT="$(cat)"
RAIZ="$(git rev-parse --show-toplevel)"
PATHS="$(jq -r '
  .tool_input as $t
  | ([$t.file_path] + ([$t.edits[]?.file_path] // []))
  | map(select(. != null)) | unique | .[]' <<<"$INPUT" 2>/dev/null || true)"
[[ -z "$PATHS" ]] && exit 0

# 3. Helper: ¿casa $1 (path relativo) alguno de los globs en $2 (array JSON)?
casa_algun_glob() {
  local rel="$1" globs_json="$2" g
  while IFS= read -r g; do
    [[ -z "$g" ]] && continue
    # bash extglob: traducimos el glob a comparación con [[ == ]]
    shopt -s extglob globstar
    # shellcheck disable=SC2053
    [[ "$rel" == $g ]] && return 0
  done < <(jq -r '.[]' <<<"$globs_json")
  return 1
}

POSEE="$(jq -c --arg u "$UNIDAD" '.unidades[] | select(.nombre==$u) | .posee' "$PARTICION")"
ZONAS="$(jq -c '.zonas_calientes // []' "$PARTICION")"

for abs in $PATHS; do
  rel="${abs#"$RAIZ"/}"
  # 3a. ¿zona caliente? → bloquear siempre (ninguna unidad las edita).
  if casa_algun_glob "$rel" "$ZONAS"; then
    echo "OWNERSHIP: '$rel' es ZONA CALIENTE. La unidad '$UNIDAD' no la edita; usa /solicitar-integracion (deja un bloque [PENDIENTE] en integrador.md). Ver PROTOCOLO §3." >&2
    exit 2
  fi
  # 3b. ¿pertenece a la unidad? → permitir; si no → bloquear.
  if [[ -z "$POSEE" || "$POSEE" == "null" ]]; then
    echo "OWNERSHIP: la unidad '$UNIDAD' no existe en particion.json. Revisa el contrato (/reinferir)." >&2
    exit 2
  fi
  if ! casa_algun_glob "$rel" "$POSEE"; then
    echo "OWNERSHIP: '$rel' NO pertenece a la unidad '$UNIDAD'. Edita solo tus globs 'posee'. Si el trabajo cae en otra unidad, deja una petición [POR ENCAMINAR] en _peticiones.md; no la invadas." >&2
    exit 2
  fi
done

exit 0
