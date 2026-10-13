#!/usr/bin/env bash
# Trafico iperf3 entre clientes, RESILIENTE. El traffic.sh del lab lanza un iperf3 de un solo disparo:
# si el destino no es alcanzable en ese momento (p.ej. leaf3 en dia 0), el cliente falla y muere.
# Aqui cada cliente corre en un lazo que reintenta cada 3 s, de modo que el trafico aparece solo
# en cuanto existe el servicio (y vuelve solo tras un reset). Mismos parametros que el lab
# (8 flujos TCP x 200 kbit/s = 1,6 Mbit/s por cliente, IPv6, servidor en client1).
# Uso: bash demo/traffic.sh start|stop|status
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

declare -A IPERF=(
  [client2]='iperf3 -c 2002::172:17:0:1 -t 10000 -i 1 -p 5201 -B 2002::172:17:0:2 -P 8 -b 200K -M 1480 -l 1480'
  [client3]='iperf3 -c 2002::172:17:0:1 -t 10000 -i 1 -p 5202 -B 2002::172:17:0:3 -P 8 -b 200K -M 1480 -l 1480'
)

stop_client() {
  dk exec "$1" pkill -f "iperf-loop" >/dev/null 2>&1 || true
  dk exec "$1" pkill iperf3 >/dev/null 2>&1 || true
}

start_client() {  # lazo con nombre reconocible (iperf-loop) para poder pararlo
  stop_client "$1"
  dk exec -d "$1" bash -c "exec -a iperf-loop bash -c 'while true; do ${IPERF[$1]} >/dev/null 2>&1; sleep 3; done'"
}

case "${1:-status}" in
  start)
    for c in client2 client3; do start_client "$c" && c_ok "  $c: lazo iperf3 en marcha (reintenta hasta tener camino)"; done ;;
  stop)
    for c in client2 client3; do stop_client "$c"; done; c_ok "  trafico detenido" ;;
  status)
    for c in client2 client3; do
      if dk exec "$c" pgrep -f iperf-loop >/dev/null 2>&1; then
        dk exec "$c" pgrep -x iperf3 >/dev/null 2>&1 && c_ok "  $c: enviando trafico" || c_warn "  $c: lazo activo, sin camino todavia (reintentando)"
      else
        c_warn "  $c: sin lazo de trafico (make traffic-start)"
      fi
    done ;;
  *) echo "uso: $0 start|stop|status"; exit 1 ;;
esac
