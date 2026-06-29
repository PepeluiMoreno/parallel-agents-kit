# ¿Estamos reinventando Agent Teams? — Informe comparativo

> Fecha: 2026-06-27. Fuente: documentación oficial de Claude Code (code.claude.com/docs):
> `agents`, `agent-teams`, `sub-agents`, `worktrees`, `hooks`, `workflows`, `commands`.
> Objetivo: decidir si seguimos con el kit propio, pivotamos a lo nativo, o lo complementamos.
>
> **⚠️ Actualización (2026-06-29) — leer antes que el resto.** Este informe trata el mailbox/malla de
> agent teams como una capacidad que al kit *le falta* (§1, §2, §4-B/C) y recomienda adoptar teams
> «cuando deje de ser experimental» (§4 recomendación). Esa postura quedó **revisada**: ver
> `ADR-topologia-estrella-no-teams.md`. En resumen, la malla no es algo que falte sino algo que el
> modelo en **estrella** (coordinación radial vía integrador + contrato + backlog) **no necesita**;
> no se adopta teams por diseño, no por inmadurez. El análisis de equivalencias y de diferencial de
> abajo **sigue siendo válido**; lo que cambia es la *recomendación de topología*.

## TL;DR
La intuición del usuario era correcta: **Claude Code ya trae de serie la mayor parte de la
maquinaria de orquestación que montamos a mano.** Lo que de verdad NO existe nativo es el
**arranque inteligente** (un arquitecto que lee el repo e infiere quién posee qué) y la **capa de
producto** (responsable de producto + backlog). Recomendación: **no mantener un motor propio de
orquestación; quedarnos con el ~25% diferencial y apoyarlo sobre lo nativo.**

---

## 1. Lo que Claude Code ya hace NATIVO (y nosotros reinventamos)

Hay **cuatro** formas nativas de paralelizar, no una:

| Nativo | Qué hace | Qué nuestro/a pieza duplicaba |
|---|---|---|
| **Subagents** | Workers en una sesión, contexto propio, devuelven resumen. `isolation: worktree` en su frontmatter. | Nuestros subagentes de `/pull-tasks`. |
| **Agent teams** (experimental, flag) | Lead + teammates como sesiones independientes, **lista de tareas compartida** + **mailbox** (se mensajean entre sí), dependencias entre tareas que se desbloquean solas, hooks de calidad. | Nuestro jefe + bandejas + `_peticiones.md` + encaminamiento + `runtime.loop`. |
| **Worktrees** | `claude --worktree`, `EnterWorktree`, `.worktreeinclude` (copia `.env`), limpieza automática, hooks `WorktreeCreate/Remove`, base branch configurable. | Nuestro `montar-agentes.sh` + aislamiento por worktree. |
| **Dynamic workflows + `/batch`** | Script que lanza 5-30 subagentes aislados por worktree, cada uno con su PR, y cruza resultados. | Nuestra idea de fan-out masivo + loop-until-dry. |

**Conclusión dura:** el núcleo "lead + teammates + task list + mailbox + worktrees + gates por
hooks" **es nativo**. Mantenerlo a mano es reimplementar y mantener algo que Anthropic ya da (y
mejor: los teammates **se comunican entre sí directamente**, cosa que nuestros subagentes NO hacen).

### Mapa 1:1 de equivalencias
| Nuestro concepto | Equivalente nativo |
|---|---|
| Jefe / orquestador-integrador | **Team lead** |
| Subagente por unidad | **Teammate** (sesión independiente) o **subagent** |
| Bandejas `.claude/inbox/<unidad>.md` | **Shared task list** (`~/.claude/tasks/`) con estados pending/in-progress/completed |
| `_peticiones.md` + encaminamiento del jefe | **Mailbox** + dependencias entre tareas |
| `/request-integration` (zona caliente) | Tarea con dependencia + mensaje al lead |
| `runtime.loop` (freno) | **Hooks** `TeammateIdle` (exit 2 = sigue) |
| Validación de aceptación | **Hook** `TaskCompleted` (exit 2 = no completa hasta cumplir criterios) |
| Aislamiento por worktree | `--worktree` / `isolation: worktree` / `.worktreeinclude` |
| Roles reutilizables (integrador…) | **Subagent definitions** usadas como teammates |

