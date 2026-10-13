#!/usr/bin/env bash
# RESET: devuelve el escenario a dia 0 para poder repetirlo. Al estilo GitOps:
#   - main <- commit "vuelta a dia 0" que restaura intent/<nodo>.yml desde el tag day0 (sin reescribir
#     historia ni force-push: compatible con main protegida). Ese push dispara `deploy`, que con --prune
#     desmonta servicio y overlay del nodo, y `promote` no propone nada.
#   - borra las ramas de todas las etapas (local y remoto), existan o no.
#   - ademas lleva leaf3 a dia 0 por gNMI, por si el runner no esta disponible.
# Uso: make reset
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

c_hdr "Repo GitOps -> dia 0 (commit en main)"
cd "$REPO_DIR"
git switch -q main
git fetch -q origin
git reset -q --hard origin/main                      # main local = main remoto (main nunca se edita en local)
for b in $(stage_branches); do
  git branch -D "$b" >/dev/null 2>&1 || true
  git push -q origin --delete "$b" >/dev/null 2>&1 || true
done
c_ok "ramas de las etapas eliminadas (local y remoto, si existian)."

if git rev-parse -q --verify "refs/tags/${BASE_TAG}" >/dev/null; then
  git show "${BASE_TAG}:intent/${NODE}.yml" > "intent/${NODE}.yml"
elif [[ -f "$KIT_DIR/gitops-repo/intent/${NODE}.yml" ]]; then
  cp "$KIT_DIR/gitops-repo/intent/${NODE}.yml" "intent/${NODE}.yml"
else
  c_warn "ni tag ${BASE_TAG} ni intencion base en el kit: no puedo restaurar intent/${NODE}.yml"; exit 1
fi
if git diff --quiet -- "intent/${NODE}.yml"; then
  c_ok "main ya esta en dia 0: nada que confirmar."
else
  git add "intent/${NODE}.yml"
  git -c user.name=netops -c user.email=netops@localhost commit -q -m "${NODE}: vuelta a dia 0 (reset del escenario)"
  git push -q origin main
  c_ok "commit 'vuelta a dia 0' publicado: deploy desmontara overlay y servicio con --prune."
fi

c_hdr "leaf3 -> dia 0 via gNMI (por si el runner no esta)"
node_day0
sleep 2
node_show | sed -n '/Estado actual/,$p'
c_ok "Listo para repetir: make prep"
