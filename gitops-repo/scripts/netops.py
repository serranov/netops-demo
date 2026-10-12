#!/usr/bin/env python3
"""
netops.py - Config-as-Code para Nokia SR Linux via gNMI (gnmic).

Reconcilia la INTENCION (intent/<nodo>.yml) contra el nodo:

  --show      estado actual: grupos y vecinos BGP (estado + grupo), servicios (tipo + oper-state)
  --dry-run   comprueba prerrequisitos y muestra el PLAN (añadir / asegurar / eliminar), sin tocar nada
  --apply     aplica el plan en UNA transaccion gNMI Set por tipo de recurso y verifica el resultado
  --prune     (con dry-run/apply) elimina los objetos POSEIDOS (ownership) que no esten declarados

Recursos gestionados
  bgp.groups[]        grupo BGP + sus vecinos (dia 1: overlay iBGP EVPN)
  services[]          mac-vrf + vxlan-interface + subinterfaces de acceso (dia 2: servicio del tenant)

Alcance: solo se tocan los grupos/servicios declarados o listados en `ownership`. El underlay
(grupo de `prerequisites.underlay_group`) nunca se modifica: es dia 0 y se usa solo como prerrequisito.

Prerrequisitos (gates)
  dia 1: al menos una sesion `established` en el grupo de underlay antes de crear el overlay.
  dia 2: todos los vecinos del overlay declarado `established` antes de crear un servicio
         (si overlay y servicio van en la misma intencion, se aplican en orden y se espera entre ambos).

Entorno: SRL_USER (admin), SRL_PASSWORD (NokiaSrl1!), SRL_QUALIFY_IDENTITIES=1 si el nodo exige
identidades con prefijo de modulo (p.ej. "srl_nokia-network-instance:mac-vrf").
Salida: 0 OK · 1 error de ejecucion / intencion / prerrequisito · 2 aplicado pero la verificacion fallo.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML: pip3 install pyyaml  (o apt install python3-yaml)")

QUALIFY = os.environ.get("SRL_QUALIFY_IDENTITIES", "0") == "1"


def log(msg=""):
    print(msg, flush=True)


# =============================================================================== gNMI
def gnmic_base(target):
    # 'or' y no el 2º argumento de get(): en CI un secret ausente llega como variable VACIA
    user = os.environ.get("SRL_USER") or "admin"
    pwd = os.environ.get("SRL_PASSWORD") or "NokiaSrl1!"
    return ["gnmic", "-a", target, "-u", user, "-p", pwd,
            "--skip-verify", "-e", "json_ietf", "--timeout", "20s"]


def run(cmd, check=True):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        log(res.stdout)
        log(res.stderr)
        raise SystemExit("ERROR ejecutando gnmic " + " ".join(cmd[10:]))
    return res


def gnmi_get(target, path, datatype):
    """Lista de (path_completo, valor) de todas las actualizaciones de un Get (formato JSON de gnmic)."""
    res = run(gnmic_base(target) + ["get", "--path", path, "-t", datatype, "--format", "json"])
    try:
        data = json.loads(res.stdout or "[]")
    except json.JSONDecodeError:
        data = []
    if isinstance(data, dict):
        data = [data]
    out = []
    for notif in data:
        prefix = notif.get("prefix", "") or ""
        for upd in notif.get("updates", []) or []:
            p = upd.get("Path") or upd.get("path") or ""
            full = f"{prefix}/{p}" if prefix else p
            for v in (upd.get("values", {}) or {}).values():
                out.append((full, v))
    return out


def collect(updates, key, leaf):
    """{valor_de_key: valor_de_leaf} para una lista YANG, aceptando las dos formas de respuesta de
    SR Linux ante un comodin: subarbol JSON ({"x":[{key:..., leaf:...}]}) o una actualizacion por hoja
    con la clave en el Path (.../x[key=K]/leaf -> valor)."""
    found = {}
    key_re = re.compile(r"(?<![\w-])" + re.escape(key) + r"=([^\]]+)\]")

    def walk(v, path):
        if isinstance(v, dict):
            if leaf in v:
                k = v.get(key)
                if k is None:
                    m = key_re.search(path)
                    k = m.group(1) if m else None
                if k is not None:
                    found[str(k)] = str(v[leaf])
                    return
            for x in v.values():
                walk(x, path)
        elif isinstance(v, list):
            for x in v:
                walk(x, path)
        elif isinstance(v, (str, int)) and path.endswith("/" + leaf):
            m = key_re.search(path)
            if m:
                found[m.group(1)] = str(v)

    for p, v in updates:
        walk(v, p)
    return found


def find_names(updates, list_key):
    """Nombres de los elementos de una lista (p.ej. 'interface' o 'vxlan-interface') dentro de un subarbol."""
    names = set()

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k == list_key and isinstance(x, list):
                    names.update(str(e.get("name")) for e in x if isinstance(e, dict) and "name" in e)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    for _, v in updates:
        walk(v)
    return names


def gnmi_set(target, updates=(), deletes=()):
    """UNA transaccion Set con N updates (path, payload) y M deletes (path). Atomica en SR Linux."""
    if not updates and not deletes:
        return
    cmd = gnmic_base(target) + ["set"]
    tmp_files = []
    try:
        for path, payload in updates:
            tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
            json.dump(payload, tmp)
            tmp.close()
            tmp_files.append(tmp.name)
            cmd += ["--update-path", path, "--update-file", tmp.name]
        for path in deletes:
            cmd += ["--delete", path]
        run(cmd)
    finally:
        for f in tmp_files:
            os.unlink(f)


def ident(module, name):
    return f"{module}:{name}" if QUALIFY else name


# =============================================================================== intencion
def load_intent(path):
    with open(path) as fh:
        it = yaml.safe_load(fh) or {}
    for key in ("node", "target"):
        if key not in it:
            raise SystemExit(f"Intencion invalida: falta '{key}' en {path}")
    it.setdefault("network_instance", "default")
    it.setdefault("prerequisites", {}).setdefault("underlay_group", "eBGP")
    it.setdefault("ownership", {})
    it["ownership"].setdefault("bgp_groups", [])
    it["ownership"].setdefault("services", [])
    it.setdefault("bgp", {}).setdefault("groups", [])
    it["bgp"]["groups"] = it["bgp"]["groups"] or []
    it["services"] = it.get("services") or []
    for g in it["bgp"]["groups"]:
        if "name" not in g:
            raise SystemExit(f"Grupo BGP sin 'name': {g}")
        g["neighbors"] = g.get("neighbors") or []
        for n in g["neighbors"]:
            if "peer_address" not in n:
                raise SystemExit(f"Vecino sin 'peer_address' en grupo {g['name']}: {n}")
    for s in it["services"]:
        for key in ("name", "vni", "evi", "route_target", "vxlan", "access_interfaces"):
            if key not in s:
                raise SystemExit(f"Servicio invalido (falta '{key}'): {s}")
        s.setdefault("type", "mac-vrf")
        s.setdefault("ecmp", 2)
    return it


# =============================================================================== lectura del nodo
def read_bgp(target, ni):
    bgp = f"/network-instance[name={ni}]/protocols/bgp"
    groups = set(collect(gnmi_get(target, f"{bgp}/group[group-name=*]/group-name", "CONFIG"),
                         "group-name", "group-name"))
    states = collect(gnmi_get(target, f"{bgp}/neighbor[peer-address=*]/session-state", "STATE"),
                     "peer-address", "session-state")
    pgroups = collect(gnmi_get(target, f"{bgp}/neighbor[peer-address=*]/peer-group", "CONFIG"),
                      "peer-address", "peer-group")
    neighbors = {p: {"state": states.get(p, "?"), "group": pgroups.get(p, "?")}
                 for p in sorted(set(states) | set(pgroups))}
    return groups, neighbors


def read_services(target):
    types = collect(gnmi_get(target, "/network-instance[name=*]/type", "CONFIG"), "name", "type")
    oper = collect(gnmi_get(target, "/network-instance[name=*]/oper-state", "STATE"), "name", "oper-state")
    out = {}
    for name, t in types.items():
        if name in ("default", "mgmt"):
            continue
        out[name] = {"type": t.split(":")[-1], "oper": oper.get(name, "?")}
    return out


def service_members(target, name):
    """Subinterfaces y vxlan-interfaces que usa un mac-vrf existente (para poder eliminarlos con el)."""
    upd = gnmi_get(target, f"/network-instance[name={name}]", "CONFIG")
    return sorted(find_names(upd, "interface")), sorted(find_names(upd, "vxlan-interface"))


def mac_entries(target, name):
    upd = gnmi_get(target, f"/network-instance[name={name}]/bridge-table/statistics/active-entries", "STATE")
    for _, v in upd:
        if isinstance(v, (int, str)):
            return str(v)
        if isinstance(v, dict):
            for x in v.values():
                if isinstance(x, (int, str)):
                    return str(x)
    return "?"


# =============================================================================== render SR Linux
def group_payload(g):
    p = {}
    if "peer_as" in g:
        p["peer-as"] = int(g["peer_as"])
    if "local_as" in g:
        p["local-as"] = {"as-number": int(g["local_as"])}
    if g.get("export_policy"):
        p["export-policy"] = [str(x) for x in g["export_policy"]]
    if g.get("import_policy"):
        p["import-policy"] = [str(x) for x in g["import_policy"]]
    if g.get("afi_safi"):
        p["afi-safi"] = [{"afi-safi-name": k, "admin-state": v} for k, v in g["afi_safi"].items()]
    if g.get("timers"):
        p["timers"] = {k.replace("_", "-"): int(v) for k, v in g["timers"].items()}
    return p


def neighbor_payload(n, group):
    p = {"admin-state": "enable", "peer-group": group}
    if "peer_as" in n:
        p["peer-as"] = int(n["peer_as"])
    if n.get("description"):
        p["description"] = str(n["description"])
    if n.get("local_address"):
        p["transport"] = {"local-address": str(n["local_address"])}
    return p


def service_updates(s):
    """Lista de (path, payload) que materializa un servicio mac-vrf (replica leaf3.cfg del lab)."""
    ups = []
    for a in s["access_interfaces"]:
        ups.append((f"/interface[name={a['interface']}]/subinterface[index={int(a['index'])}]",
                    {"type": ident("srl_nokia-interfaces", "bridged"), "admin-state": "enable"}))
    vx = s["vxlan"]
    ups.append((f"/tunnel-interface[name={vx['tunnel_interface']}]/vxlan-interface[index={int(vx['index'])}]",
                {"type": ident("srl_nokia-tunnel-interfaces", "bridged"), "ingress": {"vni": int(s["vni"])}}))
    vxname = f"{vx['tunnel_interface']}.{int(vx['index'])}"
    ups.append((f"/network-instance[name={s['name']}]", {
        "type": ident("srl_nokia-network-instance", s["type"]),
        "admin-state": "enable",
        "interface": [{"name": f"{a['interface']}.{int(a['index'])}"} for a in s["access_interfaces"]],
        "vxlan-interface": [{"name": vxname}],
        "protocols": {
            "bgp-evpn": {"bgp-instance": [{"id": 1, "admin-state": "enable", "vxlan-interface": vxname,
                                           "evi": int(s["evi"]), "ecmp": int(s["ecmp"])}]},
            "bgp-vpn": {"bgp-instance": [{"id": 1, "route-target": {"export-rt": str(s["route_target"]),
                                                                    "import-rt": str(s["route_target"])}}]},
        },
    }))
    return ups


def member_delete_paths(subifs, vxlanifs):
    dels = []
    for sub in subifs:                       # "ethernet-1/1.0" -> interface + subinterface
        iface, _, idx = sub.rpartition(".")
        dels.append(f"/interface[name={iface}]/subinterface[index={idx}]")
    for vxi in vxlanifs:                     # "vxlan1.1" -> tunnel-interface + vxlan-interface
        tun, _, idx = vxi.rpartition(".")
        dels.append(f"/tunnel-interface[name={tun}]/vxlan-interface[index={idx}]")
    return dels


# =============================================================================== plan
class Plan:
    def __init__(self):
        self.lines = []
        self.bgp_updates, self.bgp_deletes = [], []
        self.svc_updates, self.svc_deletes = [], []
        self.expect_established, self.expect_gone = [], []
        self.expect_up, self.expect_svc_gone = [], []
        self.changes = 0

    def add(self, line):
        self.lines.append(line)
        if line.lstrip().startswith(("+", "-")):
            self.changes += 1

    def empty(self):
        return not (self.bgp_updates or self.bgp_deletes or self.svc_updates or self.svc_deletes)


def build_plan(it, groups_dev, nbrs_dev, svcs_dev, target, prune):
    ni = it["network_instance"]
    bgp = f"/network-instance[name={ni}]/protocols/bgp"
    plan = Plan()
    underlay = it["prerequisites"]["underlay_group"]

    # ---- BGP: grupos y vecinos
    desired_groups = {g["name"]: g for g in it["bgp"]["groups"]}
    owned_groups = set(it["ownership"]["bgp_groups"]) | set(desired_groups)
    owned_groups.discard(underlay)
    for name, g in desired_groups.items():
        verb = "+ AÑADIR  " if name not in groups_dev else "= asegurar"
        plan.add(f"   {verb} grupo BGP {name} (AS {g.get('peer_as', '?')}, {', '.join(g.get('afi_safi', {}))})")
        plan.bgp_updates.append((f"{bgp}/group[group-name={name}]", group_payload(g)))
        for n in g["neighbors"]:
            peer = str(n["peer_address"])
            verb = "+ AÑADIR  " if peer not in nbrs_dev else "= asegurar"
            plan.add(f"   {verb} vecino {peer} (grupo {name})")
            plan.bgp_updates.append((f"{bgp}/neighbor[peer-address={peer}]", neighbor_payload(n, name)))
            plan.expect_established.append(peer)
    declared_peers = {str(n["peer_address"]) for g in desired_groups.values() for n in g["neighbors"]}
    for peer, info in nbrs_dev.items():
        if info["group"] in owned_groups and peer not in declared_peers:
            if prune:
                plan.add(f"   - ELIMINAR vecino {peer} (grupo {info['group']}, no declarado)")
                plan.bgp_deletes.append(f"{bgp}/neighbor[peer-address={peer}]")
                plan.expect_gone.append(peer)
            else:
                plan.add(f"   ! aviso: vecino {peer} (grupo {info['group']}) no declarado; --prune lo eliminaria")
    for name in sorted(groups_dev & owned_groups - set(desired_groups)):
        if prune:
            plan.add(f"   - ELIMINAR grupo BGP {name} (poseido, no declarado)")
            plan.bgp_deletes.append(f"{bgp}/group[group-name={name}]")
        else:
            plan.add(f"   ! aviso: grupo {name} poseido y no declarado; --prune lo eliminaria")

    # ---- Servicios
    desired_svcs = {s["name"]: s for s in it["services"]}
    owned_svcs = set(it["ownership"]["services"]) | set(desired_svcs)
    for name, s in desired_svcs.items():
        verb = "+ AÑADIR  " if name not in svcs_dev else "= asegurar"
        acc = ", ".join(f"{a['interface']}.{a['index']}" for a in s["access_interfaces"])
        plan.add(f"   {verb} servicio {name} ({s['type']}, VNI {s['vni']}, EVI {s['evi']}, RT {s['route_target']}; acceso {acc})")
        plan.svc_updates += service_updates(s)
        plan.expect_up.append(name)
    for name in sorted(set(svcs_dev) & owned_svcs - set(desired_svcs)):
        if prune:
            subifs, vxlanifs = service_members(target, name)
            plan.add(f"   - ELIMINAR servicio {name} (poseido, no declarado; con {', '.join(subifs + vxlanifs) or 'sin miembros'})")
            plan.svc_deletes.append(f"/network-instance[name={name}]")
            plan.svc_deletes += member_delete_paths(subifs, vxlanifs)
            plan.expect_svc_gone.append(name)
        else:
            plan.add(f"   ! aviso: servicio {name} poseido y no declarado; --prune lo eliminaria")
    return plan


def check_prerequisites(it, nbrs_dev, mode):
    """Devuelve lista de errores (bloquean) y avisos."""
    errors, warns = [], []
    underlay = it["prerequisites"]["underlay_group"]
    if it["bgp"]["groups"] or it["services"]:
        up = [p for p, i in nbrs_dev.items() if i["group"] == underlay and i["state"] == "established"]
        if not up:
            errors.append(f"dia 0: ninguna sesion established en el grupo de underlay '{underlay}'")
        else:
            warns.append(f"dia 0 OK: underlay '{underlay}' con {len(up)} sesion(es) established ({', '.join(up)})")
    if it["services"]:
        overlay_peers = [str(n["peer_address"]) for g in it["bgp"]["groups"] for n in g["neighbors"]]
        if not overlay_peers:
            errors.append("dia 1: la intencion declara servicios pero ningun grupo/vecino de overlay")
        else:
            missing = [p for p in overlay_peers if nbrs_dev.get(p, {}).get("state") != "established"]
            if missing and mode == "dry-run":
                errors.append(f"dia 1: overlay no establecido en el nodo ({', '.join(missing)}); "
                              "mergea y verifica primero la etapa de overlay")
            elif missing:
                warns.append(f"dia 1: overlay pendiente ({', '.join(missing)}); se aplicara antes del servicio y se esperara")
            else:
                warns.append(f"dia 1 OK: overlay established ({', '.join(overlay_peers)})")
    return errors, warns


# =============================================================================== verificacion
def wait_for(fn, seconds, every=2):
    deadline = time.time() + seconds
    while True:
        ok, detail = fn()
        if ok or time.time() >= deadline:
            return ok, detail
        time.sleep(every)


def verify_bgp(target, ni, plan):
    def check():
        _, nbrs = read_bgp(target, ni)
        ok = all(nbrs.get(p, {}).get("state") == "established" for p in plan.expect_established) \
            and not any(p in nbrs for p in plan.expect_gone)
        return ok, nbrs
    return wait_for(check, plan.wait)


def verify_services(target, plan):
    def check():
        svcs = read_services(target)
        ok = all(svcs.get(n, {}).get("oper") == "up" for n in plan.expect_up) \
            and not any(n in svcs for n in plan.expect_svc_gone)
        return ok, svcs
    return wait_for(check, plan.wait)


# =============================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intent", required=True, help="fichero YAML de intencion (p.ej. intent/leaf3.yml)")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--show", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--prune", action="store_true", help="eliminar objetos poseidos no declarados")
    ap.add_argument("--wait", type=int, default=45, help="segundos max. de espera en cada verificacion")
    args = ap.parse_args()

    it = load_intent(args.intent)
    target, ni = it["target"], it["network_instance"]
    log(f"== netops :: {it['node']} ({target}) :: ownership grupos={it['ownership']['bgp_groups']} "
        f"servicios={it['ownership']['services']}" + ("   [prune]" if args.prune else ""))

    log("\n-- Estado actual del nodo (gNMI get)")
    groups_dev, nbrs_dev = read_bgp(target, ni)
    svcs_dev = read_services(target)
    underlay = it["prerequisites"]["underlay_group"]
    owned = set(it["ownership"]["bgp_groups"]) | {g["name"] for g in it["bgp"]["groups"]}
    log(f"   grupos BGP : {', '.join(sorted(groups_dev)) or '(ninguno)'}")
    for peer, info in nbrs_dev.items():
        tag = "underlay, dia 0" if info["group"] == underlay else ("gestionado" if info["group"] in owned else "no gestionado")
        log(f"   vecino {peer:<14} {info['state']:<12} grupo {info['group']:<14} [{tag}]")
    for name, info in sorted(svcs_dev.items()):
        tag = "gestionado" if name in set(it["ownership"]["services"]) | {s["name"] for s in it["services"]} else "no gestionado"
        log(f"   servicio {name:<12} {info['type']:<8} oper {info['oper']:<6} [{tag}]")
    if not svcs_dev:
        log("   servicios  : (ninguno)")
    if args.show:
        return 0

    log("\n-- Prerrequisitos")
    errors, warns = check_prerequisites(it, nbrs_dev, "dry-run" if args.dry_run else "apply")
    for w in warns:
        log(f"   {w}")
    for e in errors:
        log(f"   !! {e}")
    if errors:
        log("\n== BLOQUEADO por prerrequisitos.")
        return 1

    plan = build_plan(it, groups_dev, nbrs_dev, svcs_dev, target, args.prune)
    plan.wait = args.wait
    log("\n-- Plan")
    for line in plan.lines:
        log(line)
    if plan.changes == 0:
        log("   sin cambios: la intencion ya esta reconciliada (solo se reasegura lo declarado)")
    if args.dry_run:
        log("\n[dry-run] nada aplicado. Validacion OK.")
        return 0

    ok_all = True
    if plan.bgp_updates or plan.bgp_deletes:
        log("\n-- Aplicando BGP (1 transaccion gNMI Set)")
        gnmi_set(target, plan.bgp_updates, plan.bgp_deletes)
        log(f"   ok  {len(plan.bgp_updates)} update(s), {len(plan.bgp_deletes)} delete(s)")
        log(f"-- Verificando BGP (hasta {plan.wait}s)")
        ok, nbrs = verify_bgp(target, ni, plan)
        for p in plan.expect_established:
            st = nbrs.get(p, {}).get("state", "ausente")
            log(f"   {'OK ' if st == 'established' else '!! '}{p:<16} {st}")
        for p in plan.expect_gone:
            log(f"   {'OK ' if p not in nbrs else '!! '}{p:<16} {'eliminado' if p not in nbrs else 'sigue presente'}")
        ok_all = ok_all and ok
        if not ok and plan.svc_updates:
            log("   !! overlay no establecido: no se aplica el servicio (prerrequisito dia 1)")
            log("\n== DEPLOY con errores.")
            return 2

    if plan.svc_updates or plan.svc_deletes:
        log("\n-- Aplicando servicios (1 transaccion gNMI Set)")
        gnmi_set(target, plan.svc_updates, plan.svc_deletes)
        log(f"   ok  {len(plan.svc_updates)} update(s), {len(plan.svc_deletes)} delete(s)")
        log(f"-- Verificando servicios (hasta {plan.wait}s)")
        ok, svcs = verify_services(target, plan)
        for n in plan.expect_up:
            st = svcs.get(n, {}).get("oper", "ausente")
            extra = f"  (MACs activas: {mac_entries(target, n)})" if st == "up" else ""
            log(f"   {'OK ' if st == 'up' else '!! '}{n:<16} oper-state {st}{extra}")
        for n in plan.expect_svc_gone:
            log(f"   {'OK ' if n not in svcs else '!! '}{n:<16} {'eliminado' if n not in svcs else 'sigue presente'}")
        ok_all = ok_all and ok

    log("\n== DEPLOY OK: intencion reconciliada." if ok_all
        else "\n== DEPLOY con avisos: alguna verificacion fallo (revisa el otro extremo / prerrequisitos).")
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
