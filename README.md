# NetOps GitOps Lab — Config-as-Code y telemetría para Nokia SR Linux

Laboratorio reproducible, 100 % open source, que cierra el bucle **Git → validación → despliegue → observación** sobre una fabric Clos EVPN-VXLAN de Nokia SR Linux desplegada con Containerlab:

- la **intención** de red vive en Git (grupos BGP de overlay y servicios del tenant, en YAML);
- un pipeline (Gitea Actions) la **valida** en cada Pull Request —con prerrequisitos leídos del nodo— y la **aplica** por gNMI al mergear;
- el despliegue se hace **por etapas** (un PR por etapa, la siguiente se propone sola al verificar la anterior);
- la **telemetría en streaming** (gNMIc → Prometheus → Grafana) muestra el efecto de cada etapa en segundos, con el despliegue anotado.

```
   Operador                       VM (Ubuntu) sobre Proxmox VE
   ────────                       ────────────────────────────────────────────────────────────────
   git push ───────────────────▶  Gitea (:3030) ──▶ act_runner (host) ──▶ netops.py ──gnmic set──▶ SR Linux (leaf3)
                                       ▲                 │ promote.py (abre el PR de la siguiente etapa)     │ overlay EVPN
                                       └─────────────────┘                                                  │ servicio vrf-1
   Navegador ◀─────────────────  Grafana (:3000) ◀── Prometheus ◀── gNMIc ◀────── gNMI subscribe ───────────┘
```

