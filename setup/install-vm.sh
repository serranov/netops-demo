#!/usr/bin/env bash
# Instala en la VM (Ubuntu 22.04/24.04) las herramientas base. Ejecutar UNA vez con internet.
# Uso: bash setup/install-vm.sh
#
# Si la VM sale a internet por un proxy, exporta antes http_proxy/https_proxy/no_proxy
# (ver README, seccion "Proxy"): el script configura Docker con ellos automaticamente.
# Las imagenes del laboratorio se descargan en setup/patch-lab.sh (segun st.clab.yml).
set -euo pipefail

echo ">> Paquetes base"
sudo apt-get update -q
sudo apt-get install -y -q curl git jq python3 python3-yaml make unzip

echo ">> Docker + containerlab + gnmic (script oficial de containerlab, modo 'all')"
curl -sL https://containerlab.dev/setup | sudo -E bash -s "all"

echo ">> gnmic (asegurar instalacion si el paso anterior no lo dejo en PATH)"
command -v gnmic >/dev/null 2>&1 || bash -c "$(curl -sL https://get-gnmic.openconfig.net)"

# --- Proxy para el demonio Docker (solo si hay proxy en el entorno y no existe daemon.json) ---
PROXY="${https_proxy:-${HTTPS_PROXY:-${http_proxy:-${HTTP_PROXY:-}}}}"
if [[ -n "$PROXY" && ! -f /etc/docker/daemon.json ]]; then
  NOPROXY="${no_proxy:-${NO_PROXY:-localhost,127.0.0.1}}"
  echo ">> Proxy detectado ($PROXY): configurando /etc/docker/daemon.json"
  sudo mkdir -p /etc/docker
  printf '{ "proxies": { "http-proxy": "%s", "https-proxy": "%s", "no-proxy": "%s" } }\n' \
    "$PROXY" "$PROXY" "$NOPROXY" | sudo tee /etc/docker/daemon.json >/dev/null
  sudo systemctl restart docker
fi

echo ">> Docker sin sudo para el usuario actual (efectivo tras cerrar sesion y volver a entrar)"
sudo usermod -aG docker "$USER" || true

echo ">> Imagen de Gitea y prueba de descarga ('sudo docker' a proposito: el grupo aun no es efectivo)"
sudo docker pull -q gitea/gitea:1.24 >/dev/null && echo "   gitea/gitea:1.24 OK"

echo
echo ">> Versiones"
sudo docker --version; containerlab version | head -n 3 || true; gnmic version | head -n 2 || true
echo ">> OK. Cierra sesion y vuelve a entrar (grupo docker). Siguiente paso: make patch"
