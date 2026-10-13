#!/usr/bin/env bash
# Pruebas de netops.py y promote.py contra un gnmic SIMULADO (sin laboratorio). Uso: make test
set -uo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$KIT/tests/mock-gnmic:$PATH"
export MOCK_STATE="$(mktemp)"
WORK="$(mktemp -d)"
pass=0; fail=0

# repo GitOps temporal (copia del kit) con git, para probar promote.py y los fragmentos reales
cp -r "$KIT/gitops-repo" "$WORK/repo"
git -C "$WORK/repo" init -q -b main && git -C "$WORK/repo" add -A \
  && git -C "$WORK/repo" -c user.name=t -c user.email=t@t commit -q -m base
REPO="$WORK/repo"
netops()  { python3 "$REPO/scripts/netops.py" "$@"; }
promote() { python3 "$REPO/scripts/promote.py" "$@"; }
intent_of_stage() {  # genera en $WORK la intencion con las etapas hasta <stage> fusionadas
  python3 - "$REPO" "$1" "$WORK/$1.yml" <<'EOF'
import sys, yaml
sys.path.insert(0, sys.argv[1] + "/scripts")
import promote
repo, upto, out = sys.argv[1:4]
stages = sorted(yaml.safe_load(open(f"{repo}/stages/leaf3.yml"))["stages"], key=lambda s: s["order"])
intent = yaml.safe_load(open(f"{repo}/intent/leaf3.yml"))
for s in stages:
    intent = promote.deep_merge(intent, s["intent"])
    if s["name"] == upto: break
yaml.safe_dump(intent, open(out, "w"), sort_keys=False)
EOF
  echo "$WORK/$1.yml"
}
BASE="$REPO/intent/leaf3.yml"
OVERLAY="$(intent_of_stage overlay)"
SERVICE="$(intent_of_stage service)"
reset_mock() { rm -f "$MOCK_STATE"; }

t() {  # t "<nombre>" "<patron grep -E>" [--rc N] <comando...>
  local name="$1" pattern="$2" want_rc="" out rc; shift 2
  if [[ "${1:-}" == "--rc" ]]; then want_rc="$2"; shift 2; fi
  out="$("$@" 2>&1)"; rc=$?
  if grep -qEe "$pattern" <<< "$out" && { [[ -z "$want_rc" ]] || [[ "$rc" == "$want_rc" ]]; }; then
    echo "  PASS  $name"; pass=$((pass+1))
  else
    echo "  FAIL  $name  (esperaba /$pattern/${want_rc:+ rc=$want_rc, obtuvo rc=$rc})"; sed 's/^/        | /' <<< "$out"; fail=$((fail+1))
  fi
}

echo "== Dia 0: la intencion base desmonta overlay y servicio del lab (el repo manda)"
reset_mock
t "show: lab completo (overlay + vrf-1 gestionados)"          "servicio vrf-1 +mac-vrf +oper up +\[gestionado\]"     netops --intent "$BASE" --show
t "dry-run base sin prune: avisa, no elimina"                 "aviso: servicio vrf-1 poseido"                        netops --intent "$BASE" --dry-run
t "dry-run base --prune: plan elimina grupo, vecinos y vrf-1" "- ELIMINAR servicio vrf-1 .*ethernet-1/1.0, vxlan1.1" netops --intent "$BASE" --dry-run --prune
t "apply base --prune: DEPLOY OK"                             "DEPLOY OK"                                            netops --intent "$BASE" --apply --prune --wait 3
t "dia 0: underlay intacto, sin overlay ni servicio"          "servicios +: \(ninguno\)"                             netops --intent "$BASE" --show

echo "== Dia 1: etapa overlay"
t "gate dia 2 sin overlay: BLOQUEADO (rc=1)"                  "dia 1: overlay no establecido" --rc 1                 netops --intent "$SERVICE" --dry-run --prune
t "dry-run overlay: prerrequisito dia 0 OK y plan añade"      "\+ AÑADIR +vecino 10\.0\.2\.2 \(grupo iBGP-overlay\)" netops --intent "$OVERLAY" --dry-run --prune
t "apply overlay: sesiones established, DEPLOY OK"            "OK 10\.0\.2\.2 +established"                          netops --intent "$OVERLAY" --apply --prune --wait 3
t "apply overlay de nuevo: idempotente"                       "sin cambios"                                          netops --intent "$OVERLAY" --dry-run --prune

echo "== Dia 2: etapa service"
t "dry-run service: gate dia 1 OK y plan añade vrf-1"         "\+ AÑADIR +servicio vrf-1 \(mac-vrf, VNI 1, EVI 1"    netops --intent "$SERVICE" --dry-run --prune
t "apply service: vrf-1 up, DEPLOY OK"                        "OK vrf-1 +oper-state up"                              netops --intent "$SERVICE" --apply --prune --wait 3

