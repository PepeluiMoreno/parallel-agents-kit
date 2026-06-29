#!/usr/bin/env bash
#
# check-cierre.sh — hook SubagentStop que IMPONE la red de seguridad al cerrar una tarea.
#
# Tapa el agujero "si un agente dice «listo», el lead se lo cree": antes de dar por cerrada la sesión
# de una unidad, comprueba en el diff de su rama que no haya hecho algo que sólo el integrador puede
# hacer. RECHAZA el cierre (exit 2) si la rama de la unidad:
#   (a) tocó una ZONA CALIENTE sin pasar por el integrador, o
#   (b) introdujo una MIGRACIÓN (las redacta el integrador — ver ADR-migraciones-zona-caliente).
# Así la validación de cierre la enforced la configuración, no la buena voluntad del prompt. Es el
# complemento radial del ownership: el centro valida lo que el radio devuelve (ver
# ADR-topologia-estrella-no-teams: la estrella mete un punto de validación que la malla no tiene).
#
# Instalación: lo despliega /generate-config y lo cablea como hook SubagentStop en .claude/settings.json
# (con agent teams, el evento análogo es TaskCompleted). Requiere: jq, git.
#
# Contrato del hook (Claude Code):
#   - exit 0  → permite cerrar.
#   - exit 2  → bloquea el cierre y devuelve el stderr al modelo como motivo (lo obliga a arreglarlo
#               o a encaminarlo al integrador antes de terminar).

# FASE FAIL-OPEN (sin `set -e`): un hook nunca debe romper una sesión legítima. Si falta una
# dependencia (jq, git) o el contrato, salimos 0 ANTES de activar el modo estricto, para que un
# fallo de entorno no se convierta en un exit ≠ 0 que bloquee el cierre de cualquier agente.
set -uo pipefail
command -v jq  >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

PARTICION="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}/.claude/kit/particion.json"
[[ -f "$PARTICION" ]] || exit 0

# A partir de aquí ya tenemos jq + git + repo + contrato: podemos exigir rigor.
set -e

# 1. Unidad activa = sufijo de la rama feature/<unidad>. El integrador (rama base) SÍ puede tocar
#    zonas calientes y migrar: este gate sólo valida el cierre de las unidades.
RAMA="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
case "$RAMA" in
  feature/*) UNIDAD="${RAMA#feature/}" ;;
  *)         exit 0 ;;   # no es una rama de unidad → no aplicamos el gate
esac

# 2. Diff de la rama de la unidad respecto a la rama base (lo que esta sesión va a "entregar").
#    Base configurable; por defecto la del contrato, si no, master/main.
BASE="$(jq -r '.runtime.rama_base // empty' "$PARTICION" 2>/dev/null || true)"
if [[ -z "$BASE" ]]; then
  if git show-ref --verify --quiet refs/heads/master; then BASE=master; else BASE=main; fi
fi
# Sólo los ficheros tocados respecto al ancestro común; si la base no existe, no bloqueamos (fail-open).
git rev-parse --verify "$BASE" >/dev/null 2>&1 || exit 0
FICHEROS="$(git diff --name-only "$(git merge-base "$BASE" HEAD)"...HEAD 2>/dev/null || true)"
[[ -z "$FICHEROS" ]] && exit 0   # nada que entregar → nada que validar

# 3. Helper: ¿casa $1 (path relativo) alguno de los globs en $2 (array JSON)?  (idéntico a ownership)
casa_algun_glob() {
  local rel="$1" globs_json="$2" g
  while IFS= read -r g; do
    [[ -z "$g" ]] && continue
    shopt -s extglob globstar
    # shellcheck disable=SC2053
    [[ "$rel" == $g ]] && return 0
  done < <(jq -r '.[]' <<<"$globs_json")
  return 1
}

ZONAS="$(jq -c '.zonas_calientes // []' "$PARTICION")"
# Patrones que identifican una migración (Alembic/Django/Prisma/…). Configurable en el contrato.
MIGR="$(jq -c '.runtime.patrones_migracion // ["**/migrations/**","**/versions/**","**/alembic/**","**/prisma/migrations/**"]' "$PARTICION")"

for rel in $FICHEROS; do
  # 3a. ¿tocó una zona caliente? → el integrador es el único dueño; debió ir por /request-integration.
  if casa_algun_glob "$rel" "$ZONAS"; then
    echo "CIERRE BLOQUEADO: la rama de '$UNIDAD' modificó la ZONA CALIENTE '$rel'. Eso lo cablea el integrador. Revierte ese cambio y deja un bloque [PENDIENTE] en integrador.md (/request-integration) antes de cerrar. Ver ADR-topologia-estrella-no-teams (validación radial)." >&2
    exit 2
  fi
  # 3b. ¿introdujo una migración? → las redacta el integrador tras el merge (ADR-migraciones).
  if casa_algun_glob "$rel" "$MIGR"; then
    echo "CIERRE BLOQUEADO: la rama de '$UNIDAD' introdujo una MIGRACIÓN ('$rel'). Las unidades commitean el MODELO, no la migración: la redacta el integrador sobre el estado ya integrado (ADR-migraciones-zona-caliente). Quita la migración y deja el cambio de esquema en integrador.md." >&2
    exit 2
  fi
done

exit 0
