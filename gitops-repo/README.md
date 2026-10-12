# netops-gitops

Fuente de verdad de lo que GitOps gestiona en los leaves de un laboratorio Containerlab + Nokia SR Linux. Lo que no está declarado aquí (y es propiedad de GitOps) no está en la red.

```
intent/leaf3.yml                   <- INTENCIÓN: estado deseado del nodo (grupos BGP de overlay y servicios)
stages/leaf3.yml                   <- PLAN por etapas: fragmentos que se van fusionando en la intención, uno por PR
scripts/netops.py                  <- reconcilia intención vs. nodo por gNMI: prerrequisitos, plan, apply, verificación
scripts/promote.py                 <- crea la rama de la siguiente etapa (y abre el PR si se le pide)
.gitea/workflows/netops.yml        <- rama ≠ main: validate · main: deploy + promote
.gitea/PULL_REQUEST_TEMPLATE.md
```

## Ciclo de vida de un leaf

| Día | Qué | Quién | Verificación |
|---|---|---|---|
| 0 | Underlay eBGP a los spines, system0 | bootstrap / startup-config (fuera de GitOps) | prerrequisito de la etapa 1 |
| 1 | Overlay: grupo `iBGP-overlay` + sesiones EVPN a los RR | PR etapa `overlay` | sesiones `established` |
| 2 | Servicio: `vrf-1` (mac-vrf, VNI 1, EVI 1) + acceso `ethernet-1/1.0` | PR etapa `service` (propuesto automáticamente) | `vrf-1` oper-state `up`, tráfico |

## Flujo

1. `python3 scripts/promote.py --node leaf3 --stage overlay` crea la rama de la etapa 1 → `git push` → **Pull Request**.
2. **validate** comprueba el prerrequisito (underlay establecido) y publica el **plan** sin tocar nada.
3. **Merge** (borra la rama) → **deploy** aplica en una transacción gNMI, espera a que las sesiones establezcan y anota el despliegue en Grafana.
4. **promote** detecta que la etapa 2 tiene `auto_promote: true`, crea su rama y **abre el PR** con el fragmento y el checklist.
5. **validate** del PR 2 exige que el overlay esté `established` en el nodo (gate). **Merge** → **deploy** crea el servicio y verifica `oper-state up`.
6. Deshacer: **Revert** del PR y merge; `deploy --prune` elimina lo que ya no está declarado (grupo, vecinos o servicio con sus subinterfaces).

## Uso manual

```bash
python3 scripts/netops.py  --intent intent/leaf3.yml --show                # estado del nodo
python3 scripts/netops.py  --intent intent/leaf3.yml --dry-run --prune     # prerrequisitos + plan
python3 scripts/netops.py  --intent intent/leaf3.yml --apply   --prune     # aplicar y verificar
python3 scripts/promote.py --node leaf3 --list                             # estado del rollout
```

`ownership` en la intención fija qué grupos y servicios posee GitOps: solo esos se crean, aseguran o eliminan. El underlay (`prerequisites.underlay_group`) nunca se toca.
