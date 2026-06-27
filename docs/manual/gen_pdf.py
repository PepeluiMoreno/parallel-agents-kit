#!/usr/bin/env python3
# Genera el manual del Equipo de desarrollo virtual en PDF (WeasyPrint).
import markdown, pathlib
from weasyprint import HTML

HERE = pathlib.Path(__file__).parent
SVG = (HERE / "diagrama.svg.html").read_text(encoding="utf-8")
OUT = str(HERE / "MANUAL_MULTIAGENTE.pdf")  # genera junto a este script

# ---------- contenido en markdown (cuerpo) ----------
# El escenario gráfico se inyecta como SVG inline donde está el marcador.
MD = r"""
## 1 · ¿Qué es esto y para qué sirve?

Cuando trabajas con **un solo chat** de Claude, todo va en fila india: una tarea, luego otra, luego
otra. Si tu proyecto tiene partes independientes (lo económico, los miembros, las actividades…),
estás desaprovechando que **podrían avanzar a la vez**.

El **Equipo de desarrollo virtual** convierte tu proyecto en eso, un equipo: varios agentes
trabajando **en paralelo**, cada uno en su parcela, sin pisarse, con un **jefe** que junta el
trabajo, un **buzón** que recoge tus peticiones y las reparte, y un **responsable de producto** que
diseña contigo qué construir. El objetivo es uno solo: **disparar la productividad** haciendo varias
cosas a la vez con seguridad.

> **La promesa:** sueltas peticiones desordenadas; el equipo se organiza, trabaja en paralelo y te
> devuelve el proyecto integrado y limpio. Tú decides cuándo se sube a producción.

---

## 2 · Los conceptos, sin tecnicismos

**Repositorio (repo).** La carpeta de tu proyecto con todo su historial de cambios (lo gestiona
*git*). Es el sitio único donde vive el código.

**git worktree.** Aquí está el truco que lo hace todo posible. Un *worktree* es una **copia de
trabajo** del mismo repo en **otra carpeta**, que comparte el mismo historial pero tiene su propia
"mesa de trabajo" y su propia rama. Así, el agente de *económico* edita en su carpeta y el de
*miembros* en la suya, **a la vez, sin tocar los mismos ficheros**. No son copias duplicadas que
luego haya que sincronizar a mano: son ventanas al mismo repo. *Por eso el equipo necesita git.*

**Rama (branch).** Una línea de trabajo paralela. Cada agente trabaja en su rama (`feature/economico`,
`feature/miembros`…); el jefe las **fusiona** (merge) en la rama principal cuando están listas.

**Unidad.** El trozo del proyecto que **posee** un agente (un dominio como "económico", o una capa,
lo que tenga sentido). Cada unidad posee **ficheros distintos** de las demás: esa es la regla que
evita choques.

**Zona caliente.** Ficheros que tocan **muchas** unidades a la vez (el menú de rutas, el esquema
central de la API, las migraciones de la base de datos, los componentes comunes). Si dos agentes
los editan a la vez → choque garantizado. Por eso tienen **un dueño único: el jefe**.

**Agente vs. subagente.** Un *agente* es un chat de Claude Code. Un *subagente* es un agente que
**otro agente lanza por debajo**. Esta distinción es la clave de la comodidad: en vez de que **tú**
abras una ventana por sala, **un solo chat** (el jefe) lanza un subagente por unidad. Una ventana,
muchos trabajadores.

**Integrador (el jefe).** El único que toca zonas calientes, fusiona ramas y aplica migraciones.
Centraliza lo delicado para que nada choque.

**Buzón.** Un chat que recibe tus quejas/ideas desordenadas, las **clasifica** por unidad y las
**encola** en una lista de tareas (la *bandeja* de cada unidad). No arregla nada: solo reparte.

**Loop (modo en bucle).** Hacer que el equipo repita el trabajo **solo**, sin que tú relances cada
vez: va vaciando las tareas pendientes hasta que no queda ninguna. Útil para dejarlo trabajando
mientras haces otra cosa. Se explica en el apartado 8.

---

## 3 · El objetivo en una imagen

Escenario real: **cuatro unidades avanzando a la vez** (económico, miembros, actividades,
secretaría), un solo chat de por medio, y el resultado integrado al final.

@@SVG@@

**Cómo se lee:** tú escribes `/orquestar` en **una sola ventana**. Ese chat (el jefe) mira las
bandejas, lanza **un subagente por unidad con trabajo**, todos en paralelo y cada uno en su
worktree. Cuando vuelven, **el mismo chat** fusiona las ramas, cablea las zonas calientes, aplica
las migraciones una sola vez y valida. Lo que sale es la rama principal **integrada y limpia** —
que solo se sube a GitHub cuando **tú** lo pides.

---

## 4 · Instalación en un proyecto nuevo

Un chat de Claude Code solo reconoce los comandos `/...` que estén en la carpeta
`.claude/commands/` **del repositorio donde está abierto el chat**. Instalar el kit es, por tanto,
copiarlo a ese repo. De cero:

```
# 1. El proyecto debe ser un repo git (el aislamiento son git worktrees)
cd /ruta/a/mi-proyecto
git init                         # solo si todavía no es un repo

# 2. Instalar el kit en ese repo
/ruta/al/parallel-agents-kit/install.sh /ruta/a/mi-proyecto
#    (o, ya dentro del repo:  /ruta/al/parallel-agents-kit/install.sh . )
```

`install.sh` copia los comandos a `.claude/commands/` (donde Claude los descubre) y el resto del
kit —schema y plantillas— a `.claude/kit/`. Si el destino no es un repo git, avisa y se detiene.

```
# 3. Abrir un chat en ESE repo y refrescar el descubrimiento de comandos
#    - en VSCode: abre la carpeta del proyecto y empieza un chat ahí;
#    - si el chat ya estaba abierto, recárgalo (los comandos se leen al iniciar la sesión).
```

> **Las dos causas de un "Unknown command":** (1) los comandos no están en el `.claude/commands/`
> del repo abierto —falta correr `install.sh`—, o (2) sí están pero el chat se abrió antes de
> instalarlos: **recarga la sesión** y aparecerán.

Hecho esto, ya puedes usar la secuencia del apartado siguiente, empezando por `/analizar-proyecto`.

---

## 5 · Los comandos

> Un *comando* se escribe empezando por `/`. Cada uno lo usa un rol distinto.

| Comando | Quién lo usa | Qué hace |
|---|---|---|
| `/analizar-proyecto` | el arquitecto | Escanea la estructura del proyecto y **propone** cómo repartirlo en unidades. No despliega: espera tu visto bueno. |
| `/desplegar-equipo` | el arquitecto | Con tu reparto aprobado, **monta** todo: worktrees, protocolo, bandejas, comandos. |
| `/orquestar` | el jefe | **Modo 1 ventana.** Lanza un subagente por unidad con tareas y luego integra. |
| `/orquestar-loop` | el jefe | **Modo en bucle (desatendido).** Va resolviendo las tareas pendientes solo, sin que relances; **te pide permiso** antes de juntar el trabajo o migrar. Se usa con `/loop`. Ver apartado 8. |
| `/inbox` | un agente de unidad | Lee su bandeja y se pone a trabajar sus tareas (modo "una ventana por unidad"). |
| `/pedir-cableado` | un agente de unidad | Cuando necesita una zona caliente, **no la toca**: deja la petición al jefe. |
| `/integrar` | el jefe | Fusiona las ramas listas, aplica los cableados pedidos y las migraciones. |
| `/triaje` | el buzón | Clasifica una nota tuya y la **encola** en la bandeja de la unidad correcta. |
| `/producto` | el responsable de producto | **Propone** funcionalidad, la **diseña contigo** paso a paso y, con tu OK, la descompone en tareas y las encola. Ver apartado 7. |
| `/aceptar` | el responsable de producto | Comprueba que una funcionalidad terminada **cumple lo acordado** y te lo resume para tu visto bueno. |

---

## 6 · La secuencia de uso

**Puesta en marcha (una sola vez por proyecto):**

```
1.  /analizar-proyecto      → el arquitecto propone el reparto en unidades
2.  (revisas y ajustas el reparto)
3.  /desplegar-equipo       → se monta todo el andamiaje
```

**Diseñar funcionalidad nueva (cuando quieres construir algo, no arreglar):**

```
/producto                  → el responsable de producto propone y diseña contigo;
                             con tu OK, encola las tareas para el equipo
/aceptar                   → cuando esté hecho, valida que cumple lo acordado
```

**El día a día (bugs y mejoras sueltas):**

```
"eres el buzón, /triaje: <tu queja tal cual>"     → encola la tarea
        (puedes soltar varias quejas seguidas; el buzón las reparte)
/orquestar                 → el jefe lanza los subagentes y luego integra
(cuando quieras subir)     "sube la rama principal a GitHub"
```

**Dejarlo trabajando solo (cuando tienes varias tareas y vas a estar a otra cosa):**

```
/loop /orquestar-loop       → va resolviendo las tareas pendientes solo;
                              te pide permiso antes de juntar el trabajo o migrar;
                              se apaga solo cuando no queda nada. (Ver apartado 8.)
```

> **Local vs. GitHub.** Todo el baile de ramas ocurre **en tu ordenador**. En GitHub solo está la
> rama principal, y **solo se sube cuando tú lo pides**. Ningún agente sube nada por su cuenta.

---

## 7 · Decidir QUÉ construir: el responsable de producto

Hasta aquí el equipo sabe **construir**. Pero ¿quién decide **qué** construir? Para eso está el
**responsable de producto** (en inglés, *product owner*): un agente que **no programa**, sino que
**diseña producto contigo** y luego le pasa el encargo al equipo.

### Cómo trabaja
Es **proactivo**: conoce tu negocio (a partir de una breve *ficha de dominio* que apruebas al
principio) y **te propone funcionalidades** que cree que faltan. A partir de ahí, vais diseñándolas
**en conversación, una decisión cada vez**, y él **te pide el visto bueno en cada paso**:

1. **Propone** una funcionalidad y te explica por qué. → la abordáis o no.
2. **Alcance y flujos:** qué entra, qué no, y cómo es el proceso paso a paso. → lo validas.
3. **UI:** cómo se ve y se usa. → lo validas.
4. **Reglas de negocio:** validaciones, permisos, casos límite. → las confirmas.
5. **Criterios de aceptación:** la lista de "esto está hecho cuando…".
6. **Descompone** la funcionalidad en tareas (una por área) y **te las enseña antes de encolar**.

Solo con tu **OK final**, escribe esas tareas en las bandejas —con todo el detalle: flujo, UI,
reglas y criterios— y el equipo de desarrollo se pone (`/orquestar`). Cuando terminan, el propio
responsable **comprueba que lo entregado cumple lo acordado** y te lo resume para tu visto bueno.

### Dónde encaja
Llevas el diálogo con el comando `/producto`; la validación final, con `/aceptar`. Todo lo decidido
queda guardado en un **backlog de producto** (una ficha por funcionalidad, con su estado), para que
nada se pierda entre sesiones y veas siempre qué hay propuesto, aprobado o en marcha.

> **Responsable de producto vs. buzón.** El **buzón** es reactivo: recoge bugs y quejas sueltas que
> tú reportas. El **responsable de producto** es proactivo: propone y diseña **funcionalidad nueva**
> contigo. Uno apaga fuegos; el otro construye el futuro del producto.

---

## 8 · Trabajar desatendido: el modo en bucle

### ¿Qué es?
Normalmente tú disparas el trabajo: escribes `/orquestar` y el equipo hace una ronda. El **modo en
bucle** es lo mismo pero **repitiéndose solo**: el equipo va mirando las tareas pendientes y las va
sacando **sin que tú tengas que relanzar nada**, hasta que no queda ninguna. Entonces se apaga.

Se activa así:

```
/loop /orquestar-loop
```

### ¿Para qué sirve?
Para que el proyecto **avance solo mientras tú haces otra cosa**. En vez de estar pendiente de
escribir `/orquestar` cada rato, vas soltando peticiones al buzón cuando se te ocurren —por la
mañana, en una reunión, desde el móvil— y el equipo las va resolviendo por su cuenta. Tú llegas
luego y te encuentras el trabajo hecho.

### ¿Cuándo conviene usarlo?
- ✅ Cuando tienes **muchas tareas acumuladas** en las bandejas y quieres que se vayan resolviendo
  sin supervisarlas una a una.
- ✅ Cuando vas a **estar un rato sin atender** (otra tarea, una comida, fin de jornada) y quieres
  que el equipo siga produciendo.
- ✅ Cuando las tareas son **independientes y rutinarias**, del tipo "ir despachando el backlog".

### ¿Cuándo NO?
- ❌ Para **una sola tarea** o algo urgente que quieres ver al momento: usa `/orquestar` normal.
- ❌ Cuando estás haciendo algo **delicado o experimental** que prefieres vigilar paso a paso.

> **La regla rápida:** ¿muchas tareas pendientes y te vas a despreocupar un rato? → modo en bucle.
> ¿una cosa concreta que quieres ver ya? → `/orquestar` normal.

### Un ejemplo de principio a fin
Es viernes a las 13:30. Antes de ir a comer has ido apuntando seis cosas sueltas en el buzón a lo
largo de la mañana: *"el botón de exportar recibos no filtra por fecha"*, *"falta el aviso de email
duplicado en altas"*, *"el listado de socios no ordena por antigüedad"*, y tres más. Son tareas
independientes, de varias áreas, ninguna urgente. En vez de quedarte despachándolas una a una,
escribes:

```
/loop /orquestar-loop
```

Te vas a comer. Mientras tanto, el equipo:

1. mira las bandejas y ve esas seis tareas repartidas por áreas (económico, miembros…);
2. lanza un trabajador por cada área con tareas, **todos a la vez**, y van resolviéndolas;
3. cuando una ronda termina, vuelve a mirar por si quedan más y repite;
4. al llegar al punto de **juntar el trabajo de todos** (que es lo delicado), **se detiene y deja
   una nota pidiéndote permiso** en lugar de hacerlo por su cuenta;
5. cuando ya no quedan tareas pendientes, **se apaga**.

Vuelves a las 15:00 y te encuentras las seis tareas resueltas, cada una en su sitio, y un aviso de
"listo para juntar e integrar, ¿le doy?". Tú revisas y das el OK. **Has producido una tarde de
trabajo del equipo sin estar delante.**

### Tranquilidad: nunca toca lo irreversible sin avisarte
El bucle automatiza la parte **segura** (que cada agente avance sus tareas en su propia copia de
trabajo; eso siempre se puede deshacer). Pero la parte **delicada** —juntar el trabajo de todos,
tocar las piezas compartidas y cambiar la base de datos— es difícil de revertir, así que el bucle
**se detiene y te pide permiso** antes de hacerla. Y cuando ya no quedan tareas, **se apaga solo**;
no se queda dando vueltas en vano. En resumen: trabaja solo en lo seguro, te llama para lo serio.

---

## 9 · Las tres reglas que nunca se rompen

1. **Un fichero, un dueño.** Cada unidad edita lo suyo; el jefe, las zonas calientes. Nadie toca lo
   que no posee. Si una tarea cruza fronteras, se **deriva** a la bandeja de la unidad dueña (no se
   invade).
2. **Solo el jefe fusiona y migra.** La base de datos es una y compartida: si varios migran a la
   vez, se rompe. Por eso esa parte está centralizada y supervisada.
3. **A GitHub solo sube la rama principal, y solo cuando tú lo pides.** Las ramas de trabajo son
   carriles desechables que viven en tu máquina.
"""

