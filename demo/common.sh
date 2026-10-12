# Variables y funciones compartidas por los scripts del escenario. Ajusta rutas si las cambias.
LAB_DIR="${LAB_DIR:-$HOME/srl-telemetry-lab}"          # clon del srl-telemetry-lab (parcheado)
REPO_DIR="${REPO_DIR:-$HOME/netops-gitops}"           # clon local del repo GitOps (remoto: Gitea)
KIT_DIR="${KIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
NODE="${NODE:-leaf3}"
BASE_TAG="${BASE_TAG:-day0}"                           # tag del estado base (dia 0) en el repo GitOps

LEAF3="${LEAF3:-172.80.80.13}"
SRL_USER="${SRL_USER:-admin}"
SRL_PASSWORD="${SRL_PASSWORD:-NokiaSrl1!}"
GNMIC=(gnmic -a "$LEAF3" -u "$SRL_USER" -p "$SRL_PASSWORD" --skip-verify -e json_ietf --timeout 20s)
BGP="/network-instance[name=default]/protocols/bgp"

c_ok()   { printf '\033[1;32m%s\033[0m\n' "$*"; }
c_warn() { printf '\033[1;33m%s\033[0m\n' "$*"; }
c_hdr()  { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }

# docker con respaldo a sudo (por si el grupo 'docker' aun no es efectivo en esta sesion)
dk() { docker "$@" 2>/dev/null || sudo docker "$@"; }

# propietario y nombre del repo GitOps, a partir del remote (para construir URLs de Gitea)
repo_owner() { git -C "$REPO_DIR" remote get-url origin 2>/dev/null | sed -E 's#.*/([^/]+)/[^/]+?(\.git)?$#\1#'; }
repo_name()  { git -C "$REPO_DIR" remote get-url origin 2>/dev/null | sed -E 's#.*/([^/]+?)(\.git)?$#\1#'; }

# Estado de leaf3 segun netops.py (grupos, vecinos, servicios)
node_show() { python3 "$REPO_DIR/scripts/netops.py" --intent "$REPO_DIR/intent/$NODE.yml" --show; }

# Ramas de todas las etapas del rollout (para borrarlas en el reset)
stage_branches() { python3 -c 'import sys,yaml; [print(s["branch"]) for s in yaml.safe_load(open(sys.argv[1]))["stages"]]' "$REPO_DIR/stages/$NODE.yml"; }

# Lleva leaf3 al DIA 0 por gNMI en UNA transaccion: sin servicio vrf-1 ni overlay iBGP (el underlay se mantiene).
# Es lo mismo que hace `deploy --prune` con la intencion base; se hace tambien por gNMI por si el runner no esta.
node_day0() {
  "${GNMIC[@]}" set \
    --delete "/network-instance[name=vrf-1]" \
    --delete "/tunnel-interface[name=vxlan1]/vxlan-interface[index=1]" \
    --delete "/interface[name=ethernet-1/1]/subinterface[index=0]" \
    --delete "${BGP}/neighbor[peer-address=10.0.2.1]" \
    --delete "${BGP}/neighbor[peer-address=10.0.2.2]" \
    --delete "${BGP}/group[group-name=iBGP-overlay]" >/dev/null 2>&1 \
  || c_warn "  (parte del dia 0 ya estaba aplicado o el nodo no respondio; comprueba con make status)"
}
