# Atajos del kit. Ejecutar desde la raiz del repositorio:  make <target>
LAB_DIR  ?= $(HOME)/srl-telemetry-lab
REPO_DIR ?= $(HOME)/netops-gitops
NODE     ?= leaf3
export LAB_DIR REPO_DIR NODE

.PHONY: help install patch lab-up lab-down gitea-up gitea-down runner traffic-start traffic-stop \
        prep diff push pr-preview promote rollout status reset test secrets \
        slides slides-pdf slides-pptx slides-all slides-watch

# ---- Slides (Marp). Por defecto, imagen Docker oficial (incluye Chromium para PDF/PPTX).
# Sin Docker: make slides MARP="npx -y @marp-team/marp-cli@latest"   (Node >= 18; PDF/PPTX necesitan un navegador)
SLIDES_DIR = slides
SLIDES_MD  = redes-como-codigo
MARP      ?= docker run --rm --init -v "$(CURDIR)/$(SLIDES_DIR):/home/marp/app" -e LANG=C.UTF-8 -e MARP_USER="$$(id -u):$$(id -g)" marpteam/marp-cli:latest
MARP_SRV  ?= docker run --rm --init -it -v "$(CURDIR)/$(SLIDES_DIR):/home/marp/app" -e LANG=C.UTF-8 -p 8080:8080 -p 37717:37717 marpteam/marp-cli:latest

help:
	@echo "Instalacion y laboratorio"
	@echo "  make install        - docker + containerlab + gnmic (1 vez, con internet; detecta proxy)"
	@echo "  make patch          - clona srl-telemetry-lab, aplica los parches y pre-descarga sus imagenes"
	@echo "  make lab-up         - containerlab deploy (fabric + telemetria)"
	@echo "  make lab-down       - containerlab destroy"
	@echo "  make traffic-start  - iperf3 entre clientes en lazo resiliente (el trafico aparece solo cuando hay camino)"
	@echo "  make traffic-stop   - detiene el trafico"
	@echo "Capa GitOps"
	@echo "  make gitea-up       - Gitea en :3030 (necesita gitea/.env)"
	@echo "  make gitea-down     - detiene Gitea"
	@echo "  make runner         - instala/registra act_runner en modo host (label 'lab')"
	@echo "  make secrets        - crea los secrets NETOPS_PAT y SRL_PASSWORD del repo GitOps por API (desde gitea/.env)"
	@echo "Escenario: onboarding de leaf3 (dia 0 -> overlay -> servicio)"
	@echo "  make prep           - leaf3 a dia 0 + trafico + rama de la etapa 'overlay' (commit local)"
	@echo "  make diff           - diff de la intencion en la rama actual frente a main"
	@echo "  make push           - publica la rama actual y ABRE el PR en Gitea ya documentado (descripcion + plan real)"
	@echo "  make pr-preview     - muestra el cuerpo del PR que generaria make push (sin abrirlo)"
	@echo "  make promote        - crea localmente la rama de la siguiente etapa pendiente (si no la abrio el pipeline)"
	@echo "  make rollout        - estado del rollout (etapas aplicadas / pendientes)"
	@echo "  make status         - chequeo de salud de todo"
	@echo "  make reset          - vuelve a dia 0 (repo y nodo) para repetir"
	@echo "Desarrollo"
	@echo "  make test           - pruebas de netops.py y promote.py con gnmic simulado + validacion estatica"
	@echo "Slides (Marp, slides/redes-como-codigo.md -> slides/dist/)"
	@echo "  make slides         - HTML autocontenido"
	@echo "  make slides-pdf     - PDF"
	@echo "  make slides-pptx    - PPTX con notas de orador"
	@echo "  make slides-all     - HTML + PDF + PPTX"
	@echo "  make slides-watch   - servidor con recarga en caliente en http://localhost:8080"

install:        ; bash setup/install-vm.sh
patch:          ; bash setup/patch-lab.sh
lab-up:         ; cd $(LAB_DIR) && sudo containerlab deploy -t st.clab.yml --reconfigure
lab-down:       ; cd $(LAB_DIR) && sudo containerlab destroy -t st.clab.yml --cleanup
traffic-start:  ; bash demo/traffic.sh start
traffic-stop:   ; bash demo/traffic.sh stop
gitea-up:       ; cd gitea && docker compose up -d
gitea-down:     ; cd gitea && docker compose down
runner:         ; bash gitea/runner-setup.sh
secrets:        ; bash demo/secrets.sh
prep:           ; bash demo/prep.sh
diff:           ; cd $(REPO_DIR) && git --no-pager diff main..HEAD -- intent/
push:           ; cd $(REPO_DIR) && git push -u origin "$$(git branch --show-current)" && set -a && . $(CURDIR)/gitea/.env && set +a && python3 scripts/promote.py --node $(NODE) --pr
pr-preview:     ; cd $(REPO_DIR) && python3 scripts/promote.py --node $(NODE) --pr --print
promote:        ; cd $(REPO_DIR) && python3 scripts/promote.py --node $(NODE) --next
rollout:        ; cd $(REPO_DIR) && python3 scripts/promote.py --node $(NODE) --list
status:         ; bash demo/status.sh
reset:          ; bash demo/reset.sh
test:           ; bash tests/run.sh

slides:         ; mkdir -p $(SLIDES_DIR)/dist && cd $(SLIDES_DIR) && $(MARP) $(SLIDES_MD).md --html --allow-local-files -o dist/$(SLIDES_MD).html && echo "-> $(SLIDES_DIR)/dist/$(SLIDES_MD).html"
slides-pdf:     ; mkdir -p $(SLIDES_DIR)/dist && cd $(SLIDES_DIR) && $(MARP) $(SLIDES_MD).md --html --allow-local-files --pdf -o dist/$(SLIDES_MD).pdf && echo "-> $(SLIDES_DIR)/dist/$(SLIDES_MD).pdf"
slides-pptx:    ; mkdir -p $(SLIDES_DIR)/dist && cd $(SLIDES_DIR) && $(MARP) $(SLIDES_MD).md --html --allow-local-files --pptx -o dist/$(SLIDES_MD).pptx && echo "-> $(SLIDES_DIR)/dist/$(SLIDES_MD).pptx"
slides-all:     slides slides-pdf slides-pptx
slides-watch:   ; cd $(SLIDES_DIR) && $(MARP_SRV) -s --html --allow-local-files .
