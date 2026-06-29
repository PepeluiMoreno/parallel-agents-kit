# ADR · Modo greenfield: el kit SÍ genera código, acotado a un scaffold mínimo de catálogo

> Estado: **aceptada** · Fecha: 2026-06-29 · Ámbito: arranque de proyectos desde cero
> Relacionada con `ADR-topologia-estrella-no-teams.md` y `ADR-cliente-habla-solo-con-el-po.md`.

## Contexto

El arquitecto (`/design-board`) **infiere la partición de la estructura existente**: escanea
carpetas y módulos y reparte. Su receta presupone que hay algo que escanear. En un repo **vacío**
(git init, sin commits, sin estructura) no tiene nada que mirar → no puede inferir partición. El
Product Owner tampoco cubre el hueco: asume que el equipo y la estructura ya existen.

Resultado: **el kit no sabe arrancar un proyecto desde cero.** El usuario que quiere construir una
app nueva *en paralelo desde el principio* se queda sin punto de entrada. (Caso real que disparó este
ADR: un repo `crm` recién iniciado, vacío, con el kit instalado y nada que particionar.)

Hasta ahora el kit tenía una frontera deliberada: **planifica y orquesta, pero no genera código de
producto** (no es `create-react-app` ni `cookiecutter`). Cubrir greenfield obliga a revisar esa
frontera.

## Decisión

**En modo greenfield, el kit SÍ genera código — pero acotado a un *scaffold mínimo* derivado de un
stack de catálogo.** Es un cambio de frontera consciente, no un descuido; por eso se registra aquí.

El límite es la clave que lo hace aceptable. El kit genera:
- el **esqueleto de carpetas** según las buenas prácticas conocidas del stack elegido,
- **un placeholder por unidad** (un fichero mínimo que ancla la carpeta y da algo sobre lo que
  trabajar: un `__init__.py`, un componente vacío, un `index`),
- las **zonas calientes vacías pero existentes** (un `gql/schema.py` que agrega nada, un `app/main.py`
  mínimo, el directorio de migraciones inicializado),
- la **config base** imprescindible del stack (gestor de paquetes, entrypoint), no más.

El kit **NO** genera: lógica de negocio, modelos de dominio, endpoints reales, pantallas, tests de
producto. Eso lo construyen las unidades en sus tareas. La regla mental: *el scaffold es el esqueleto
canónico del stack; el músculo lo ponen los agentes.*

Por qué esto no rompe del todo la filosofía: generar el scaffold canónico de un stack conocido **no
es inventar producto, es aplicar una convención**. FastAPI+SQLAlchemy tiene un layout de buenas
prácticas conocido; emitirlo es plantilla, no creatividad. La frontera real que el kit sigue sin
cruzar es *escribir el producto*.

### De dónde sale la información: un cuestionario, no texto libre

El arquitecto en modo greenfield no recibe una descripción en prosa: conduce un **cuestionario
interactivo** que extrae justo lo que decide el scaffold y la partición:
- **tipo de app** (API, web fullstack, SPA + API, CLI…),
- **stack backend** (lenguaje, framework),
- **stack frontend** (framework, librería CSS / design system),
- **ORM / persistencia** (¿hay migraciones?),
- **colas / workers** (Celery, etc.),
- **monorepo vs repos separados** (¿el frontend es `self` o cross-repo?),
- **dominios del producto** (las áreas funcionales: contactos, oportunidades… — esto da las
  unidades verticales si las hay).

Las respuestas **predeterminan más que las carpetas**: deciden las **zonas calientes** (ORM con
migraciones → `versions/` caliente; design system → estilos compartidos calientes; schema raíz
agregador → caliente), las **unidades** (dominios + capas) y los **workers** (Celery → unidad/área de
tareas). El cuestionario es la entrada de TODO el `particion.json`, no solo del esqueleto.

### División determinista vs inferida

- **Scaffold de carpetas = casi determinista del stack.** Dado el stack, el layout sale de una base
  de conocimiento de convenciones. Poco margen de invención.
- **Estructura modular (unidades) = inferida del dominio** (+ del stack). Cuántas unidades y cómo
  cortar es el trabajo de siempre del arquitecto, aplicado sobre la estructura que él *va a crear* en
  vez de una que ya existe.

### Alcance de la base de conocimiento (KB)

**Pocos stacks bien hechos.** Se empieza con UN combo canónico —**FastAPI + SQLAlchemy + Alembic
(back) + Vue + Tailwind (front)**— con su scaffold de buenas prácticas codificado. El catálogo crece
después. Para un stack fuera de catálogo, el arquitecto avisa de que improvisará con criterio (menos
garantía de "canónico") o sugiere quedarse en el combo soportado. **No se promete soporte universal.**

## Flujo greenfield

```
(repo vacío) → /design-board detecta que no hay estructura → entra en modo greenfield
  1. Cuestionario interactivo (tipo app, stack, ORM, CSS, colas, monorepo, dominios)
  2. Propone: stack + estructura-objetivo + partición (unidades, zonas calientes, workers)
  3. El usuario valida (igual que en el modo normal)
  4. Genera el SCAFFOLD MÍNIMO (carpetas + placeholders + zonas calientes vacías + config base)
  5. Primer commit ("scaffold inicial: <stack>")
  6. Escribe particion.json sobre la estructura recién creada
→ /deploy-team (igual que siempre) → worktrees sobre el scaffold
→ las unidades construyen el producto en paralelo
```

El modo normal (proyecto existente) es **idéntico al de hoy**; greenfield es una rama que solo se
activa cuando el repo está vacío. Mismo comando, misma salida (`particion.json` validado).

## Alternativas consideradas

- **Comando aparte `/greenfield` o `/scaffold`.** Rechazada: duplica el principio rector y la lógica
  de partición. Es la misma tarea del arquitecto (proponer partición + validar) con un paso previo de
  cuestionario+scaffold; vive mejor como modo de `/design-board`.
- **No generar scaffold; solo proponer estructura en texto y que el usuario la cree.** Rechazada por
  el usuario: quería que el kit montara el esqueleto, no solo describirlo. (Era la postura más
  conservadora; se descartó a favor de generar scaffold mínimo.)
- **Que cada unidad monte su propio scaffold en su primera tarea.** Riesgo de stacks incompatibles si
  el contrato técnico es flojo; además deja el primer commit en manos del fan-out. Mejor un scaffold
  coherente único antes de desplegar.

## Consecuencias

**A favor:**
- El kit cubre el ciclo completo: de un repo vacío a un equipo trabajando en paralelo.
- El cuestionario garantiza que el arquitecto obtiene exactamente los datos que deciden el contrato
  (no se le olvida el ORM, que define la zona caliente de migraciones).

**En contra / límites:**
- El kit ahora **mantiene plantillas de scaffold por stack** — una superficie nueva que crece con
  cada stack del catálogo. Mitiga: pocos stacks, bien hechos; el resto, improvisado con aviso.
- "Mínimo" es una línea borrosa que hay que custodiar: si el scaffold engorda hacia una app completa,
  el kit invade el terreno de los generadores de proyectos. La regla "esqueleto sí, músculo no" es la
  guarda; revisar en cada stack nuevo.
- Cruza la frontera "el kit no genera código". Aceptado y acotado por este ADR.

## Cómo revertir

Quitar la rama greenfield de `commands/design-board.md` (la detección de repo vacío + el cuestionario
+ la generación de scaffold). El modo normal queda intacto. No hay estado persistente que migrar: un
proyecto ya scaffoldeado es indistinguible de uno hecho a mano para el resto del kit.
