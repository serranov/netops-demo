#!/usr/bin/env python3
"""
promote.py - despliegue por etapas: propone la siguiente etapa de stages/<nodo>.yml como rama (+ PR).

  --node leaf3 --list            estado de cada etapa (aplicada / pendiente) respecto a intent/<nodo>.yml
  --node leaf3 --stage overlay   crea la rama de esa etapa con el fragmento fusionado en la intencion
                                 (commit local; publica con `git push` o `make push`)
  --node leaf3 --next            idem para la primera etapa pendiente
  --auto                         solo actua si la etapa pendiente tiene auto_promote: true (uso en pipeline)
  --open-pr                      ademas empuja la rama y abre el Pull Request en Gitea via API

Variables para --open-pr: GITEA_URL (http://localhost:3030), GITEA_OWNER, GITEA_REPO (owner/repo o repo),
GITEA_PAT (token con permiso de ESCRITURA en el repositorio).
Salida: 0 (hecho, o nada que hacer) · 1 error.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
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
        return branch
    git("switch", "-q", "-c", branch, "main")
    merged = deep_merge(intent, stage.get("intent", {}))
    write_intent(intent_file, merged, stage)
    git("add", str(intent_file.relative_to(ROOT)))
    git("-c", "user.name=netops", "-c", "user.email=netops@localhost", "commit", "-q", "-m", stage["title"])
    log(f"   rama {branch} creada con la etapa '{stage['name']}' (commit local)")
    return branch


def open_pr(stage, branch):
    url = os.environ.get("GITEA_URL", "http://localhost:3030").rstrip("/")
    owner = os.environ.get("GITEA_OWNER") or ""
    repo = os.environ.get("GITEA_REPO") or ""
    pat = os.environ.get("GITEA_PAT") or ""
    if "/" in repo:
        owner, repo = repo.split("/", 1)
    if not (owner and repo and pat):
        raise SystemExit("--open-pr necesita GITEA_OWNER/GITEA_REPO y GITEA_PAT (con escritura)")
    push_url = url.replace("://", f"://{owner}:{pat}@") + f"/{owner}/{repo}.git"
    if git("ls-remote", "--heads", push_url, branch, check=False):
        log(f"   la rama {branch} ya existe en el remoto: etapa ya propuesta, nada que hacer")
        return 0
    git("push", "-q", "-u", push_url, f"{branch}:{branch}")
    log(f"   rama {branch} publicada")
    body = (f"{stage.get('description', '').strip()}\n\n"
            f"**Etapa:** `{stage['name']}` (order {stage.get('order', 0)}) · propuesta automaticamente por el job `promote` "
            f"tras verificar la etapa anterior en el nodo.\n\n"
            "## Fragmento de intencion\n```yaml\n" + yaml.safe_dump(stage.get("intent", {}), sort_keys=False) + "```\n\n"
            "## Checklist\n- [ ] `validate` en verde y plan revisado (prerrequisitos OK, sin eliminaciones inesperadas)\n"
            "- [ ] Impacto conocido / ventana\n- [ ] Rollback: Revert del PR y merge\n")
    data = json.dumps({"base": "main", "head": branch, "title": stage["title"], "body": body}).encode()
    req = urllib.request.Request(f"{url}/api/v1/repos/{owner}/{repo}/pulls", data=data, method="POST",
                                 headers={"Authorization": f"token {pat}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            pr = json.load(r)
        log(f"   PR #{pr.get('number')} abierto: {pr.get('html_url')}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API Gitea {e.code}: {e.read().decode(errors='ignore')[:300]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--stage")
    mode.add_argument("--next", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--open-pr", action="store_true")
    args = ap.parse_args()

    stages, intent, intent_file = load(args.node)
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
        rc = open_pr(chosen, branch)
        git("switch", "-q", "main")
        return rc
    log(f"   siguiente: revisa `git diff main..{branch}` y publica con `git push -u origin {branch}` (o make push)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
