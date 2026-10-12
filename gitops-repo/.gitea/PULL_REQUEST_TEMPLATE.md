## Qué cambia

<!-- Etapa del rollout (overlay / service / otra), nodo afectado y motivo (ticket, ventana) -->

## Plan esperado

<!-- Pega el bloque "-- Prerrequisitos" y "-- Plan" del job `validate` -->

## Checklist

- [ ] `validate` en verde: prerrequisitos OK y plan exactamente el esperado (sin eliminaciones inesperadas)
- [ ] Dependencias: la etapa anterior está desplegada y verificada en el nodo
- [ ] Impacto conocido: ¿afecta a tráfico en producción? ¿hay ventana?
- [ ] Observación tras el merge: anotación de deploy en Grafana y paneles de la etapa en verde
- [ ] Rollback: Revert del PR y merge (el pipeline elimina lo que deja de estar declarado)
