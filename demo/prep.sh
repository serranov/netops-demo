#!/usr/bin/env bash
# PREPARA el escenario "onboarding de leaf3":
#   1. Lleva leaf3 al dia 0 (solo underlay): elimina servicio vrf-1 y overlay iBGP por gNMI.
#   2. Arranca trafico iperf3 entre clientes en lazo resiliente (client3 reintenta hasta que exista el servicio).
#   3. Crea en el repo GitOps la rama de la etapa 1 (overlay) con promote.py (commit local, sin push).
#
# Uso: bash demo/prep.sh      -> despues: make diff && make push, y abre el PR en Gitea
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
sudo -v 2>/dev/null || true     # pide la credencial de sudo ahora, no a mitad del script

c_hdr "1/3 leaf3 -> dia 0 (sin overlay ni servicio) via gNMI"
node_day0
sleep 2
node_show | sed -n '/Estado actual/,$p'
c_ok "leaf3 solo con underlay: client3 sin conectividad hasta completar el rollout."

c_hdr "2/3 Trafico iperf3 entre clientes (lazo resiliente)"
bash "$KIT_DIR/demo/traffic.sh" start
c_ok "client3 reintenta cada 3 s: leaf3 e1-1 pasara de 0 a ~1,6 Mb/s solo, en cuanto exista el servicio."

c_hdr "3/3 Repo GitOps: rama de la etapa 'overlay'"
cd "$REPO_DIR"
git switch -q main
git pull -q --ff-only origin main || true
python3 scripts/promote.py --node "$NODE" --stage overlay
c_ok "siguiente: make diff && make push  (abre el PR ya documentado; tras el merge, el PR del dia 2 se abre solo)"

OWNER="$(repo_owner)"; NAME="$(repo_name)"
c_hdr "URLs (con el tunel SSH abierto, o sustituye localhost por la IP de la VM)"
cat <<EOF
  Grafana lab      : http://localhost:3000
  Grafana NetOps   : http://localhost:3000/d/netops-demo
  Gitea - PRs      : http://localhost:3030/${OWNER:-<usuario>}/${NAME:-netops-gitops}/pulls
  Gitea - Actions  : http://localhost:3030/${OWNER:-<usuario>}/${NAME:-netops-gitops}/actions
  Repo lab         : $LAB_DIR
  Repo GitOps      : $REPO_DIR   (rama $(git branch --show-current))
EOF