# ---------- CSS de impresión ----------
CSS = r"""
@page {
  size: A4;
  margin: 20mm 18mm 18mm 18mm;
  @bottom-center {
    content: "Equipo de desarrollo virtual · " counter(page) " / " counter(pages);
    font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 8.5pt; color: #94a3b8;
  }
}
@page :first { @bottom-center { content: ""; } }

* { box-sizing: border-box; }
body {
  font-family: 'Helvetica Neue', 'Segoe UI', Arial, sans-serif;
  font-size: 10.3pt; line-height: 1.5; color: #1e293b; margin: 0;
}

/* ---- portada (sin fondo de color) ---- */
.cover {
  page-break-after: always; height: 247mm; position: relative;
  background: #fff; color: #1e293b; padding: 30mm 4mm;
  border-top: 5px solid #4f46e5;
}
.cover .kicker { font-size: 11pt; letter-spacing: 3px; text-transform: uppercase; color: #4f46e5; font-weight: 600; }
.cover h1 { font-size: 34pt; line-height: 1.08; margin: 14mm 0 6mm 0; font-weight: 800; color: #0f172a; }
.cover .sub { font-size: 13.5pt; color: #475569; max-width: 130mm; font-weight: 400; }
.cover .badges { position: absolute; bottom: 30mm; left: 4mm; right: 4mm; }
.cover .badge {
  display: inline-block; background: #eef2ff; border: 1px solid #c7d2fe; color: #4338ca;
  border-radius: 999px; padding: 4px 13px; font-size: 9.5pt; margin: 0 8px 8px 0;
}
.cover .foot { position: absolute; bottom: 16mm; left: 4mm; font-size: 9.5pt; color: #94a3b8; }

/* ---- cuerpo ---- */
h2 {
  font-size: 16pt; color: #4338ca; margin: 9mm 0 3mm 0; padding-bottom: 2mm;
  border-bottom: 2px solid #e0e7ff; page-break-after: avoid;
}
h3 { font-size: 12pt; color: #0f172a; margin: 5mm 0 2mm 0; page-break-after: avoid; }
p { margin: 0 0 2.6mm 0; }
strong { color: #0f172a; }

ul, ol { margin: 0 0 3mm 0; padding-left: 6mm; }
li { margin-bottom: 1.4mm; }

blockquote {
  margin: 3mm 0; padding: 3mm 5mm; background: #eef2ff; border-left: 4px solid #6366f1;
  border-radius: 0 6px 6px 0; color: #3730a3;
}
blockquote p { margin: 0; }

table { width: 100%; border-collapse: collapse; margin: 3mm 0 4mm 0; font-size: 9.4pt; }
th { background: #4f46e5; color: #fff; text-align: left; padding: 2.2mm 3mm; font-weight: 600; }
td { padding: 2.2mm 3mm; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
td code, th code { background: transparent; }

code {
  font-family: 'SF Mono', 'Consolas', monospace; font-size: 9pt;
  background: #f1f5f9; color: #be123c; padding: 1px 4px; border-radius: 4px;
}
pre {
  background: #0f172a; color: #e2e8f0; padding: 4mm 5mm; border-radius: 8px;
  font-size: 9pt; line-height: 1.5; overflow: hidden; margin: 3mm 0 4mm 0;
  page-break-inside: avoid;
}
pre code { background: transparent; color: #e2e8f0; padding: 0; font-size: 9pt; }

.diagram { text-align: center; margin: 4mm 0; page-break-inside: avoid; }
.diagram svg { width: 100%; height: auto; max-height: 150mm; }
.caption { font-size: 8.6pt; color: #64748b; text-align: center; margin-top: 1mm; }
h2 { page-break-inside: avoid; }
"""