---

## 2. Lo que NO existe nativo (nuestro diferencial real)

Verificado leyendo `agents`, `agent-teams` y `sub-agents`: **no hay** nada de esto en Claude Code.

1. **Arquitecto que infiere la partición.** Lo nativo te obliga a decir en lenguaje natural a quién
   lanzar y qué posee cada uno. **Nadie analiza tu repo, detecta el nivel de modularidad, empareja
   back↔front, marca zonas calientes y propone un `particion.json` para que valides.** Esto es
   100% nuestro (`/design-board` + contrato de datos).
2. **Ownership declarativo y persistente.** Agent teams dice "particiona para evitar conflictos"
   pero **no impone ownership**; queda en manos del prompt. Nuestro mapa de globs disjuntos +
   protocolo generado es un artefacto versionado y reutilizable entre sesiones.
3. **Capa de producto.** No existe responsable de producto, ni diálogo estructurado
   (propuesta→flujos→UI→reglas→criterios→encolar), ni **backlog de producto persistente** con ciclo
   de vida. Es lógica de negocio, no de orquestación: nativo no la cubrirá nunca.
4. **Disciplina de dominio "un solo integrador migra".** Regla nuestra (BD compartida). Replicable
   con un hook `TaskCompleted`, pero la *política* es nuestra.

---

## 3. Riesgos de apoyarse en lo nativo
- **Agent teams es EXPERIMENTAL** y va tras `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`. Limitaciones
  documentadas: no resiste `/resume` (pierde teammates in-process), estados de tarea que se quedan
  colgados, apagado lento, **un solo equipo por sesión**, **sin equipos anidados** (un teammate no
  puede lanzar los suyos), lead fijo. Para flujo desatendido serio, hoy es frágil.
- **Worktrees + agent teams NO se combinan automáticamente:** la doc dice explícitamente que los
  teammates **no** se aíslan en worktrees; hay que particionar a mano los ficheros. Justo el punto
  donde nuestro enfoque (worktree por unidad) es más fuerte — pero eso se logra con subagents
  `isolation: worktree`, no con agent teams.
- Depender de una API experimental = riesgo de que cambie bajo nuestros pies (ya pasó: `TeamCreate`/
  `TeamDelete` desaparecieron, `team_name` quedó deprecado).

---

## 4. Opciones y recomendación

**A) Pivotar a fino sobre lo nativo (recomendada).** Tirar nuestro motor de orquestación
(subagentes a mano, bandejas, `_peticiones.md`, encaminamiento, `/pull-tasks`, `/pull-loop`,
`/request-integration`, `/apply-integration`). Quedarnos SOLO con lo que no existe:
   - `/design-board` → produce el `particion.json` (sigue valiendo tal cual).
   - A partir de él, **generar la configuración nativa**: spawnear teammates/subagents con
     `isolation: worktree`, una **subagent definition por unidad** (con su ownership en el system
     prompt), y **hooks** `TaskCompleted`/`TeammateIdle` que impongan "no completar si toca zona
     caliente / si no pasa criterios". El ownership lo enforced un hook, no nuestro runtime.
   - Mantener la **capa de producto** (`/product-owner`, `/accept`, backlog) tal cual: alimenta la task
     list nativa en vez de nuestras bandejas.
   Resultado: ~75% menos código que mantener, y nos montamos sobre algo que Anthropic mejora solo.

**B) Mantener el kit independiente.** Cero dependencia de un flag experimental, control total,
portabilidad. Coste: mantenemos un motor que reimplementa lo nativo y nos perdemos el mailbox real
(comunicación directa entre teammates) que nosotros no tenemos.

**C) Híbrido por ahora.** Dejar el kit como está (funciona hoy con subagents estables, sin flag) y
**preparar** el pivote para cuando Agent Teams salga de experimental.

