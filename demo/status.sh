#!/usr/bin/env bash
# Chequeo de salud del entorno completo. Uso: make status
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
sudo -v 2>/dev/null || true

c_hdr "Lab containerlab"
( cd "$LAB_DIR" && sudo containerlab inspect -t st.clab.yml 2>/dev/null | grep -E 'leaf|spine|gnmic|prometheus|grafana|client' ) || c_warn "lab no desplegado? (make lab-up)"

c_hdr "leaf3 segun netops.py (gNMI)"
node_show 2>/dev/null | sed -n '/Estado actual/,$p' || c_warn "gnmic no responde: ¿leaf3 arriba? ¿password? ¿existe $REPO_DIR?"

c_hdr "Rollout (stages/$NODE.yml vs main)"
( cd "$REPO_DIR" && python3 scripts/promote.py --node "$NODE" --list ) 2>/dev/null || c_warn "no se pudo leer el rollout"

c_hdr "Prometheus: sesiones BGP de leaf3 (ultimo valor)"
curl -s 'http://localhost:9090/api/v1/query' --data-urlencode \
  'query=network_instance_protocols_bgp_neighbor_session_state{source="leaf3"}' \
  | python3 -c 'import sys,json; r=json.load(sys.stdin)["data"]["result"]; [print("  ", x["metric"].get("neighbor_peer_address"), "=", x["value"][1]) for x in r] or print("  (sin datos: revisa el parche gnmic-config.yml y http://localhost:9090/targets)")' 2>/dev/null \
  || c_warn "Prometheus no responde en :9090"

c_hdr "Grafana"
code="$(curl -s -o /dev/null -w '%{http_code}' localhost:3000/api/health || true)"
[[ "$code" == "200" ]] && c_ok "  Grafana: OK (:3000)" || c_warn "  Grafana no responde (HTTP ${code:-000}); con proxy, revisa las variables del nodo grafana en st.clab.yml"

c_hdr "Gitea y runner"
if dk ps --format '{{.Names}}' | grep -qx gitea; then c_ok "  gitea: $(dk ps --filter name='^gitea$' --format '{{.Status}}')"; else c_warn "  gitea no corre (make gitea-up)"; fi
systemctl is-active act_runner >/dev/null 2>&1 && c_ok "  act_runner: active" || c_warn "  act_runner: NO activo (sudo systemctl start act_runner)"
if [[ -f "$KIT_DIR/gitea/.env" ]]; then
  set -a; source "$KIT_DIR/gitea/.env"; set +a
  if [[ -n "${GITEA_PAT:-}" ]]; then
    names="$(curl -s -H "Authorization: token ${GITEA_PAT}" "http://localhost:3030/api/v1/repos/$(repo_owner)/$(repo_name)/actions/secrets" \
      | python3 -c 'import sys,json; d=json.load(sys.stdin); print(" ".join(sorted(x["name"] for x in d)) if isinstance(d,list) else "")' 2>/dev/null || true)"
    for sname in GITEA_PAT SRL_PASSWORD; do
      grep -qw "$sname" <<< "$names" && c_ok "  secret $sname: definido" || c_warn "  secret $sname: FALTA en el repo (make secrets)"
    done
  else
    c_warn "  GITEA_PAT vacio en gitea/.env: make push y make secrets no funcionaran"
  fi
fi

c_hdr "Repo GitOps"
( cd "$REPO_DIR" && echo "  rama: $(git branch --show-current)  |  ultimo commit: $(git log -1 --pretty=%s)" ) || c_warn "  no existe $REPO_DIR"
