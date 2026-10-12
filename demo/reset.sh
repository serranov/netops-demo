#!/usr/bin/env bash
# RESET: devuelve el repo GitOps y el nodo al dia 0 para poder repetir el escenario.
#   - main <- tag day0 (force-push), borra las ramas de todas las etapas (local y remoto).
#     El job `deploy` que dispara ese push reconcilia el nodo (con --prune elimina overlay y servicio).
#   - Ademas lleva leaf3 al dia 0 por gNMI, por si el runner no esta disponible.
# Si `main` esta protegida en Gitea, el force-push requiere que tu usuario este en la lista blanca
# de push forzado (o desactivar la proteccion temporalmente).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

c_hdr "Repo GitOps -> dia 0 (${BASE_TAG})"
cd "$REPO_DIR"
git switch -q main
git fetch -q origin
git reset -q --hard "$BASE_TAG"
if git push -q --force origin main; then
  c_ok "main = ${BASE_TAG}"
else
  c_warn "no se pudo hacer force-push a main (¿rama protegida?). Añade tu usuario a la lista blanca de push forzado o desprotege main temporalmente."
fi
for b in $(stage_branches); do
  git branch -D "$b" >/dev/null 2>&1 || true
  git push -q origin --delete "$b" >/dev/null 2>&1 || true
done
c_ok "ramas de las etapas eliminadas (local y remoto)."

c_hdr "leaf3 -> dia 0 via gNMI"
node_day0
sleep 2
node_show | sed -n '/Estado actual/,$p'
c_ok "Listo para repetir: make prep"
