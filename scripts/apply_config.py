#!/usr/bin/env python3
"""apply_config.py — persiste el payload de la página de ajustes en su sitio.

Lee por stdin (o de un fichero como argv[1]) el JSON que emite settings.html:
    { "project": { "runtime.wip.global": 4, ... }, "user": { "plan": "max20x" } }

Escribe cada valor en su destino, validando contra params.manifest.json:
  - claves `project` → .claude/kit/particion.json   (por ruta con puntos)
  - claves `user`    → ~/.claude/kit-config.json

Determinista, idempotente. No toca nada que no venga en el payload.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except Exception:
        return Path.cwd()


ROOT = repo_root()
PARTICION = ROOT / ".claude" / "kit" / "particion.json"
USER_CONFIG = Path.home() / ".claude" / "kit-config.json"
MANIFEST = ROOT / ".claude" / "dashboard" / "params.manifest.json"


def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def manifest_index() -> dict:
    """key → spec, para validar tipo/rango/enum."""
    m = load_json(MANIFEST, {})
    idx = {}
    for g in m.get("groups", []):
        for p in g.get("params", []):
            idx[p["key"]] = p
    return idx


def validate(key: str, val, spec: dict):
    t = spec.get("type")
    if t == "int":
        val = int(val)
        lo, hi = spec.get("min"), spec.get("max")
        if lo is not None and val < lo: raise ValueError(f"{key}={val} < min {lo}")
        if hi is not None and val > hi: raise ValueError(f"{key}={val} > max {hi}")
    elif t == "enum":
        if val not in spec.get("options", []):
            raise ValueError(f"{key}={val!r} no está en {spec.get('options')}")
    elif t == "bool":
        val = bool(val)
    return val


def set_dotted(d: dict, dotted: str, val) -> None:
    cur = d
    parts = dotted.split(".")
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
        if not isinstance(cur, dict):
            raise ValueError(f"ruta {dotted}: '{p}' no es objeto")
    cur[parts[-1]] = val


def apply(payload: dict) -> list[str]:
    idx = manifest_index()
    log: list[str] = []

    proj = payload.get("project", {}) or {}
    if proj:
        data = load_json(PARTICION, {})
        if not data:
            raise SystemExit("no hay particion.json todavía; usa /design-board primero")
        for k, v in proj.items():
            spec = idx.get(k)
            if not spec:
                log.append(f"  (ignorado, no en manifiesto) {k}")
                continue
            set_dotted(data, k, validate(k, v, spec))
            log.append(f"  proyecto · {k} = {v}")
        PARTICION.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    user = payload.get("user", {}) or {}
    if user:
        data = load_json(USER_CONFIG, {})
        for k, v in user.items():
            spec = idx.get(k)
            if spec:
                v = validate(k, v, spec)
            set_dotted(data, k, v)
            log.append(f"  cuenta · {k} = {v}")
        USER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        USER_CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return log


def main() -> int:
    raw = Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception as e:
        raise SystemExit(f"payload no es JSON válido: {e}")
    try:
        log = apply(payload)
    except (ValueError, SystemExit) as e:
        print(f"config NO aplicada: {e}", file=sys.stderr)
        return 1
    print("config aplicada:" if log else "nada que aplicar.")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