echo "== Rollback por etapas (git revert simulado)"
t "revert service: elimina vrf-1 con subinterfaz y vxlan"     "OK vrf-1 +eliminado"                                  netops --intent "$OVERLAY" --apply --prune --wait 3
t "revert overlay: elimina vecinos y grupo"                   "OK 10\.0\.2\.1 +eliminado"                            netops --intent "$BASE" --apply --prune --wait 3
t "underlay nunca se toca"                                    "192\.168\.31\.1 +established +grupo eBGP +\[underlay" netops --intent "$BASE" --show

echo "== Respuesta hoja a hoja (otra forma de SR Linux)"
reset_mock
MOCK_SHAPE=leaf t "show con respuesta hoja a hoja"            "vecino 10\.0\.2\.1 +established"                      netops --intent "$BASE" --show

echo "== promote.py (rollout por etapas)"
t "list: ambas etapas pendientes en base"                     "\[ \] +10 +overlay"                                   promote --node leaf3 --list
t "list: service pendiente y automatica"                      "\[ \] +20 +service +auto=true"                        promote --node leaf3 --list
t "stage overlay: crea la rama con el fragmento"              "rama onboarding/leaf3-10-overlay creada"              promote --node leaf3 --stage overlay
t "la rama contiene el grupo iBGP-overlay"                    "name: iBGP-overlay"                                   git -C "$REPO" show onboarding/leaf3-10-overlay:intent/leaf3.yml
t "next --auto en base: overlay no es automatica"             "no es automatica"                                     promote --node leaf3 --next --auto
git -C "$REPO" switch -q main && git -C "$REPO" merge -q --ff-only onboarding/leaf3-10-overlay
t "list tras merge overlay: overlay aplicada"                 "\[x\] +10 +overlay"                                   promote --node leaf3 --list
t "next --auto tras overlay: propone service"                 "rama onboarding/leaf3-20-service-vrf1 creada"         promote --node leaf3 --next --auto
git -C "$REPO" switch -q main && git -C "$REPO" merge -q --ff-only onboarding/leaf3-20-service-vrf1
t "rollout completo"                                          "rollout completo"                                     promote --node leaf3 --next

echo "== promote.py --pr --print (cuerpo del PR generado, con plan real del mock)"
git -C "$REPO" switch -q main && git -C "$REPO" reset -q --hard "$(git -C "$REPO" rev-list --max-parents=0 HEAD)"
git -C "$REPO" branch -D onboarding/leaf3-10-overlay onboarding/leaf3-20-service-vrf1 >/dev/null 2>&1 || true
reset_mock; MOCK_START=day0 promote --node leaf3 --stage overlay >/dev/null
MOCK_START=day0 t "cuerpo: seccion Que cambia desde la etapa"   "Etapa.*overlay.*order 10"                         promote --node leaf3 --pr --print
MOCK_START=day0 t "cuerpo: plan real con las altas del overlay" "\+ AÑADIR +vecino 10\.0\.2\.2"                    promote --node leaf3 --pr --print
MOCK_START=day0 t "cuerpo: checklist con impacto calculado"     "\[x\] Impacto: 3 alta\(s\), 0 baja\(s\)"         promote --node leaf3 --pr --print
t "pr sin GITEA_PAT: error claro (rc=1)"                        "falta GITEA_PAT" --rc 1                            env -u GITEA_PAT python3 "$REPO/scripts/promote.py" --node leaf3 --pr

echo "== validacion estatica"
t "py_compile"  "^$" python3 -m py_compile "$REPO/scripts/netops.py" "$REPO/scripts/promote.py"
t "YAML del kit" "YAML OK" python3 -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]; print('YAML OK')" \
    "$BASE" "$REPO/stages/leaf3.yml" "$REPO/.gitea/workflows/netops.yml" "$KIT/lab-patches/gnmic-config.yml" \
    "$KIT/lab-patches/prometheus.yml" "$KIT/lab-patches/datasource.yml" "$KIT/gitea/docker-compose.yml"
t "JSON del dashboard" "JSON OK" python3 -c "import json,sys; json.load(open(sys.argv[1])); print('JSON OK')" "$KIT/lab-patches/netops-demo.json"
t "bash -n scripts" "^$" bash -c 'for f in "$@"; do bash -n "$f" || exit 1; done' _ "$KIT"/setup/*.sh "$KIT"/demo/*.sh "$KIT"/gitea/*.sh "$KIT"/tests/run.sh

rm -rf "$MOCK_STATE" "$WORK"
echo; echo "== $pass OK, $fail fallos"
[[ $fail -eq 0 ]]
