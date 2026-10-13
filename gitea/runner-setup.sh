#!/usr/bin/env bash
# Instala y registra act_runner en MODO HOST (los jobs corren en el shell de la VM,
# donde ya estan gnmic, python3 y acceso directo a la red de gestion del lab).
# Uso:  bash runner-setup.sh            (usa localhost:3030)
set -euo pipefail

ACT_RUNNER_VERSION="${ACT_RUNNER_VERSION:-0.2.11}"   # comprueba la ultima en https://gitea.com/gitea/act_runner/releases
GITEA_URL="${GITEA_URL:-http://localhost:3030}"
RUNNER_DIR="${RUNNER_DIR:-$HOME/act_runner}"
RUNNER_NAME="${RUNNER_NAME:-lab-runner}"
RUNNER_LABELS="${RUNNER_LABELS:-lab:host}"           # 'lab' = runs-on del workflow; ':host' = modo host

mkdir -p "$RUNNER_DIR" && cd "$RUNNER_DIR"

if [[ ! -x ./act_runner ]]; then
  echo ">> Descargando act_runner ${ACT_RUNNER_VERSION}..."
  curl -fsSL -o act_runner \
    "https://dl.gitea.com/act_runner/${ACT_RUNNER_VERSION}/act_runner-${ACT_RUNNER_VERSION}-linux-amd64"
  chmod +x act_runner
fi

if [[ -f .runner ]]; then
  echo ">> Hay un registro previo (.runner): se elimina para registrar contra la instancia actual de Gitea"
  sudo systemctl stop act_runner 2>/dev/null || true
  rm -f .runner
fi

echo ">> Generando token de registro en Gitea..."
TOKEN="$(docker exec -u git gitea gitea actions generate-runner-token | tr -d '\r\n')"

echo ">> Registrando runner '${RUNNER_NAME}' con labels '${RUNNER_LABELS}' en ${GITEA_URL}..."
./act_runner register --no-interactive \
  --instance "${GITEA_URL}" \
  --token "${TOKEN}" \
  --name "${RUNNER_NAME}" \
  --labels "${RUNNER_LABELS}"

# Servicio systemd para que sobreviva a reinicios de la VM
SERVICE_FILE=/etc/systemd/system/act_runner.service
echo ">> Creando servicio systemd (${SERVICE_FILE})..."
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=Gitea act_runner (host mode) - NetOps demo
After=network-online.target docker.service
Wants=network-online.target

[Service]
User=$(id -un)
WorkingDirectory=${RUNNER_DIR}
ExecStart=${RUNNER_DIR}/act_runner daemon
Restart=always
RestartSec=3
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable act_runner >/dev/null 2>&1
sudo systemctl restart act_runner          # restart, no 'enable --now': si ya corria con otro registro, debe recargarlo
sleep 3
sudo systemctl --no-pager status act_runner | head -n 8
echo
echo ">> Listo. Comprueba en Gitea: Site Administration -> Actions -> Runners (debe aparecer '${RUNNER_NAME}' Idle)."