**Base:** [`srl-labs/srl-telemetry-lab`](https://github.com/srl-labs/srl-telemetry-lab) (2 spines + 3 leafs SR Linux con underlay eBGP, overlay iBGP EVPN y un servicio L2 `vrf-1` VNI 1 entre los clientes; gNMIc → Prometheus → Grafana; Alloy → Loki; tráfico iperf3) + 4 parches mínimos + una capa GitOps (Gitea + Actions + `netops.py` + `promote.py`).

**Escenario incluido — onboarding de un leaf (crecimiento de la fabric):** llega un rack de servidores (Proxmox) y hay que dar servicio a `leaf3`, que solo tiene el día 0 (underlay eBGP a los spines). GitOps lo lleva, en dos Pull Requests, al estado que el laboratorio define en su `startup-config` para ese leaf:

| Día | Etapa | Qué declara el PR | Prerrequisito que comprueba `validate` | Qué se observa |
|---|---|---|---|---|
| 0 | — | nada (bootstrap, fuera de GitOps) | — | 2 sesiones eBGP `established` |
| 1 | `overlay` | grupo `iBGP-overlay` (AS 100, EVPN) + sesiones a los route reflectors 10.0.2.1/10.0.2.2 | underlay establecido | 2 sesiones iBGP `established` |
| 2 | `service` | `vrf-1` (mac-vrf, VNI 1, EVI 1, RT 100:1) + `vxlan1.1` + acceso `ethernet-1/1.0` | overlay `established` | `vrf-1` UP, MACs aprendidas, tráfico de `client3` en e1-1 |

Revertir cualquiera de los PRs deshace esa etapa en el nodo (`--prune`). El underlay nunca se toca.

---

## Índice

1. [Estructura del repositorio](#1-estructura-del-repositorio)
2. [La VM en Proxmox VE](#2-la-vm-en-proxmox-ve)
3. [Salida a Internet por proxy](#3-salida-a-internet-por-proxy)
4. [Instalación](#4-instalación)
5. [Despliegue del laboratorio](#5-despliegue-del-laboratorio)
6. [Gitea y runner](#6-gitea-y-runner)
7. [Repositorio GitOps](#7-repositorio-gitops)
8. [Flujo de cambio: del PR a la red](#8-flujo-de-cambio-del-pr-a-la-red)
9. [Escenario de ejemplo](#9-escenario-de-ejemplo)
10. [Guía de desarrollo](#10-guía-de-desarrollo)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Estructura del repositorio

```
netops-demo/
├── README.md
├── Makefile                   ← atajos (make help)
├── setup/
│   ├── install-vm.sh          ← docker + containerlab + gnmic (detecta proxy y configura Docker)
│   └── patch-lab.sh           ← clona srl-telemetry-lab, aplica los parches y pre-descarga sus imágenes
├── lab-patches/               ← los 4 ficheros que se sustituyen/añaden en el lab
│   ├── gnmic-config.yml       ← + suscripción session-state por vecino BGP (2 s) y procesador 1/0
│   ├── prometheus.yml         ← scrape 2 s
│   ├── datasource.yml         ← uids explícitos de los datasources (los que usa el dashboard del lab)
│   └── netops-demo.json       ← dashboard "NetOps - Onboarding de leaf3" (día 0/1/2 + anotaciones de deploy)
├── gitea/
│   ├── docker-compose.yml     ← Gitea en :3030 (Actions habilitado)
│   ├── .env.example           ← VM_IP (lo que escribes en el navegador) y GITEA_PAT (para que make push abra el PR)
│   └── runner-setup.sh        ← act_runner en modo host, label 'lab', servicio systemd
├── gitops-repo/               ← contenido inicial del repositorio GitOps `netops-gitops`
│   ├── intent/leaf3.yml       ← la INTENCIÓN (estado base = día 0; ownership de lo que GitOps posee)
│   ├── stages/leaf3.yml       ← el PLAN por etapas (fragmentos overlay y service, auto_promote)
│   ├── scripts/netops.py      ← prerrequisitos + plan + apply atómico + verificación + prune
│   ├── scripts/promote.py     ← etapas: crea la rama siguiente y abre PRs ya documentados (descripción + plan real)
│   ├── .gitea/workflows/netops.yml       ← rama ≠ main: validate · main: deploy + promote
│   └── .gitea/PULL_REQUEST_TEMPLATE.md
├── demo/                      ← scripts del escenario
│   ├── prep.sh                ← leaf3 a día 0 + tráfico + rama de la etapa 'overlay'
│   ├── reset.sh               ← vuelve a día 0 (repo y nodo)
│   ├── status.sh              ← chequeo de salud (incluye secrets del pipeline)
│   ├── secrets.sh             ← crea los secrets del repo GitOps por API desde gitea/.env
│   └── tunnel.sh              ← (desde el portátil) túnel SSH a Grafana/Prometheus/Gitea
└── tests/
    ├── run.sh                 ← 31 pruebas sin laboratorio (make test)
    └── mock-gnmic/gnmic       ← mini SR Linux simulado con estado (grupos, vecinos, servicios)
```

---

## 2. La VM en Proxmox VE

Todo corre **dentro de una VM**, nunca sobre el host PVE: Docker y Containerlab manipulan iptables, veth y bridges justo encima de la red del hipervisor. La VM, además, permite snapshots con RAM (restauración completa del entorno en segundos).

| Recurso | Recomendado | Notas |
|---|---|---|
| SO | Ubuntu Server 24.04 LTS (mínima + OpenSSH) | 1 VM dedicada |
| vCPU | 8–12, tipo **`host`** | 5 nodos SR Linux + stack |
| RAM | **24–32 GB, ballooning desactivado** | cada SR Linux ~2 GB; 16 GB va justo |
| Disco | 60–100 GB SSD, virtio-scsi + discard | imágenes + TSDB + logs |
| Virt. anidada | No necesaria | SR Linux es contenedor Docker |
| Guest agent | Activado | resincroniza el reloj tras restaurar un snapshot |

### 2.1 Red de la VM: IP privada con NAT (zona SDN "Simple")

La VM no necesita una IP del rango externo. Una **zona SDN Simple con SNAT + DHCP** le da una IP privada y NAT de salida por el host, sin tocar `vmbr0`:

1. En el nodo PVE (una vez): `apt install dnsmasq && systemctl disable --now dnsmasq`.
2. *Datacenter → SDN → Zones → Add → Simple*: ID `lab`, IPAM `pve`, DHCP `dnsmasq`.
3. *VNets → Create*: `labnet`, zona `lab`.
4. *Subnets → Create*: `10.77.0.0/24`, gateway `10.77.0.1`, **SNAT ✔**, DHCP `10.77.0.100–10.77.0.200`.
5. *SDN → Apply*. NIC de la VM → bridge `labnet`. En la VM, IP fija por netplan (p. ej. `10.77.0.10/24`, gw `10.77.0.1`).

El rango se elige para no solapar con `172.17.0.0/16` (Docker) ni `172.80.80.0/24` (gestión del lab). Alternativa sin SDN: bridge `vmbr1` sin puertos + `MASQUERADE`, según la wiki de Proxmox ("Masquerading").

### 2.2 Acceso desde tu equipo

Con la VM en una red privada, lo más sencillo es un **túnel SSH** a través del host (no requiere cambios en el servidor):

```bash
bash demo/tunnel.sh root@<IP_HOST_PVE> 10.77.0.10        # desde tu equipo; déjalo abierto
```

Navegador: `http://localhost:3000` (Grafana) · `http://localhost:9090` (Prometheus) · `http://localhost:3030` (Gitea). Shell en la VM: `ssh -J root@<IP_HOST_PVE> ubuntu@10.77.0.10`.

Alternativas: reglas DNAT en el host para los puertos 3000/3030/9090 (Grafana va con acceso anónimo admin: solo en redes de confianza), o Tailscale dentro de la VM.

### 2.3 Snapshots recomendados

- `clean-installed` (sin RAM): tras `make patch`.
- `lab-ready` (**con RAM**): con todo desplegado y verde. Restaurar aquí evita volver a desplegar el lab (que necesita Internet, ver §5).

---

## 3. Salida a Internet por proxy

Si la VM solo sale a Internet a través de un proxy, cada herramienta lo lee de un sitio distinto. `apt` suele venir configurado por el instalador de Ubuntu; el resto no. Sustituye `http://proxy:3128` por el tuyo:

```bash
# shell, git, curl, gnmic, scripts (+ cerrar sesión y volver a entrar)
sudo tee -a /etc/environment <<'EOF'
http_proxy=http://proxy:3128
https_proxy=http://proxy:3128
no_proxy=localhost,127.0.0.1,10.77.0.0/24,172.80.80.0/24,172.17.0.0/16
HTTP_PROXY=http://proxy:3128
HTTPS_PROXY=http://proxy:3128
NO_PROXY=localhost,127.0.0.1,10.77.0.0/24,172.80.80.0/24,172.17.0.0/16
EOF
# que sudo herede el proxy (si no, 'sudo curl' se queda colgado)
echo 'Defaults env_keep += "http_proxy https_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY"' | sudo tee /etc/sudoers.d/proxy
sudo chmod 0440 /etc/sudoers.d/proxy && sudo visudo -cf /etc/sudoers.d/proxy
# apt (no lee el entorno)
echo 'Acquire::http::Proxy "http://proxy:3128"; Acquire::https::Proxy "http://proxy:3128";' | sudo tee /etc/apt/apt.conf.d/95proxy
```

Comprueba tras el relogin: `env | grep -i proxy` y `sudo env | grep -i proxy`. `make install` configura **Docker** (`/etc/docker/daemon.json`) automáticamente al detectar el proxy.

El contenedor **Grafana** descarga el plugin FlowPanel al arrancar y Containerlab no inyecta el proxy en los contenedores. Tras `make patch`, añade bajo `grafana: → env:` en `~/srl-telemetry-lab/st.clab.yml` (8 espacios de indentación):

```yaml
        HTTP_PROXY: http://proxy:3128
        HTTPS_PROXY: http://proxy:3128
        NO_PROXY: localhost,127.0.0.1,prometheus,loki,172.80.80.0/24
```

> **`no_proxy` es crítico.** gnmic y act_runner son Go y gRPC honra `HTTPS_PROXY`: sin `172.80.80.0/24` gnmic intentaría llegar a los nodos por el proxy; sin `localhost`, el `git push` a Gitea también. Sin `prometheus,loki` en el contenedor de Grafana, los paneles saldrían vacíos. El runner (servicio systemd) **no** lee `/etc/environment`, y así debe quedarse.

Dominios que necesita la instalación (si el proxy es de lista blanca): `github.com`, `objects.githubusercontent.com`, `raw.githubusercontent.com`, `containerlab.dev`, `netdevops.fury.site`, `get-gnmic.openconfig.net`, `download.docker.com`, `cli.github.com`, `dl.gitea.com`, `ghcr.io`, `pkg-containers.githubusercontent.com`, `quay.io`, `cdn*.quay.io`, `registry-1.docker.io`, `auth.docker.io`, `production.cloudflare.docker.com`, `grafana.com`, `storage.googleapis.com`.

---

## 4. Instalación

```bash
git clone https://github.com/serranov/netops-demo ~/netops-demo
cd ~/netops-demo
make install          # docker + containerlab + gnmic + python3-yaml; configura Docker si hay proxy
# cierra sesión y vuelve a entrar (grupo docker)
make patch            # clona ~/srl-telemetry-lab, aplica los 4 parches y pre-descarga sus imágenes
```

Comprueba: `docker --version && containerlab version && gnmic version && docker pull hello-world`.

---

## 5. Despliegue del laboratorio

> **Con proxy, antes de desplegar:** añade las variables al nodo `grafana` de `st.clab.yml` (§3). Si no, Grafana se queda colgado descargando el plugin y nunca escucha en :3000 aunque el contenedor figure `running`. Si ya desplegaste sin ellas: edita el YAML y `sudo containerlab deploy -t st.clab.yml --reconfigure --node-filter grafana`.

```bash
make lab-up           # = cd ~/srl-telemetry-lab && sudo containerlab deploy -t st.clab.yml --reconfigure
```

Tarda 2–3 minutos. Verifica:

```bash
sudo containerlab inspect -t ~/srl-telemetry-lab/st.clab.yml      # todos 'running'
ssh admin@leaf3                                                    # password: NokiaSrl1!
  show network-instance default protocols bgp neighbor             # 4 sesiones established (2 eBGP + 2 iBGP)
  quit
docker logs --since 5m gnmic 2>&1 | grep -c ERROR                  # 0 (los errores del primer minuto son el arranque)
```

Con el túnel abierto (§2.2):

- `http://localhost:9090/targets` → `gnmic:9273` **UP**.
- `http://localhost:9090/graph` → `network_instance_protocols_bgp_neighbor_session_state{source="leaf3"}` → 4 series a **1**.
- `http://localhost:3000` → *Network Telemetry* con datos, y **"NetOps Demo - BGP GitOps"** (`/d/netops-demo`): leaf3 = **4** en verde.

Cada `make lab-up` vuelve a descargar el plugin de Grafana (Internet). Para trabajar sin conexión, restaura el snapshot `lab-ready` en lugar de redesplegar.

---

## 6. Gitea y runner

Toda la capa GitOps corre en la VM: no depende de ningún servicio externo.

### 6.1 Gitea

```bash
cd ~/netops-demo/gitea
cp .env.example .env                       # VM_IP = lo que escribes en el navegador: localhost (túnel), IP o DNS
                                           # GITEA_PAT = lo rellenas en el paso 2 de abajo
docker compose up -d && sleep 10
# usuario de Gitea (independiente de los usuarios Linux; username/password/email son libres)
docker exec -u git gitea gitea admin user create --admin --username <usuario> \
  --password '<password>' --email <usuario>@example.com --must-change-password=false
```

Abre `http://localhost:3030` (o la IP), entra y:

1. **Nuevo repositorio** → `netops-gitops` (vacío, sin README).
2. **Token personal**: avatar → *Settings → Applications → Generate new token* → `netops-pipeline`, permiso **repository: Read and Write** (sirve para que `make push` y el job `promote` abran PRs por API). Cópialo y ponlo también en `gitea/.env` como `GITEA_PAT=…`.
3. **Secrets del repo** (los lee el pipeline; no confundir con `gitea/.env`, que solo lo usa tu shell): una vez creado el repositorio y configurado el remote del paso §7, ejecuta `make secrets`, que crea `GITEA_PAT` y `SRL_PASSWORD` por API a partir de `gitea/.env`. (A mano: `netops-gitops → Settings → Actions → Secrets`.) `make status` avisa si faltan.

### 6.2 Runner (modo host)

```bash
cd ~/netops-demo && make runner       # descarga act_runner, lo registra con label 'lab:host' y crea el servicio systemd
```

Comprueba en Gitea: *Site Administration → Actions → Runners* → `lab-runner` **Idle**.

> **Por qué modo host:** los jobs ejecutan `gnmic` y `python3` ya instalados en la VM y llegan a `172.80.80.0/24` directamente. Sin Docker-in-Docker ni Node.js; el checkout es un `git clone` con el PAT.

---

## 7. Repositorio GitOps

Desde **dentro de la VM** el remote es `localhost:3030` (no depende de túneles ni de la IP del DHCP):

```bash
cp -r ~/netops-demo/gitops-repo ~/netops-gitops && cd ~/netops-gitops
git init -b main && git add -A && git commit -m "leaf3: día 0 (solo underlay, ownership de overlay y servicio)"
git tag day0                                           # ← estado base al que vuelve `make reset`
git remote add origin http://<usuario>@localhost:3030/<usuario>/netops-gitops.git
git config credential.helper store                     # guarda el password/PAT tras el primer push
git push -u origin main --tags
cd ~/netops-demo && make secrets                       # secrets del pipeline (GITEA_PAT, SRL_PASSWORD) por API
```

Ese primer push lanza `deploy`. La intención base no declara overlay ni servicio pero **los posee** (`ownership`), y el job usa `--prune`: **los elimina de leaf3** (que el lab arranca completo). A partir de aquí el repositorio manda y leaf3 está en día 0. *Actions* debe terminar en verde con `DEPLOY OK`; el job `promote` dirá que la siguiente etapa no es automática.

> Si ya tenías un `netops-gitops` de una versión anterior del kit: copia encima `intent/`, `stages/`, `scripts/` y `.gitea/`, haz commit, `git tag -f day0`, borra el tag antiguo (`git push origin :demo-base`) y `git push -f origin main --tags`.

---

## 8. Flujo de cambio: del PR a la red

```
 rama etapa N ──push──▶ validate ──▶ PR N ──merge──▶ main ──push──▶ deploy ──▶ SR Linux ──▶ Grafana (+ anotación)
                        (lint, prerrequisitos,                       (Set atómico + verificación)   │
                         plan; no toca nada)                                                        ▼
                                                                     promote ──▶ rama etapa N+1 + PR N+1 (si auto_promote)
```

1. Una persona inicia el rollout: `make prep` (o `promote.py --stage overlay`) crea la rama de la etapa 1; `make push` la publica **y abre el Pull Request ya documentado**: "Qué cambia" (etapa, descripción, fragmento YAML), "Plan esperado" (la salida real de `netops.py --dry-run --prune` contra el nodo en ese momento) y un checklist con los prerrequisitos y el impacto calculados. Nadie escribe PRs a mano.
2. **validate** vuelve a comprobar en el nodo el prerrequisito de la etapa (día 0: underlay establecido) y publica el **plan** en su log: `+ añadir`, `= asegurar`, `- eliminar`.
3. **Merge** (borrando la rama). **deploy** aplica en una transacción gNMI, espera a que las sesiones establezcan y anota el despliegue en Grafana (líneas naranjas en los paneles).
4. **promote** ve que la etapa `service` tiene `auto_promote: true`: crea su rama con el fragmento fusionado y **abre el PR** con el mismo generador (descripción, YAML, plan real y checklist). Una persona lo revisa.
5. **validate** del PR 2 exige que el overlay esté `established` en el nodo (gate). **Merge** → **deploy** crea subinterfaz, vxlan-interface y mac-vrf, y verifica `oper-state up`.
6. Deshacer: **Revert** del PR y merge → `deploy --prune` elimina lo que ya no está declarado (servicio con sus miembros, o grupo y vecinos).

---

## 9. Escenario de ejemplo

```bash
cd ~/netops-demo
make prep             # leaf3 a día 0 por gNMI, tráfico iperf3, rama onboarding/leaf3-10-overlay con el commit
make status           # salud: lab, estado de leaf3, rollout, Prometheus, Grafana, Gitea, runner
make diff             # el cambio de la etapa 1: grupo iBGP-overlay + 2 vecinos
make pr-preview       # (opcional) el cuerpo del PR que se va a abrir
make push             # publica la rama y abre el PR documentado → validate → merge
#                      ... deploy aplica y verifica; promote abre el PR de la etapa 2 → validate (gate) → merge
make rollout          # [x] overlay  [x] service
make reset            # main ← day0 (force-push), borra las ramas de las etapas, leaf3 a día 0
```

Qué observar en `http://localhost:3000/d/netops-demo`: tras el PR 1, *Día 1* pasa de 0 a **2** y aparece la anotación del deploy; tras el PR 2, *vrf-1* pasa de AUSENTE a **UP** en leaf3, suben las MACs activas y **leaf3 e1-1** empieza a llevar el tráfico de `client3` (también en el weathermap del dashboard del lab).

Si el job `promote` no pudiera abrir el PR (token sin escritura, por ejemplo), `make promote && make push` crea la rama de la siguiente etapa localmente y la publica para abrir el PR a mano.

---

## 10. Guía de desarrollo

### 10.1 Organización del código

| Componente | Responsabilidad | Dónde se prueba |
|---|---|---|
| `intent/<nodo>.yml` | Estado deseado del nodo (datos) + `ownership` (qué posee GitOps) + `prerequisites`. | `validate` (lint + plan) |
| `stages/<nodo>.yml` | Plan de despliegue: fragmentos de intención en orden, con `auto_promote`, rama y título. | `promote.py --list`, `make test` |
| `scripts/netops.py` | Reconciliación: lee el nodo por gNMI, comprueba prerrequisitos, calcula el plan, aplica (un Set por tipo de recurso) y verifica. Sin estado propio. | `make test` (mock) + `--dry-run` contra el lab |
| `scripts/promote.py` | Secuenciación: fusiona el siguiente fragmento en la intención, crea la rama y abre el PR (API de Gitea). | `make test` (repo git temporal) |
| `.gitea/workflows/netops.yml` | Cuándo: ramas → validate; main → deploy → promote. | Un push a una rama de prueba |
| `lab-patches/` | Qué se observa: telemetría por vecino, dashboard por etapas, anotaciones. | Prometheus `/graph` y Grafana |

Principios: la intención es declarativa y mínima (el script rellena el resto replicando la configuración del lab); el script es **idempotente** (reasegura lo declarado, no cambia lo ya conforme), **acotado** (solo toca lo poseído; el underlay es solo prerrequisito) y **atómico** (una transacción gNMI por tipo de recurso, de modo que subinterfaz, vxlan y mac-vrf se crean o fallan juntos); todo cambio pasa por un PR con el plan y los prerrequisitos visibles.

### 10.2 Cómo probar

```bash
make test                                                           # sin laboratorio: 27 casos (ciclo día 0→1→2, rollback, gates, promote)
python3 scripts/netops.py  --intent intent/leaf3.yml --show         # contra el lab: estado real
python3 scripts/netops.py  --intent intent/leaf3.yml --dry-run --prune   # prerrequisitos + plan que vería el PR
python3 scripts/promote.py --node leaf3 --list                      # estado del rollout respecto a main
```

Añade un caso a `tests/run.sh` por cada comportamiento nuevo (una línea `t "nombre" "patrón" [--rc N] comando…`). El mock (`tests/mock-gnmic/gnmic`) es un mini dispositivo con estado: rechaza borrar un grupo con vecinos, exige que existan la subinterfaz y la vxlan-interface antes de crear el mac-vrf, y responde en las dos formas de SR Linux ante un `get` con comodín.

### 10.3 Ramas, PRs y Gitea

- **Nunca se empuja a `main`**: cada etapa es una rama corta (`onboarding/<nodo>-<orden>-<etapa>`) y un PR; el PR *es* la ventana de cambio y deja registrados plan, prerrequisitos y aprobación.
- **Los PRs se abren por API, ya documentados** (`make push` para el humano, `promote` para la máquina), con un único generador de cuerpo en `promote.py`. Así ningún cambio depende de que alguien recuerde pegar el plan. La plantilla `.gitea/PULL_REQUEST_TEMPLATE.md` solo aplica a PRs creados a mano desde la web.
- **Una etapa por PR.** Juntar overlay y servicio en un PR funciona (el script aplica en orden y espera entre ambos), pero pierdes la gate explícita, la verificación por etapa y el rollback independiente.
- **Promoción automática, aprobación humana.** `promote` solo crea ramas y PRs para etapas con `auto_promote: true`; nunca mergea. Es el patrón de *staged rollout* de las herramientas de CD.
- Protege `main` (`Settings → Branches → Add rule`): sin push directo, status check **`validate`** obligatorio y, si quieres, una aprobación. `make reset` hace force-push a `main`: añade tu usuario a la lista blanca de *force push* o usa *Revert* como vuelta atrás.
- Al mergear, **borra la rama** (casilla del diálogo, o por defecto en *Settings → Repository → Pull Requests*). Estrategia *merge commit* o *squash*, no *rebase* con checks obligatorios.
- Mensajes de commit en imperativo y con el nodo y la etapa: `leaf3: dia 1 - sesiones iBGP EVPN de overlay`.
- Tags para hitos del estado de la red (`day0`, `leaf3-onboarded`): checkout del tag + merge a `main` es un rollback completo.

### 10.4 Observabilidad de los cambios

- Cada `deploy` anota en Grafana (`POST /api/annotations`, tags `netops,deploy`) con el resultado y el mensaje del commit; el dashboard las dibuja sobre los paneles para **correlar cambio y efecto**.
- Paneles por etapa con umbrales: día 0 (underlay), día 1 (overlay), día 2 (`vrf-1` por leaf, MACs, tráfico de acceso). Si un panel no cambia tras un deploy en verde, es la señal de que la verificación del pipeline no cubre lo que importa: añade el check a `netops.py`.
- El log del job es la auditoría: estado leído, prerrequisitos, plan y verificación con tiempos.

### 10.5 Límites conocidos

- Un nodo por fichero de intención y un tipo de servicio (mac-vrf L2 con una vxlan-interface). Añadir ip-vrf, varios VNIs o políticas implica un renderizador por recurso y sus casos de prueba.
- Las identidades YANG se envían sin prefijo de módulo (`mac-vrf`, `bridged`). Si tu versión de SR Linux las rechaza, exporta `SRL_QUALIFY_IDENTITIES=1` en el runner (`Environment=` del unit) para enviarlas cualificadas.
- La verificación de servicio comprueba `oper-state` y muestra las MACs activas; no lanza tráfico de prueba. Un test de alcance (ping entre clientes) sería el siguiente check natural.
- Dos repositorios: el kit (este) y `netops-gitops`. Un cambio en `gitops-repo/` hay que replicarlo en `~/netops-gitops` y, si usas `make reset`, mover el tag (`git tag -f day0 && git push -f origin day0`).

---

## 11. Troubleshooting

| Síntoma | Causa probable | Arreglo |
|---|---|---|
| `git clone`/`curl` se cuelgan pero `apt` funciona | solo apt tiene proxy | §3 completo + relogin |
| `sudo curl …` se cuelga | `sudo` limpia el entorno | `/etc/sudoers.d/proxy` (env_keep) o `sudo -E` |
| `docker: permission denied` | grupo `docker` no efectivo aún | cerrar sesión y volver a entrar |
| `docker pull` falla con proxy | demonio sin proxy | `/etc/docker/daemon.json` con `proxies` + `systemctl restart docker` |
| `gnmic` "connection refused" en los logs | nodos arrancando | solo el primer minuto; `--since 5m` debe dar 0 |
| `gnmic` falla con proxy configurado | gRPC usa `HTTPS_PROXY` | `172.80.80.0/24` en `no_proxy` |
| Dashboard NetOps no aparece; log `permission denied` | fichero sin permiso de lectura para uid 472 | `chmod 644 ~/srl-telemetry-lab/configs/grafana/dashboards/*.json` (el `patch` actual ya instala con 0644) |
| Grafana con triángulos rojos / NetOps vacío | uid de datasource | `datasource.yml` del kit (`PBFA97CFB590B2093` / `P8E80F9AEF21F6940`); `docker restart grafana` |
| Grafana `running` pero :3000 no responde | plugin FlowPanel sin proxy | variables en el nodo grafana (§3) + `--node-filter grafana` |
| Grafana paneles vacíos solo con proxy | consulta datasources vía proxy | `NO_PROXY: …,prometheus,loki` en el nodo grafana |
| No llego a :3000/:9090 desde mi equipo | VM en red privada | `demo/tunnel.sh` (o DNAT, §2.2) |
| Runner **Desconectado / Nunca** en Gitea | demonio con un registro antiguo (Gitea reinstalada) | `sudo systemctl restart act_runner`; si persiste, `rm ~/act_runner/.runner && make runner` |
| Job **Waiting** | runner caído o label | `sudo systemctl status act_runner`; `runs-on: lab` = label `lab:host` |
| Job falla con `Unauthenticated: Missing password` | secret `SRL_PASSWORD` ausente | `Settings → Actions → Secrets` |
| `validate` **BLOQUEADO por prerrequisitos** | etapa anterior no desplegada/verificada | mergea y verifica la etapa anterior; es la gate funcionando |
| `promote` falla con `falta GITEA_PAT` | el secret no existe en el repo (Gitea recreada) | `make secrets` y "Volver a ejecutar todos los trabajos" |
| `promote` falla con `API Gitea 403/401` o al hacer push | PAT sin escritura | regenera el token con *repository: Read and Write* y actualiza el secret `GITEA_PAT` |
| `make push` dice `falta GITEA_PAT` | `gitea/.env` sin el token | añade `GITEA_PAT=<token>` a `gitea/.env` (mismo valor que el secret) |
| `make push` abre el PR pero el plan sale BLOQUEADO | etapa anterior no desplegada | es la gate; mergea y verifica la anterior, luego `make push` de nuevo (el PR existente no se duplica) |
| `promote` dice "la rama ya existe en el remoto" | etapa ya propuesta | nada que hacer: revisa el PR abierto |
| `gnmic set` rechaza `mac-vrf`/`bridged` | identidad sin prefijo de módulo | `SRL_QUALIFY_IDENTITIES=1` en el entorno del runner |
| `vrf-1` no sube o sin MACs | overlay no establecido / tráfico parado | `make status`; `make traffic-start`; `ssh admin@spine1` → `show … bgp neighbor` |
| Job falla en *Checkout* | PAT/URL | secret `GITEA_PAT`; el runner clona por `http://localhost:3030` |
| Job `gnmic: not found` | PATH del servicio | `Environment=PATH=…` en el unit o `sudo ln -s $(which gnmic) /usr/local/bin/gnmic` |
| Plan vacío ("no se pudo interpretar…") | formato de respuesta gNMI | el script imprime la salida bruta: revisa la ruta/encoding |
| Sesión no llega a `established` | otro extremo sin configurar | `ssh admin@spine2` → `show … bgp neighbor` |
| `make status` dice que Gitea no corre | `docker ps` sin permisos | relogin; los scripts ya hacen fallback a `sudo docker` |
| Dashboard: panel de MACs o tráfico vacío | nombre de métrica distinto en tu versión de gNMIc | Prometheus `/graph` → busca `bridge_table` / `traffic_rate` y ajusta la expresión |
| `git push` a GitHub pide password y falla | GitHub exige token | `gh auth login` o PAT + `credential.helper store` |
| `make reset` falla al hacer push | `main` protegida | lista blanca de force-push o desproteger temporalmente |
