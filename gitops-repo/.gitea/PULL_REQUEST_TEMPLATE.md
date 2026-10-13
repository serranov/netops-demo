<!--
Los PRs del flujo (make push, job promote) se crean ya documentados por scripts/promote.py.
Esta plantilla solo aplica a PRs creados a mano desde la web de Gitea.
-->
## Qué cambia

## Plan esperado

Pega el bloque "-- Prerrequisitos" y "-- Plan" del job `validate` (o ejecuta `python3 scripts/promote.py --node leaf3 --pr --print` en la rama).

## Checklist

- [ ] Prerrequisitos de la etapa comprobados en el nodo
- [ ] Impacto conocido (altas/bajas, nodos afectados)
- [ ] `validate` en verde en el último commit
- [ ] Tras el merge: `deploy` en verde, anotación en Grafana y paneles de la etapa en verde
- [x] Rollback disponible: Revert del PR y merge
