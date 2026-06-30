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

STATE_RX = re.compile(r"\[(ABIERTO|EN CURSO|HECHO)\]\s*(.*)")
RESUELTO_RX = re.compile(r"\*\*Resuelto:\*\*")


def load_particion() -> dict:
    if not PARTICION.exists():
        return {}
    try:
        return json.loads(PARTICION.read_text(encoding="utf-8"))
    except Exception:
        return {}


def unit_model(unit: dict, default_model: str) -> str:
    """Modelo de la unidad: su override, o el por defecto. Normaliza a opus/sonnet/haiku."""
    m = (unit.get("model") or default_model or "").lower()
    for tag in ("opus", "sonnet", "haiku"):
        if tag in m:
            return tag
    return "sonnet"


def parse_inbox(unit_name: str) -> list[dict]:
    """Devuelve [{subject, state}] de la bandeja de una unidad."""
    f = INBOX / f"{unit_name}.md"
    if not f.exists():
        return []
    tasks: list[dict] = []
    for line in f.read_text(encoding="utf-8").splitlines():
        m = STATE_RX.search(line)
        if not m:
            continue
        state, rest = m.group(1), m.group(2).strip()
        # limpia markdown de viñeta/cabecera y deja el asunto legible
        subject = re.sub(r"^[#\-*\s]+", "", rest).strip(" :·-") or "(sin asunto)"
        tasks.append({"subject": subject[:80], "state": state})
    return tasks


def count_integrator_queue() -> dict:
    f = INBOX / "integrador.md"
    if not f.exists():
        return {"merge_queue": [], "migration_pending": False, "hotzones_touched": []}
    text = f.read_text(encoding="utf-8")
    pend = [
        re.sub(r"^[#\-*\s]+", "", l).strip()[:70]
        for l in text.splitlines()
        if "[PENDIENTE]" in l
    ]
    migration = bool(re.search(r"migraci|alembic|esquema|schema", text, re.I))
    return {
        "merge_queue": pend[:8],
        "migration_pending": migration,
        "hotzones_touched": [],
    }


def done_today_count() -> int:
    """Cuenta [HECHO] cuya línea o vecindad menciona la fecha de hoy; si no hay fechas, 0."""
    today = date.today().isoformat()
    n = 0
    for f in INBOX.glob("*.md"):
        if f.name.startswith("_"):
            continue
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "[HECHO]" in line and today in line:
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

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": part.get("proyecto") or ROOT.name,
        "methodology": "kanban-continuo",
        "wip": {"global_limit": wip_global, "global_used": global_used, "por_unidad": wip_unit},
        "columns": cols,
        "tasks": tasks,
        "units": units,
        "integrator": integ,
        "cost_by_model": ccusage_by_model(),
        "flow": {"done_today": cols["hecho_hoy"], "bottleneck": bottleneck},
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    state = build()
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"dashboard: estado escrito en {OUT.relative_to(ROOT)} "
          f"({len(state['units'])} unidades, {state['wip']['global_used']}/{state['wip']['global_limit']} WIP)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
