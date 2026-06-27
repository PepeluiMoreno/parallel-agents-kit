# Manual del equipo de desarrollo virtual (PDF)

Genera `MANUAL_MULTIAGENTE.pdf` (portada + conceptos + diagrama SVG + comandos + secuencia + loops).

```bash
uv venv .venv && . .venv/bin/activate
uv pip install weasyprint markdown
python gen_pdf.py        # produce MANUAL_MULTIAGENTE.pdf junto al script
```

Requiere las libs de sistema de WeasyPrint (Pango/Cairo/gdk-pixbuf), normalmente ya presentes en Linux de escritorio.
