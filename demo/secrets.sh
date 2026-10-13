#!/usr/bin/env bash
# Crea/actualiza los secrets del repositorio GitOps en Gitea por API, a partir de gitea/.env:
#   GITEA_PAT     <- GITEA_PAT del .env (token con escritura; el pipeline lo usa para push de ramas y PRs)
#   SRL_PASSWORD  <- SRL_PASSWORD del .env si existe, si no NokiaSrl1! (password de admin en SR Linux)
# Uso: make secrets      (idempotente)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ENV_FILE="$KIT_DIR/gitea/.env"
[[ -f "$ENV_FILE" ]] || { c_warn "no existe $ENV_FILE (cp gitea/.env.example gitea/.env y rellena GITEA_PAT)"; exit 1; }
set -a; source "$ENV_FILE"; set +a
[[ -n "${GITEA_PAT:-}" ]] || { c_warn "GITEA_PAT vacio en $ENV_FILE"; exit 1; }

OWNER="$(repo_owner)"; NAME="$(repo_name)"
URL="${GITEA_URL:-http://localhost:3030}"
[[ -n "$OWNER" && -n "$NAME" ]] || { c_warn "no puedo deducir owner/repo del remote de $REPO_DIR"; exit 1; }

put_secret() {  # put_secret NOMBRE VALOR
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' -X PUT \
    -H "Authorization: token ${GITEA_PAT}" -H "Content-Type: application/json" \
    "${URL}/api/v1/repos/${OWNER}/${NAME}/actions/secrets/$1" -d "$(python3 -c 'import json,sys; print(json.dumps({"data": sys.argv[1]}))' "$2")")"
  case "$code" in
    201) c_ok "  $1: creado";;
    204) c_ok "  $1: actualizado";;
    *)   c_warn "  $1: HTTP $code (¿token sin permiso de escritura? ¿repo ${OWNER}/${NAME} existe?)"; return 1;;
  esac
}

c_hdr "Secrets de Actions en ${URL}/${OWNER}/${NAME}"
put_secret GITEA_PAT "$GITEA_PAT"
put_secret SRL_PASSWORD "${SRL_PASSWORD:-NokiaSrl1!}"
echo
echo "  comprobar: ${URL}/${OWNER}/${NAME}/settings/actions/secrets"
