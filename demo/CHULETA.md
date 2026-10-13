# 🗒️ Chuleta del directo — Bloque 3 (imprímela)

**Antes de subir:** `make prep && make status` · túnel abierto · pestañas: Grafana NetOps, Grafana lab, Gitea PRs, Gitea Actions, Proxmox SDN · GIFs a mano · Terminal A en `~/srl-telemetry-lab`, Terminal B en `~/netops-demo`.

---

## ACTO 1 — La fabric viva y el leaf nuevo (3 min)

| Haz | Di |
|---|---|
| **Terminal A** → `sudo containerlab inspect -t st.clab.yml` | "Fabric Clos: 2 spines, 3 leafs SR Linux, contenedores en una VM de Proxmox, levantada desde un YAML." |
| **Terminal B** → `make status` (bloque *leaf3 segun netops.py*) | "leaf3 es el leaf **nuevo**: acaba de llegar un rack de Proxmox. Tiene underlay (día 0) y nada más: ni overlay EVPN ni servicio. client3 es ese servidor." |
| **Proxmox → Datacenter → SDN** (60 s) | "La VNet del tenant en Proxmox termina en un VNI de la fabric. Para que este servidor entre, hay que adherir el leaf al overlay y al servicio." |
| **Grafana NetOps** | "Día 0 verde (2), día 1 en rojo (0), vrf-1 AUSENTE en leaf3. Y leaf3 e1-1 sin tráfico." |

---

## ACTO 2 — Onboarding por GitOps (4–5 min)

| Haz | Di |
|---|---|
| **Terminal B** → `make diff` | "Etapa 1, el overlay: un grupo iBGP EVPN y dos sesiones a los route reflectors. YAML, no CLI." |
| `make push` → Gitea → *Pull Requests* → PR #1 | "Publico la rama y el PR se abre solo, ya documentado: qué cambia, el fragmento, y el **plan calculado contra el nodo real** con el prerrequisito comprobado. Nadie ha escrito esto a mano." |
| **Actions** → `validate` → log: `dia 0 OK`, `+ AÑADIR vecino 10.0.2.1/2` | "Lee el nodo real por gNMI. Sin tocar nada." |
| **PR** → **Merge** (borrar rama) | "Aprobado." |
| **Actions** → `deploy` → `OK 10.0.2.1 established` → `DEPLOY OK` | "Una transacción gNMI y espera a que establezcan. Y anota el despliegue en Grafana." |
| **Grafana NetOps** → día 1 pasa a **2** verde; línea naranja en el timeline | "El overlay está. Fijaos en la línea naranja: cambio y efecto correlados." |
| **Actions** → job `promote` → **PR #2 abierto automáticamente** | "El pipeline ha propuesto solo la etapa 2 porque la 1 está verificada. Nadie ha escrito ese PR." |
| **PRs** → PR #2 → `validate` verde (`dia 1 OK`, `+ AÑADIR servicio vrf-1`) → **Merge** | "La gate: si el overlay no estuviera establecido, este PR estaría bloqueado. Merge." |
| **Actions** → `deploy` → `OK vrf-1 oper-state up (MACs activas: n)` | "mac-vrf, VNI 1, subinterfaz de acceso. El servidor ya está en el tenant." |
| **Grafana NetOps** → vrf-1 **UP** en leaf3, MACs suben, **e1-1 con tráfico** · **Grafana lab** → weathermap | "client3 habla con el resto. Día 0, 1 y 2 por Git, con verificación en cada paso." |

**Cierre:** *"Dos pull requests, cero comandos en el equipo, y la red contó sola lo que pasaba en cada etapa."*

---

## Si algo falla

* Job **Waiting** > 20 s → `sudo systemctl restart act_runner` y sigue hablando.
* `promote` no abre el PR #2 → `make promote && make push` y crea el PR a mano ("lo haría el pipeline").
* Sesión no establece → `ssh admin@spine1` → `show network-instance default protocols bgp neighbor` (debe listar 10.0.1.3).
* Runner / Gitea caídos → **GIF del Acto 2** y narra.

## Reset (fuera del directo)

`make reset && make prep`