# ---------- portada ----------
COVER = r"""
<div class="cover">
  <div class="kicker">Guía práctica</div>
  <h1>Equipo de<br>desarrollo virtual</h1>
  <div class="sub">Agentes de Claude Code que diseñan, implementan e integran tu aplicación en
  paralelo sobre el mismo proyecto, sin pisarse — desde una sola ventana.</div>
  <div class="badges">
    <span class="badge">responsable de producto</span>
    <span class="badge">desarrollo en paralelo</span>
    <span class="badge">integrador &middot; buzón</span>
    <span class="badge">desde una sola ventana</span>
    <span class="badge">modo en bucle</span>
  </div>
  <div class="foot">Proyecto SIGA &middot; generado con WeasyPrint</div>
</div>
"""

body_html = markdown.markdown(MD, extensions=["tables", "fenced_code"])
body_html = body_html.replace("<p>@@SVG@@</p>",
                              f'<div class="diagram">{SVG}</div>'
                              '<div class="caption">Escenario: 4 unidades en paralelo desde una sola ventana — '
                              'fan-out a subagentes, vuelta, integración y rama principal limpia.</div>')

html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<style>{CSS}</style></head><body>{COVER}{body_html}</body></html>"""

HTML(string=html, base_url=str(HERE)).write_pdf(OUT)
print("PDF generado en", OUT)
"""done"""