### Recomendación
**A cuando Agent Teams deje de ser experimental; C mientras tanto.** Hoy: conservar el kit actual
(usa subagents estables, sin flag), pero **dejar de invertir** en ampliar su motor de orquestación
(p.ej. no terminar el encaminamiento `_peticiones.md` como pieza propia: eso es mailbox nativo).
Concentrar el esfuerzo en lo único que es nuestro de verdad y que da valor: **el arquitecto que
infiere la partición y la capa de producto.**

---

## 4.bis Experiencia real de la comunidad (webreactiva.com/blog/claude-agent-teams)
Un artículo en español con uso real aporta avisos que la doc oficial NO da, y que refuerzan nuestro
diferencial:
- ⚠️ **"No hay validación automática entre pasos: si un teammate dice 'listo', el lead se lo cree."**
  Los errores se propagan en dominó. → Es EXACTAMENTE el agujero que tapan nuestra capa de producto
  (`/accept` contra criterios) y los hooks `TaskCompleted` como gate. No es lujo: es red de seguridad.
- 💸 **Coste real brutal:** un caso (compilador C) costó **20.000 USD**. Regla: 3 agentes = 3× tokens;
  mitigar con Sonnet para lo simple. → Desaconseja "desatendido pleno" sin control.
- 🖥️ La comunidad considera **tmux casi obligatorio** para ver/intervenir cada agente. Ojo: tmux NO
  funciona en la terminal integrada de VSCode (donde trabaja este usuario) → friconfig de visibilidad.
- El lead **implementa en vez de delegar** a veces (hay que forzarlo). Confirma limitación de la doc.
- Madurez: experimental pero funcional; recomiendan **empezar por code reviews, no refactors críticos**.
- **No menciona roles tipo product owner** → confirma que la capa de producto es diferencial nuestro.

## 4.ter Piezas reutilizables (guía FlorianBruniaux/claude-code-ultimate-guide)
Catálogo de buenas prácticas (no competidor; material para endurecer NUESTRO diferencial). Lo
adoptable de verdad:
- **Test "SPEC" para validar una subtarea antes de encolarla** (Específica · Evaluable
  programáticamente · alcance explícito · acotada). → Adoptar en `/product-owner` al descomponer y en los
  criterios de aceptación: filtra tareas mal definidas antes de que el equipo las coja.
- **Presupuestos de tokens por agente** ("mantente bajo 180K; auto-pausa y reporta al 85%"). →
  Respuesta directa al riesgo de coste (caso 20k USD). Adoptar en el prompt de subagentes de `/pull-tasks`.
- **Ciclos de recuperación de contexto (máx 3)**: el subagente pide más contexto de forma acotada en
  vez de inventar ("necesito [X] porque [Y]"). Mejora calidad sin barra libre.
- **Red flags para intervención humana**: agentes que acaban a tiempos muy dispares (mala
  descomposición), muchos conflictos de merge, tests fallando tras merge, naming inconsistente. →
  Checklist para el integrador en `/apply-integration`.
- **Patrón dual-instance** (planificador SIN herramientas → revisión humana → ejecutor CON
  herramientas). Encaja con nuestro arquitecto/PO: diseñar en read-only, aprobar, luego ejecutar.

Confirma además (sin novedad): sus 3 arquitecturas (fan-out/fan-in, fases paralelizadas, delegación
jerárquica) = las nuestras; worktrees + ficheros disjuntos = su recomendación central; y **sigue sin
haber partición inferida ni capa de producto** → diferencial nuestro intacto. Sus 23 agentes
(code-reviewer, security-auditor, test-writer…) son subagent definitions reutilizables al pivotar.
Cautela: las métricas del repo (casos "20k USD", "500K horas", quizzes) no están verificadas.

## 5. Acciones propuestas (a confirmar por el usuario)
1. **Congelar** el desarrollo del motor de orquestación del kit (no más bandejas/encaminamiento a mano).
2. **Probar** Agent Teams nativo en SIGA (flag en `settings.local.json`) con una tarea real de 2-3
   unidades, para medir su madurez de primera mano.
3. Según el resultado: reescribir `/design-board` para que **emita config nativa**
   (subagent definitions + hooks) en vez de nuestro protocolo + bandejas.
4. Mantener `/product-owner` + `/accept` + backlog como capa propia encima de lo nativo.
