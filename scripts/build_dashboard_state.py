#!/usr/bin/env python3
"""build_dashboard_state.py — serializa el estado del equipo a .claude/dashboard/state.json.

Determinista, sin LLM: lee lo que ya existe (bandejas, particion.json, ccusage si está) y
emite el JSON que consume dashboard/index.html. Pensado para ejecutarse tras cada ronda
(lo llama /dashboard y, si se quiere, un hook al cierre de /pull-tasks).

Fuentes:
  .claude/kit/particion.json        → unidades, zonas calientes, runtime.wip, modelo por unidad
  .claude/inbox/<unidad>.md         → tareas [ABIERTO]/[EN CURSO]/[HECHO]
  .claude/inbox/integrador.md       → cola de integración
  .claude/inbox/_triage_log.md      → timestamps (flujo)
  ccusage (npx ccusage --json)      → consumo por modelo (opcional; si falla, se omite)

Diseño honesto: solo emite lo que puede derivar de verdad. El consumo se da POR MODELO
(lo que ccusage expone sin instrumentación extra); el desglose por unidad exige OTel
etiquetado por subagente y queda como mejora futura (ver docs/POSIBLES_COMPLEMENTOS.md §1).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


def repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except Exception:
        return Path.cwd()


ROOT = repo_root()
CLAUDE = ROOT / ".claude"
INBOX = CLAUDE / "inbox"
PARTICION = CLAUDE / "kit" / "particion.json"
OUT = CLAUDE / "dashboard" / "state.json"
CONFIG_OUT = CLAUDE / "dashboard" / "config.json"
MANIFEST = CLAUDE / "dashboard" / "params.manifest.json"
USER_CONFIG = Path.home() / ".claude" / "kit-config.json"

PLAN_LABEL = {"pro": "Pro (1x)", "max5x": "Max 5x", "max20x": "Max 20x", "api": "API"}
PLAN_MULT = {"pro": 1, "max5x": 5, "max20x": 20, "api": None}

# Una tarea real es un BLOQUE que empieza por una cabecera "## [ESTADO] <metadata>".
# Anclar en la cabecera evita contar comentarios (<!-- ... [ABIERTO] ... -->) y pies de leyenda
# que mencionen un estado. El asunto legible vive en la línea "**Asunto:**" del bloque, no tras el "]".
TASK_HDR_RX = re.compile(r"^##\s*\[(ABIERTO|EN CURSO|HECHO|EN ESPERA)\]")
ASUNTO_RX = re.compile(r"\*\*Asunto:\*\*\s*(.+)")
ID_RX = re.compile(r"\bid:([A-Za-z0-9_-]+)")
BLOCK_SPLIT_RX = re.compile(r"(?m)^(?=##\s*\[)")


def load_particion() -> dict:
    if not PARTICION.exists():
        return {}
    try:
        return json.loads(PARTICION.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_user_config() -> dict:
    """Config de ámbito usuario (~/.claude/kit-config.json): plan, etc. Mismo en todos los repos."""
    if not USER_CONFIG.exists():
        return {}
    try:
        return json.loads(USER_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _dig(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def export_config(part: dict, user: dict) -> None:
    """Vuelca los valores VIGENTES de cada parámetro del manifiesto → config.json, para que la
    página de ajustes los precargue. Si no hay manifiesto, no hace nada."""
    if not MANIFEST.exists():
        return
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return
    values: dict[str, object] = {}
    for group in manifest.get("groups", []):
        src = user if group.get("scope") == "user" else part
        for p in group.get("params", []):
            v = _dig(src, p["key"])
            values[p["key"]] = v if v is not None else p.get("default")
    CONFIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_OUT.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")


def unit_model(unit: dict, default_model: str) -> str:
    """Modelo de la unidad: su override, o el por defecto. Normaliza a opus/sonnet/haiku."""
    m = (unit.get("model") or default_model or "").lower()
    for tag in ("opus", "sonnet", "haiku"):
        if tag in m:
            return tag
    return "sonnet"


def parse_inbox(unit_name: str) -> list[dict]:
    """Devuelve [{subject, state, id}] de la bandeja de una unidad.

    Parte el fichero en bloques por cabecera "## [ESTADO]" y solo cuenta los que la tienen; el
    asunto sale de la línea **Asunto:** (o del id: si no hay), nunca de los metadatos tras el "]".
    Así los comentarios de cabecera y los pies de leyenda que mencionan estados no cuentan como tareas.
    """
    f = INBOX / f"{unit_name}.md"
    if not f.exists():
        return []
    tasks: list[dict] = []
    for block in BLOCK_SPLIT_RX.split(f.read_text(encoding="utf-8")):
        m = TASK_HDR_RX.match(block)
        if not m:
            continue
        state = m.group(1)
        header = block.splitlines()[0]
        idm = ID_RX.search(header)
        am = ASUNTO_RX.search(block)
        subject = (am.group(1).strip() if am else (idm.group(1) if idm else "")).strip()
        tasks.append({
            "subject": (subject or "(sin asunto)")[:80],
            "state": state,
            "id": idm.group(1) if idm else None,
        })
    return tasks


def count_integrator_queue() -> dict:
    """Cola del integrador: bloques "## [PENDIENTE]" (cableados/migración esperando integración).

    Ancla en la cabecera, así el comentario de cabecera del fichero (<!-- [PENDIENTE] ... -->) y los
    bloques [ENTREGADO]/[ENCARGO]/[EN CURSO] no cuentan. migration_pending = algún [PENDIENTE]
    menciona migración/tabla (no se dispara por el texto de leyenda del fichero).
    """
    f = INBOX / "integrador.md"
    if not f.exists():
        return {"merge_queue": [], "migration_pending": False, "hotzones_touched": []}
    hdr_rx = re.compile(r"^##\s*\[PENDIENTE\]")
    label_rx = re.compile(r"\*\*(?:Asunto|Funcionalidad):\*\*\s*(.+)")
    mig_rx = re.compile(r"migraci|alembic|esquema|\btabla", re.I)
    pend: list[str] = []
    migration = False
    for block in BLOCK_SPLIT_RX.split(f.read_text(encoding="utf-8")):
        if not hdr_rx.match(block):
            continue
        lm = label_rx.search(block)
        label = lm.group(1).strip() if lm else block.splitlines()[0].lstrip("# ").strip()
        pend.append(label[:70])
        if mig_rx.search(block):
            migration = True
    return {
        "merge_queue": pend[:8],
        "migration_pending": migration,
        "hotzones_touched": [],
    }


def done_today_count() -> int:
    """Cuenta cabeceras "## [HECHO]" cuya línea menciona la fecha de hoy; si no hay fechas, 0."""
    today = date.today().isoformat()
    n = 0
    for f in INBOX.glob("*.md"):
        if f.name.startswith("_"):
            continue
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.lstrip().startswith("## [HECHO]") and today in line:
                n += 1
    return n


def ccusage_by_model() -> list[dict]:
    """Intenta `npx ccusage --json`; agrega coste por modelo de HOY. Si falla, lista vacía."""
    try:
        out = subprocess.run(
            ["npx", "--yes", "ccusage", "--json"],
            capture_output=True, text=True, timeout=40,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return []
        data = json.loads(out.stdout)
    except Exception:
        return []
    # ccusage expone estructuras variables entre versiones; buscamos costes con etiqueta de modelo.
    buckets: dict[str, float] = {}
    def walk(node):
        if isinstance(node, dict):
            model = node.get("model") or node.get("modelName")
            cost = node.get("costUSD") or node.get("totalCost") or node.get("cost")
            if model and isinstance(cost, (int, float)):
                key = str(model).lower()
                tag = next((t for t in ("opus", "sonnet", "haiku") if t in key), key)
                buckets[tag] = buckets.get(tag, 0.0) + float(cost)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(data)
    total = sum(buckets.values()) or 1.0
    return [
        {"model": k, "usd": round(v, 2), "pct": round(100 * v / total)}
        for k, v in sorted(buckets.items(), key=lambda kv: -kv[1])
    ]


def build() -> dict:
    part = load_particion()
    runtime = part.get("runtime", {}) or {}
    wip = runtime.get("wip", {}) or {}
    wip_global = int(wip.get("global", 4))
    wip_unit = int(wip.get("por_unidad", 1))
    default_model = part.get("model_por_defecto") or "sonnet"

    raw_units = part.get("unidades", []) or []
    units, tasks = [], []
    cols = {"abierto": 0, "en_curso": 0, "hecho_hoy": 0}
    global_used = 0

    for u in raw_units:
        name = u.get("nombre") or u.get("name") or "?"
        model = unit_model(u, default_model)
        inbox_tasks = parse_inbox(name)
        n_open = sum(1 for t in inbox_tasks if t["state"] == "ABIERTO")
        n_prog = sum(1 for t in inbox_tasks if t["state"] == "EN CURSO")
        cols["abierto"] += n_open
        cols["en_curso"] += n_prog
        current = next((t["subject"] for t in inbox_tasks if t["state"] == "EN CURSO"), None)

        if n_prog > 0:
            st, global_used = "work", global_used + 1
        elif n_open > 0:
            st = "queue"
        else:
            st = "idle"

        units.append({
            "name": name, "state": st, "model": model,
            "current": current, "wip_used": n_prog, "wip_limit": u.get("wip", wip_unit),
        })
        for t in inbox_tasks:
            if t["state"] in ("ABIERTO", "EN CURSO"):
                tasks.append({"subject": t["subject"], "unit": name,
                              "state": t["state"], "model": model})

    cols["hecho_hoy"] = done_today_count()
    integ = count_integrator_queue()
    queued_units = sum(1 for u in units if u["state"] == "queue")
    bottleneck = None
    if integ["merge_queue"] and queued_units:
        bottleneck = "integrador — unidades esperando hueco de WIP"
    elif queued_units:
        bottleneck = f"{queued_units} unidad(es) en cola sin hueco de WIP"

    user = load_user_config()
    plan = user.get("plan")
    rate = ccusage_by_model()  # ritmo aproximado de la ventana (tokens/€ por modelo), NO saldo oficial
    quota = {
        "plan": plan,
        "plan_label": PLAN_LABEL.get(plan),
        "plan_multiplier": PLAN_MULT.get(plan),
        "rate_by_model": rate,            # proxy de consumo de la ventana de 5h; saldo real en Settings>Usage
        "plan_mode_multiplier": 7,        # recordatorio: teammates en plan mode queman ~7x
        "balance_url": "https://claude.ai/settings/usage",
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": part.get("proyecto") or ROOT.name,
        "methodology": "kanban-continuo",
        "wip": {"global_limit": wip_global, "global_used": global_used, "por_unidad": wip_unit},
        "columns": cols,
        "tasks": tasks,
        "units": units,
        "integrator": integ,
        "quota": quota,
        "flow": {"done_today": cols["hecho_hoy"], "bottleneck": bottleneck},
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    part = load_particion()
    export_config(part, load_user_config())
    state = build()
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"dashboard: estado escrito en {OUT.relative_to(ROOT)} "
          f"({len(state['units'])} unidades, {state['wip']['global_used']}/{state['wip']['global_limit']} WIP, "
          f"plan={state['quota']['plan'] or 'sin configurar'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
