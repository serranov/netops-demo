#!/usr/bin/env bash
# Tunel SSH desde TU PORTATIL hacia la VM (que vive detras del NAT del host Proxmox).
# Uso:  bash demo/tunnel.sh root@<IP_SERVIDOR> <IP_VM>
# Luego en el navegador: http://localhost:3000 (Grafana) · :9090 (Prometheus) · :3030 (Gitea)
set -euo pipefail
HOST="${1:?uso: tunnel.sh usuario@host_proxmox ip_vm}"
VM="${2:?uso: tunnel.sh usuario@host_proxmox ip_vm}"
echo ">> Tunel a ${VM} via ${HOST}: localhost:3000 / :9090 / :3030  (Ctrl+C para cerrar)"
exec ssh -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
  -L "3000:${VM}:3000" -L "9090:${VM}:9090" -L "3030:${VM}:3030" "${HOST}"
