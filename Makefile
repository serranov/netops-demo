# Atajos del kit. Ejecutar desde la raiz del repositorio:  make <target>
LAB_DIR  ?= $(HOME)/srl-telemetry-lab
REPO_DIR ?= $(HOME)/netops-gitops
NODE     ?= leaf3
export LAB_DIR REPO_DIR NODE

.PHONY: help install patch lab-up lab-down gitea-up gitea-down runner traffic-start traffic-stop \
        prep diff push promote rollout status reset test

help:
	@echo "Instalacion y laboratorio"
	@echo "  make install        - docker + containerlab + gnmic (1 vez, con internet; detecta proxy)"
	@echo "  make patch          - clona srl-telemetry-lab, aplica los parches y pre-descarga sus imagenes"
	@echo "  make lab-up         - containerlab deploy (fabric + telemetria)"
	@echo "  make lab-down       - containerlab destroy"
	@echo "  make traffic-start  - iperf3 entre clientes (anima los dashboards)"
	@echo "  make traffic-stop   - detiene el trafico"
	@echo "Capa GitOps"
	@echo "  make gitea-up       - Gitea en :3030 (necesita gitea/.env)"
	@echo "  make gitea-down     - detiene Gitea"
	@echo "  make runner         - instala/registra act_runner en modo host (label 'lab')"
	@echo "Escenario: onboarding de leaf3 (dia 0 -> overlay -> servicio)"
	@echo "  make prep           - leaf3 a dia 0 + trafico + rama de la etapa 'overlay' (commit local)"
	@echo "  make diff           - diff de la intencion en la rama actual frente a main"
	@echo "  make push           - publica la rama actual en Gitea (abre el PR desde la web)"
	@echo "  make promote        - crea localmente la rama de la siguiente etapa pendiente (si no la abrio el pipeline)"
	@echo "  make rollout        - estado del rollout (etapas aplicadas / pendientes)"
	@echo "  make status         - chequeo de salud de todo"
	@echo "  make reset          - vuelve a dia 0 (repo y nodo) para repetir"
	@echo "Desarrollo"
	@echo "  make test           - pruebas de netops.py y promote.py con gnmic simulado + validacion estatica"

install:        ; bash setup/install-vm.sh
patch:          ; bash setup/patch-lab.sh
lab-up:         ; cd $(LAB_DIR) && sudo containerlab deploy -t st.clab.yml --reconfigure
lab-down:       ; cd $(LAB_DIR) && sudo containerlab destroy -t st.clab.yml --cleanup
traffic-start:  ; cd $(LAB_DIR) && bash traffic.sh start all
traffic-stop:   ; cd $(LAB_DIR) && bash traffic.sh stop all
gitea-up:       ; cd gitea && docker compose up -d
gitea-down:     ; cd gitea && docker compose down
runner:         ; bash gitea/runner-setup.sh
prep:           ; bash demo/prep.sh
diff:           ; cd $(REPO_DIR) && git --no-pager diff main..HEAD -- intent/
push:           ; cd $(REPO_DIR) && git push -u origin "$$(git branch --show-current)"
promote:        ; cd $(REPO_DIR) && python3 scripts/promote.py --node $(NODE) --next
rollout:        ; cd $(REPO_DIR) && python3 scripts/promote.py --node $(NODE) --list
status:         ; bash demo/status.sh
reset:          ; bash demo/reset.sh
test:           ; bash tests/run.sh
