#!/usr/bin/env python3
"""
promote.py - despliegue por etapas y Pull Requests documentados automaticamente.

  --node leaf3 --list            estado de cada etapa (aplicada / pendiente) respecto a main
  --node leaf3 --stage overlay   crea la rama de esa etapa con el fragmento fusionado (commit local)
  --node leaf3 --next            idem para la primera etapa pendiente
  --auto                         (con --next) solo si la etapa pendiente tiene auto_promote: true
  --open-pr                      (con --stage/--next) ademas publica la rama y abre el PR en Gitea
  --node leaf3 --pr              abre el PR de la RAMA ACTUAL (ya publicada): descripcion desde la etapa
                                 (o desde los commits si no es una etapa) + plan real (netops --dry-run)
  --print                        (con --pr) solo imprime el cuerpo del PR, sin llamar a la API

El cuerpo del PR se genera siempre con el mismo codigo, asi que ningun PR del flujo requiere
escribir nada a mano: "Que cambia" (etapa, descripcion, fragmento YAML), "Plan esperado"
(salida de `netops.py --dry-run --prune` contra el nodo en el momento de abrir el PR) y checklist.

Entorno para la API: GITEA_PAT (token con ESCRITURA en el repo). GITEA_URL y GITEA_REPO (owner/repo)
se deducen del remote `origin` si no se indican. SRL_PASSWORD para el plan (def. NokiaSrl1!).
Salida: 0 (hecho, o nada que hacer) · 1 error.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIST_KEYS = ("name", "peer_address")      # claves que identifican elementos de listas en la intencion


def log(msg=""):
    print(msg, flush=True)


def git(*args, check=True):
    res = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        raise SystemExit(f"git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout.strip()


# =============================================================================== fusion de fragmentos
def item_key(item):
    for k in LIST_KEYS:
        if isinstance(item, dict) and k in item:
            return str(item[k])
    return json.dumps(item, sort_keys=True)


def deep_merge(base, frag):
    """Fusiona frag en base: dicts por clave, listas de dicts por name/peer_address (añade los que faltan)."""
    if isinstance(base, dict) and isinstance(frag, dict):
        out = dict(base)
        for k, v in frag.items():
            out[k] = deep_merge(base.get(k), v) if k in base else v
        return out
    if isinstance(base, list) and isinstance(frag, list):
        out = list(base)
        existing = {item_key(x): i for i, x in enumerate(out)}
        for item in frag:
            k = item_key(item)
            if k in existing:
                out[existing[k]] = deep_merge(out[existing[k]], item)
            else:
                out.append(item)
        return out
    return frag


def contains(base, frag):
    """True si todo lo que declara frag ya esta en base (misma regla de identidad que deep_merge)."""
    if isinstance(frag, dict):
        return isinstance(base, dict) and all(k in base and contains(base[k], v) for k, v in frag.items())
    if isinstance(frag, list):
        if not isinstance(base, list):
            return False
        idx = {item_key(x): x for x in base}
        return all(item_key(i) in idx and contains(idx[item_key(i)], i) for i in frag)
    return base == frag


# =============================================================================== etapas
def load(node):
    stages_file = ROOT / "stages" / f"{node}.yml"
    intent_file = ROOT / "intent" / f"{node}.yml"
    if not stages_file.exists():
        raise SystemExit(f"no existe {stages_file}")
    stages = yaml.safe_load(stages_file.read_text()) or {}
    # la referencia es SIEMPRE lo que hay en main (no el arbol de trabajo, que puede estar en otra rama)
    main_intent = git("show", f"main:intent/{node}.yml", check=False) \
        or git("show", f"origin/main:intent/{node}.yml", check=False)
    intent = yaml.safe_load(main_intent or intent_file.read_text()) or {}
    st = sorted(stages.get("stages", []), key=lambda s: s.get("order", 0))
    return st, intent, intent_file


def status(stages, intent):
    return [(s, contains(intent, s.get("intent", {}))) for s in stages]


def stage_for_branch(stages, branch):
    return next((s for s in stages if s.get("branch") == branch), None)


def write_intent(intent_file, intent, stage):
    """Reescribe la intencion conservando la cabecera de comentarios y actualizando su linea de estado."""
    header = []
    for line in intent_file.read_text().splitlines():
        if line.startswith("#"):
            header.append(line)
        else:
            break
    state = f"# Estado actual de este fichero: etapa '{stage['name']}' fusionada (order {stage.get('order', 0)})"
    idx = next((i for i, l in enumerate(header) if l.startswith("# Estado actual")), None)
    if idx is None:
        header.append(state)
    else:
        header[idx] = state
    body = yaml.safe_dump(intent, sort_keys=False, allow_unicode=True, default_flow_style=False)
    intent_file.write_text("\n".join(header) + "\n" + body)


def create_branch(stage, intent, intent_file):
    branch = stage["branch"]
    if git("rev-parse", "--verify", "--quiet", branch, check=False):
        log(f"   la rama {branch} ya existe localmente: etapa ya propuesta (git switch {branch} para verla)")
        git("switch", "-q", branch)
        return branch
    git("switch", "-q", "-c", branch, "main")
    merged = deep_merge(intent, stage.get("intent", {}))
    write_intent(intent_file, merged, stage)
    git("add", str(intent_file.relative_to(ROOT)))
    git("-c", "user.name=netops", "-c", "user.email=netops@localhost", "commit", "-q", "-m", stage["title"])
    log(f"   rama {branch} creada con la etapa '{stage['name']}' (commit local)")
    return branch


# =============================================================================== plan real (netops)
def compute_plan(node):
    """Ejecuta netops --dry-run --prune sobre la intencion del arbol de trabajo. Devuelve (rc, texto_del_plan)."""
    cmd = [sys.executable, str(ROOT / "scripts" / "netops.py"), "--intent", str(ROOT / "intent" / f"{node}.yml"),
           "--dry-run", "--prune"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = (res.stdout or "") + (res.stderr or "")
    return res.returncode, extract_plan(out)


def extract_plan(output):
    """Desde '-- Prerrequisitos' hasta antes de '[dry-run]' / '== BLOQUEADO'; si no se encuentra, la salida entera."""
    lines = output.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("-- Prerrequisitos")), None)
    if start is None:
        return output.strip()
    end = next((i for i, l in enumerate(lines) if l.startswith("[dry-run]") or l.startswith("== BLOQUEADO")), len(lines))
    return "\n".join(lines[start:end]).strip()


def plan_counts(plan_text):
    adds = sum(1 for l in plan_text.splitlines() if l.lstrip().startswith("+ AÑADIR"))
    dels = sum(1 for l in plan_text.splitlines() if l.lstrip().startswith("- ELIMINAR"))
    return adds, dels


# =============================================================================== cuerpo del PR
def pr_body(node, branch, stage, plan_rc, plan_text, commits=None, diffstat=""):
    adds, dels = plan_counts(plan_text)
    sha = git("rev-parse", "--short", "HEAD", check=False) or "?"
    when = time.strftime("%Y-%m-%d %H:%M")
    parts = ["## Qué cambia", ""]
    if stage:
        parts += [f"**Etapa** `{stage['name']}` (order {stage.get('order', 0)}) del rollout de **{node}** · rama `{branch}`", "",
                  stage.get("description", "").strip(), "",
                  "<details><summary>Fragmento de intención fusionado en <code>intent/" + node + ".yml</code></summary>", "",
                  "```yaml", yaml.safe_dump(stage.get("intent", {}), sort_keys=False, allow_unicode=True).rstrip(), "```", "",
                  "</details>"]
    else:
        parts += [f"Cambio en la intención de **{node}** · rama `{branch}`", ""]
        parts += [f"- {c}" for c in (commits or [])] or ["- (sin commits respecto a main)"]
        if diffstat:
            parts += ["", "```text", diffstat, "```"]
    ok = plan_rc == 0
    parts += ["", "## Plan esperado", "",
              f"Calculado contra el nodo real (`netops.py --dry-run --prune`) al abrir el PR, commit `{sha}`, {when}. "
              "El job `validate` lo vuelve a calcular en cada push.", "",
              "```text", plan_text or "(sin salida)", "```", ""]
    parts += ["## Checklist", "",
              f"- [{'x' if ok else ' '}] Prerrequisitos de la etapa comprobados en el nodo "
              + ("(OK)" if ok else "(**BLOQUEADO**: revisa el plan; mergea antes la etapa anterior)"),
              f"- [{'x' if ok and dels == 0 else ' '}] Impacto: {adds} alta(s), {dels} baja(s) en {node}"
              + ("; sin eliminaciones" if dels == 0 else " — **revisa las eliminaciones**"),
              "- [ ] `validate` en verde en el último commit (lo confirma Gitea en los checks)",
              "- [ ] Tras el merge: `deploy` en verde, anotación en Grafana y paneles de la etapa en verde",
              "- [x] Rollback disponible: Revert del PR y merge (el pipeline elimina lo que deja de estar declarado)"]
    return "\n".join(parts) + "\n"


# =============================================================================== API de Gitea
def gitea_cfg():
    remote = git("remote", "get-url", "origin", check=False)
    m = re.match(r"(https?://)(?:[^@/]+@)?([^/]+)/([^/]+)/([^/]+?)(?:\.git)?$", remote or "")
    url = os.environ.get("GITEA_URL") or (f"{m.group(1)}{m.group(2)}" if m else "http://localhost:3030")
    repo = os.environ.get("GITEA_REPO") or (f"{m.group(3)}/{m.group(4)}" if m else "")
    owner_env = os.environ.get("GITEA_OWNER")
    if "/" in repo:
        owner, name = repo.split("/", 1)
    else:
        owner, name = owner_env or "", repo
    pat = os.environ.get("GITEA_PAT") or ""
    if not pat:
        raise SystemExit("falta GITEA_PAT (token con escritura). En local: ponlo en gitea/.env del kit; en CI: secret GITEA_PAT")
    if not (owner and name):
        raise SystemExit("no puedo deducir owner/repo del remote origin: define GITEA_REPO=owner/repo")
    return url.rstrip("/"), owner, name, pat


def api(method, path, payload=None, query=None):
    url, owner, name, pat = gitea_cfg()
    full = f"{url}/api/v1/repos/{owner}/{name}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(full, data=data, method=method,
                                 headers={"Authorization": f"token {pat}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API Gitea {method} {path} -> {e.code}: {e.read().decode(errors='ignore')[:300]}")


def find_open_pr(branch):
    for pr in api("GET", "/pulls", query={"state": "open", "limit": 50}) or []:
        if (pr.get("head") or {}).get("ref") == branch:
            return pr
    return None


def push_branch(branch):
    url, owner, name, pat = gitea_cfg()
    push_url = url.replace("://", f"://{owner}:{pat}@") + f"/{owner}/{name}.git"
    git("push", "-q", "-u", push_url, f"{branch}:{branch}")


def open_pr(node, branch, stage, auto=False):
    existing = find_open_pr(branch)
    if existing:
        log(f"   ya hay un PR abierto para {branch}: {existing.get('html_url')}")
        return 0
    rc, plan = compute_plan(node)
    if stage:
        title = stage["title"]
        body = pr_body(node, branch, stage, rc, plan)
        if auto:
            body = body.replace("## Qué cambia\n\n", "## Qué cambia\n\n_PR propuesto automáticamente por el job `promote` "
                                "tras verificar la etapa anterior en el nodo._\n\n", 1)
    else:
        commits = [c for c in git("log", "--pretty=%s", "main..HEAD", check=False).splitlines() if c]
        title = commits[0] if commits else f"{node}: cambio de intencion ({branch})"
        body = pr_body(node, branch, None, rc, plan, commits, git("diff", "--stat", "main..HEAD", check=False))
    pr = api("POST", "/pulls", {"base": "main", "head": branch, "title": title, "body": body})
    log(f"   PR #{pr.get('number')} abierto: {pr.get('html_url')}")
    if rc != 0:
        log("   aviso: el plan esta BLOQUEADO por prerrequisitos; el PR queda abierto para revision")
    return 0


# =============================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--stage")
    mode.add_argument("--next", action="store_true")
    mode.add_argument("--pr", action="store_true", help="abrir el PR de la rama actual con descripcion y plan generados")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--open-pr", action="store_true")
    ap.add_argument("--print", dest="print_only", action="store_true", help="con --pr: imprimir el cuerpo y salir")
    args = ap.parse_args()

    stages, intent, intent_file = load(args.node)

    if args.pr:
        branch = git("branch", "--show-current")
        if not branch or branch == "main":
            raise SystemExit("--pr requiere estar en una rama distinta de main")
        stage = stage_for_branch(stages, branch)
        if args.print_only:
            rc, plan = compute_plan(args.node)
            commits = [c for c in git("log", "--pretty=%s", "main..HEAD", check=False).splitlines() if c]
            print(pr_body(args.node, branch, stage, rc, plan, commits, git("diff", "--stat", "main..HEAD", check=False)))
            return 0
        log(f"== PR para la rama {branch}" + (f" (etapa '{stage['name']}')" if stage else " (cambio libre)"))
        return open_pr(args.node, branch, stage)

    st = status(stages, intent)
    log(f"== rollout {args.node} :: {len(stages)} etapa(s)")
    for s, done in st:
        log(f"   {'[x]' if done else '[ ]'} {s.get('order', 0):>3}  {s['name']:<10} auto={str(s.get('auto_promote', False)).lower():<5} {s['title']}")
    if args.list:
        return 0

    if args.stage:
        chosen = next((s for s in stages if s["name"] == args.stage), None)
        if not chosen:
            raise SystemExit(f"etapa '{args.stage}' no existe")
        if contains(intent, chosen.get("intent", {})):
            log(f"   la etapa '{args.stage}' ya esta aplicada en la intencion: nada que hacer")
            return 0
    else:
        chosen = next((s for s, done in st if not done), None)
        if not chosen:
            log("   rollout completo: no quedan etapas pendientes")
            return 0
        if args.auto and not chosen.get("auto_promote", False):
            log(f"   siguiente etapa '{chosen['name']}' no es automatica (auto_promote: false): la inicia una persona")
            return 0

    if git("status", "--porcelain"):
        raise SystemExit("hay cambios sin confirmar en el repositorio; limpia el arbol antes de promover")
    log(f"\n-- Proponiendo etapa '{chosen['name']}'")
    branch = create_branch(chosen, intent, intent_file)
    if args.open_pr:
        push_branch(branch)
        log(f"   rama {branch} publicada")
        rc = open_pr(args.node, branch, chosen, auto=True)
        git("switch", "-q", "main")
        return rc
    log(f"   siguiente: revisa el cambio (make diff) y publica con make push (abre el PR documentado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
