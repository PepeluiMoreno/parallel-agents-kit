---
description: (Integrador) Mergea ramas de unidad listas, aplica cableados y migra contra la BD compartida
---

Eres el **integrador**. Vives en la raíz sobre la rama base y eres el ÚNICO que toca zonas
calientes, mergea y migra. Trabaja con cuidado y de forma supervisada.

1. Confirma rol y ubicación: `.claude/AGENTE.local.md` debe decir `ROL=integrador` y la rama actual
   ser la base. Si no, para y avisa.
2. **Estado del terreno:**
   - `git worktree list` — qué worktrees/ramas hay.
   - `git branch --list 'feature/*'` y, por cada una, `git log <base>..feature/<x> --oneline` para
     ver qué traería cada merge.
   - Lee `.claude/inbox/integrador.md` — peticiones de cableado `[PENDIENTE]`.
3. **Por cada rama lista para integrar** (confírmalo con el usuario si hay dudas):
   - `git merge --no-ff feature/<unidad>`. Resuelve conflictos con criterio: en zonas calientes
     manda la base + lo que pida el bloque de cableado.
   - Aplica los **cableados** que esa rama dejó en `integrador.md` (edita router/schema/registro/
     componentes comunes según el bloque).
   - Marca cada bloque `[PENDIENTE]` → `[CABLEADO]` con el hash del commit de cableado.
4. **Migraciones (solo aquí — las redactas TÚ):** si alguna rama trajo cambios de esquema (modelos
   nuevos/modificados):
   - con todas las ramas ya mergeadas, **redacta una única migración** que cubra el conjunto del
     cambio de esquema (autogenera contra los modelos ya integrados y revísala). Las unidades NO
     traen migraciones: traen modelos; tú redactas la migración una sola vez sobre el estado unido.
   - así no hay heads divergentes que reconciliar. Si por lo que sea llegaran migraciones en una
     rama, trátalo como excepción: colapsa a un solo head antes de aplicar.
   - aplica UNA sola vez contra la BD compartida.
   - reinicia/valida el backend del stack dev.
5. **Valida que arranca:** levanta o recarga el stack compartido; comprueba que importa todo sin
   errores y que el frontend buildea. Si hay CI, mira que pase.
6. Commitea el cableado con `chore(integracion): …` o `feat(<unidad>): cableado de …`.
7. Resume: qué ramas mergeaste, qué cableaste, qué migraciones aplicaste, qué quedó pendiente.

$ARGUMENTS
