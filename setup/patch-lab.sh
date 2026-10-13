#!/usr/bin/env bash
# Clona el srl-telemetry-lab, aplica los parches del kit y pre-descarga las imagenes que declara.
# Uso: bash setup/patch-lab.sh   (LAB_DIR por defecto ~/srl-telemetry-lab)
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_DIR="${LAB_DIR:-$HOME/srl-telemetry-lab}"
dk() { docker "$@" 2>/dev/null || sudo docker "$@"; }

if [[ ! -d "$LAB_DIR/.git" ]]; then
  echo ">> Clonando srl-telemetry-lab en $LAB_DIR"
  git clone -q https://github.com/srl-labs/srl-telemetry-lab.git "$LAB_DIR"
fi

cd "$LAB_DIR"
echo ">> Guardando copia de los originales en .orig"
for f in configs/gnmic/gnmic-config.yml configs/prometheus/prometheus.yml configs/grafana/datasource.yml; do
  [[ -f "$f.orig" ]] || cp "$f" "$f.orig"
done

echo ">> Aplicando parches (modo 0644: los contenedores corren con otro uid y deben poder leerlos)"
install -m 0644 "$KIT_DIR/lab-patches/gnmic-config.yml"  configs/gnmic/gnmic-config.yml
install -m 0644 "$KIT_DIR/lab-patches/prometheus.yml"    configs/prometheus/prometheus.yml
install -m 0644 "$KIT_DIR/lab-patches/datasource.yml"    configs/grafana/datasource.yml
install -m 0644 "$KIT_DIR/lab-patches/netops-demo.json"  configs/grafana/dashboards/netops-demo.json

echo ">> Resumen de cambios respecto al upstream:"
git --no-pager diff --stat

echo ">> Pre-descarga de las imagenes declaradas en st.clab.yml (asi el deploy no necesita internet)"
grep -E '^\s*image:' st.clab.yml | awk '{print $2}' | sort -u | while read -r img; do
  echo "   - $img"; dk pull -q "$img" >/dev/null
done

PROXY="${https_proxy:-${HTTPS_PROXY:-${http_proxy:-${HTTP_PROXY:-}}}}"
if [[ -n "$PROXY" ]] && ! grep -q 'HTTPS_PROXY' st.clab.yml; then
  echo
  echo ">> AVISO: hay proxy en el entorno y st.clab.yml no lo declara para el nodo grafana."
  echo "   Añade bajo 'grafana: -> env:' (8 espacios de indentacion):"
  echo "        HTTP_PROXY: $PROXY"
  echo "        HTTPS_PROXY: $PROXY"
  echo "        NO_PROXY: localhost,127.0.0.1,prometheus,loki,172.80.80.0/24"
fi
echo
echo ">> OK. Despliega con:  make lab-up"
