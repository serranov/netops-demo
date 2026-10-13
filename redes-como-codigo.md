---
marp: true
theme: default
size: 16:9
paginate: true
footer: 'Redes como Código · Tecnocrática Tech Day 2026'
title: 'Redes como Código: Aplicación de GitOps en gemelos digitales'
author: Víctor Serrano
description: 'Config-as-code, validación en un gemelo y telemetría en streaming sobre una fabric Nokia SR Linux en Containerlab.'
---

<!--
Deck en Marp (https://marp.app). Renderizar con HTML habilitado:
  npx @marp-team/marp-cli@latest redes-como-codigo.md --html -o redes-como-codigo.html
  npx @marp-team/marp-cli@latest redes-como-codigo.md --html --pdf --allow-local-files
  npx @marp-team/marp-cli@latest redes-como-codigo.md --html --pptx
VS Code (extension "Marp for VS Code"): activar  "markdown.marp.enableHtml": true
Los comentarios HTML que no son directivas son las NOTAS DE ORADOR (modo presentador: tecla P en el HTML).
-->

<style>
/* ===== Tema NetOps: navy dominante, teal apoyo, amber acento ===== */
:root { --navy:#0E2038; --navy2:#16304F; --teal:#17B3A3; --cyan:#38BDF8; --amber:#F5A524; --red:#E4007A;
        --ink:#17233A; --mute:#5B6B82; --line:#D8E2EF; --bg:#F5F8FC; --gray:#9AA7B8; }
section { background: var(--bg); color: var(--ink); font-family: Calibri, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
          padding: 40px 56px 60px; font-size: 22px; line-height: 1.3; justify-content: flex-start; position: relative; }
section.dark { background: var(--navy); color: #fff; }
section h1 { font-size: 40px; font-weight: 800; margin: 2px 0 18px; color: var(--ink); letter-spacing: -0.3px; }
section.dark h1 { color: #fff; }
section h2 { font-size: 24px; font-weight: 600; color: var(--cyan); margin: -6px 0 18px; }
section p { margin: 6px 0; }
.kick { font-size: 13px; letter-spacing: 3px; text-transform: uppercase; font-weight: 700; margin: 0 0 2px; }
.red { color: var(--red); } .teal { color: var(--teal); } .cyan { color: var(--cyan); } .amber { color: var(--amber); } .mute { color: var(--mute); }
.row { display: flex; gap: 18px; align-items: stretch; }
.card { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 16px 22px; }
.card.teal-bg { background: #E7F6F4; border-color: var(--teal); } .card.red-bg { background: #FCE8F2; border-color: var(--red); }
.card.amber-bg { background: #FEF3DC; border-color: var(--amber); }
section.dark .card { background: var(--navy2); border-color: var(--cyan); color: #fff; }
section.dark .card.t { border-color: var(--teal); } section.dark .card.a { border-color: var(--amber); }
.card h3 { margin: 0 0 8px; font-size: 24px; font-weight: 800; }
.card ul { margin: 6px 0 0; padding-left: 22px; } .card li { margin: 5px 0; } ul { margin: 6px 0; }
.callout { background: var(--navy); color: #fff; border-radius: 12px; padding: 14px 22px; margin-top: 18px; font-size: 19px; }
section.dark .callout { background: var(--navy2); }
.chips span { display: inline-block; border: 1px solid var(--teal); border-radius: 999px; padding: 4px 14px; font-size: 14px; font-weight: 700; margin: 6px 8px 0 0; }
section.dark .chips span { background: var(--navy2); color: #fff; }
.num { display: inline-flex; width: 48px; height: 48px; border-radius: 50%; align-items: center; justify-content: center; font-weight: 800; color: #fff; font-size: 22px; }
.steps { display: flex; gap: 12px; } .step { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 16px 12px; text-align: center; }
.step b { display: block; font-size: 21px; margin: 10px 0 6px; } .step small { color: var(--mute); font-size: 15px; line-height: 1.25; display: block; }
.ladder { display: flex; gap: 10px; align-items: flex-end; height: 290px; margin-top: 10px; }
.lv { flex: 1; border-radius: 8px; color: #fff; font-weight: 800; font-size: 26px; text-align: center; padding-top: 8px; }
.lv.g { background: #C8D0DB; color: var(--ink); } .lv.t { background: var(--teal); } .lv.l { background: #8FD3CB; }
.lab { display: flex; gap: 10px; text-align: center; } .lab div { flex: 1; } .lab b { display: block; font-size: 17px; } .lab small { color: var(--mute); font-size: 13px; }
.tags { display: flex; gap: 10px; margin-bottom: 6px; } .tag { flex: 1; text-align: center; border-radius: 999px; padding: 4px 0; font-size: 14px; font-weight: 700; border: 1px solid; }
pre { background: var(--navy) !important; color: #fff; border-radius: 12px; padding: 18px 22px; font-size: 19px; line-height: 1.35; margin: 0; }
pre code { background: transparent; color: inherit; }
.k { color: var(--cyan); } .v { color: var(--amber); }
table { font-size: 20px; width: 100%; border-collapse: collapse; } th, td { padding: 10px 14px; border: 1px solid var(--line); text-align: left; }
th { background: var(--navy); color: #fff; } th.g { background: #0E6E63; } td:first-child { font-weight: 700; }
.big { font-size: 66px; font-weight: 800; line-height: 1; } .fact b { display: block; font-size: 20px; margin-top: 6px; } .fact small { color: var(--mute); font-size: 14px; }
.stage { flex: 1; border-radius: 12px; padding: 16px 20px; display: flex; flex-direction: column; justify-content: flex-end; }
.stage .d { font-size: 13px; letter-spacing: 2px; font-weight: 700; } .stage b { font-size: 28px; display: block; margin: 4px 0; } .stage small { font-size: 15px; }
.gate { width: 56px; align-self: center; border: 2px solid var(--red); color: var(--red); border-radius: 8px; text-align: center; font-size: 12px; font-weight: 800; padding: 10px 0; }
.quote { font-size: 26px; font-style: italic; margin: 10px 0 22px; }
footer { font-size: 12px; color: var(--gray); } section.dark footer { color: #7E92AE; }
section::after { font-size: 12px; color: var(--gray); } section.dark::after { color: #7E92AE; }
</style>

<!-- _class: dark -->
<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="kick cyan">Tecnocrática Tech Day 2026</div>

# <span style="font-size:60px">Redes como Código</span>

## Aplicación de GitOps en gemelos digitales

<p style="color:#AEC2DE;max-width:820px">Config-as-code, validación en un gemelo y telemetría en streaming sobre una fabric Nokia SR Linux en Containerlab.</p>

<div class="chips" style="margin-top:28px"><span>100 % Open Source</span><span>Proxmox VE</span><span>Containerlab</span><span>SR Linux</span><span>gNMI</span><span>Gitea Actions</span></div>

<p style="margin-top:70px;font-weight:700">Víctor Serrano</p>

<svg style="position:absolute;right:56px;top:60px" width="330" height="150" viewBox="0 0 330 150">
  <g stroke="#38BDF8" stroke-opacity=".55" stroke-width="1.2">
    <line x1="100" y1="20" x2="40" y2="130"/><line x1="100" y1="20" x2="130" y2="130"/><line x1="100" y1="20" x2="220" y2="130"/><line x1="100" y1="20" x2="300" y2="130"/>
    <line x1="230" y1="20" x2="40" y2="130"/><line x1="230" y1="20" x2="130" y2="130"/><line x1="230" y1="20" x2="220" y2="130"/><line x1="230" y1="20" x2="300" y2="130"/>
  </g>
  <circle cx="100" cy="20" r="11" fill="#38BDF8"/><circle cx="230" cy="20" r="11" fill="#38BDF8"/>
  <circle cx="40" cy="130" r="11" fill="#17B3A3"/><circle cx="130" cy="130" r="11" fill="#17B3A3"/><circle cx="220" cy="130" r="11" fill="#17B3A3"/><circle cx="300" cy="130" r="11" fill="#17B3A3"/>
</svg>

<!--
[0:00] Bienvenida, 20 s de presentación. Gancho: "¿Cuántos seguís tocando la red por SSH cruzando los dedos?". Anuncia: la mitad de la charla es demo en vivo y el repo se lo llevan en un QR.
-->

---

<div class="kick red">Bloque 1 · El problema</div>

# ¿En qué nivel de autonomía está tu red?

<div class="tags">
  <div class="tag" style="background:#FCE8F2;border-color:#E4007A;color:#A80E5C;flex:2">la mayoría de redes hoy</div>
  <div class="tag" style="background:#E7F6F4;border-color:#17B3A3;color:#0E6E63;flex:2">esta charla, con open source</div>
  <div class="tag" style="background:#fff;border-color:#9AA7B8;color:#5B6B82;flex:2">AIOps (bloque 4)</div>
</div>
<div class="ladder">
  <div class="lv g" style="height:22%">L0</div><div class="lv g" style="height:36%">L1</div>
  <div class="lv t" style="height:50%">L2</div><div class="lv t" style="height:64%">L3</div>
  <div class="lv l" style="height:78%">L4</div><div class="lv l" style="height:92%">L5</div>
</div>
<div class="lab" style="margin-top:8px">
  <div><b>Manual</b><small>CLI / SSH</small></div><div><b>Asistida</b><small>scripts, SNMP</small></div>
  <div><b>Parcial</b><small>IaC + telemetría</small></div><div><b>Condicional</b><small>GitOps + validación</small></div>
  <div><b>Alta</b><small>closed-loop + IA</small></div><div><b>Autónoma</b><small>agentes</small></div>
</div>
<p class="mute" style="font-size:13px;font-style:italic;margin-top:10px">Niveles de autonomía según TM Forum (IG1252)</p>

<!--
[0:30 · 1 min] Escalera de TM Forum. La mayoría de redes de producción siguen en L0/L1: cambios por CLI, monitorización por SNMP. Las apps llevan años en L3. Hoy subimos la red a L2/L3 con herramientas libres; la IA (L4/L5) la dejamos para el final.
-->

---

<div class="kick red">Bloque 1 · El problema</div>

# La paradoja actual

<div class="row">
  <div class="card teal-bg"><h3 style="color:#0E6E63">Apps &amp; Cloud</h3>
    <ul><li>Infraestructura como código</li><li>GitOps: Git es la fuente de verdad</li><li>CI/CD con validación previa</li><li>Observabilidad y tracing en tiempo real</li></ul></div>
  <div class="card red-bg"><h3 style="color:#A80E5C">Redes</h3>
    <ul><li>Configuración manual por CLI / SSH</li><li>Dispositivos <em>snowflake</em></li><li>SNMP: polling reactivo</li><li>Cambios a ciegas, sin validación previa</li></ul></div>
</div>
<div class="callout"><b>La red frena la agilidad del resto de la infraestructura.</b> No es culpa del equipo de redes: es falta de tooling y de metodología.</div>

<!--
[1:30 · 1,5 min] Dos columnas. Insiste: no culpar al ingeniero de red; el problema es de herramientas y proceso. La red es el cuello de botella del CI/CD del negocio.
-->

---

<div class="kick red">Bloque 1 · El problema</div>

# Lo que cuesta hacerlo a mano

<div class="row">
  <div class="card"><span class="num" style="background:#E4007A">!</span><h3 style="margin-top:12px">¿Quién cambió qué?</h3><p class="mute">Sin trazabilidad: la config es texto no estructurado y nadie firma los cambios.</p></div>
  <div class="card"><span class="num" style="background:#F5A524">!</span><h3 style="margin-top:12px">Rollback = volver a teclear</h3><p class="mute">No hay un estado autoritativo al que regresar.</p></div>
  <div class="card"><span class="num" style="background:#7E92AE">!</span><h3 style="margin-top:12px">MTTR alto</h3><p class="mute">Se descubre tarde (polling) y se diagnostica a mano.</p></div>
</div>
<div class="callout"><b class="amber">Las operaciones de red deben ser deterministas.</b> Hace falta una fuente de verdad, un modelo de datos y una forma de validar antes de tocar producción.</div>

<!--
[3:00 · 1,5 min] Tres síntomas y una causa: configuración como texto sin modelo ni estado autoritativo. Planta la promesa: "todo esto se arregla hoy, con open source, y lo vais a ver corriendo". Fin del bloque 1 en el minuto 5.
-->

---

<!-- _class: dark -->

<div class="kick cyan">Bloque 2 · La solución</div>

# Tres pilares, un bucle cerrado

<div class="row" style="margin-top:16px">
  <div class="card t"><span class="num" style="background:#17B3A3;color:#17233A">1</span><h3 style="margin-top:14px">Red como código</h3><p style="color:#CFE0F2">Git es la fuente de verdad</p></div>
  <div class="card a"><span class="num" style="background:#F5A524;color:#17233A">2</span><h3 style="margin-top:14px">Gemelo digital</h3><p style="color:#CFE0F2">Validar antes de desplegar</p></div>
  <div class="card"><span class="num" style="background:#38BDF8;color:#17233A">3</span><h3 style="margin-top:14px">Telemetría streaming</h3><p style="color:#CFE0F2">La red cuenta lo que pasa</p></div>
</div>
<p class="cyan" style="text-align:center;font-style:italic;margin-top:34px;font-size:20px">PR → validación en el gemelo → merge → deploy por gNMI → telemetría confirma el efecto</p>

<!--
[5:00 · 1 min] Mapa del bloque 2: tres pilares y cómo se encadenan en un bucle cerrado. Cada uno tiene su slide.
-->

---

<div class="kick teal">Pilar 1 · Red como código</div>

# La intención vive en Git, no en el router

<div class="row">
<div style="flex:1.1">
<pre><code><span class="mute" style="font-size:14px">intent/leaf3.yml</span>
<span class="k">bgp:</span>
<span class="k">  groups:</span>
  - name: iBGP-overlay
    peer_as: 100
    afi_safi: {evpn: enable}
<span class="k">    neighbors:</span>
<span class="v">    - peer_address: 10.0.2.1</span>
<span class="v">    - peer_address: 10.0.2.2</span></code></pre>
</div>
<div style="flex:1;padding-left:8px">
<div class="kick teal">Qué quiero</div>
<p>Declarativo, mínimo, revisable en un Pull Request. El script rellena el resto.</p>
<div class="kick red" style="margin-top:18px">Cómo se aplica</div>
<p>Reconciliación idempotente contra el estado real del nodo, en una transacción.</p>
<div class="chips"><span>gNMIc set</span><span style="border-color:#38BDF8">Ansible</span><span style="border-color:#F5A524">Nornir</span></div>
<p class="mute" style="font-style:italic;font-size:16px;margin-top:22px">→ modelo YANG de SR Linux: lo que configuras es lo que consultas</p>
</div>
</div>

<!--
[6:00 · 2 min] Intención vs estado. El YAML es el cambio real de la demo (etapa overlay). Opciones para empujar: gnmic set (nativo gNMI/YANG), Ansible, Nornir; en la demo usamos gnmic. Remata: en SR Linux el mismo modelo YANG sirve para configurar y para observar.
-->

---

<div class="kick amber">Pilar 2 · Gemelo digital</div>

# Git → validación → despliegue

<div class="steps">
  <div class="step"><span class="num" style="background:#17B3A3;width:60px;height:60px;font-size:28px">1</span><b>Pull Request</b><small>git push de la intención</small></div>
  <div class="step"><span class="num" style="background:#38BDF8;width:60px;height:60px;font-size:28px">2</span><b>Validación</b><small>el runner lee el nodo (gemelo en Containerlab) y calcula el plan</small></div>
  <div class="step"><span class="num" style="background:#F5A524;width:60px;height:60px;font-size:28px">3</span><b>Merge</b><small>revisión humana: plan y prerrequisitos a la vista</small></div>
  <div class="step"><span class="num" style="background:#17B3A3;width:60px;height:60px;font-size:28px">4</span><b>Deploy</b><small>gnmic set en una transacción + verificación</small></div>
</div>
<div class="callout"><b class="cyan">El gemelo no es solo para la charla:</b> es el entorno de validación de cada cambio. Alternativa <em>pull-based</em>: ArgoCD / Flux reconcilian desde Git.</div>

<!--
[8:00 · 2 min] El flujo que luego verán en la demo. Insistir en que la validación lee el nodo REAL (no solo lint) y que el merge es una decisión humana con el plan delante. Mencionar pull-based (ArgoCD/Flux) sin demostrarlo.
-->

---

<div class="kick amber">Pilar 2 · Gemelo digital</div>

# Despliegue por etapas con prerrequisitos

<div class="row" style="align-items:flex-end;height:300px">
  <div class="stage" style="background:#C8D0DB;color:#17233A;height:58%"><span class="d">DÍA 0</span><b>Underlay</b><small>eBGP a los spines · bootstrap, fuera de GitOps</small></div>
  <div class="gate">gate</div>
  <div class="stage" style="background:#17B3A3;color:#fff;height:76%"><span class="d">DÍA 1</span><b>Overlay</b><small>iBGP EVPN a los route reflectors</small></div>
  <div class="gate">gate</div>
  <div class="stage" style="background:#F5A524;color:#17233A;height:94%"><span class="d">DÍA 2</span><b>Servicio</b><small>mac-vrf · VNI · acceso del servidor</small></div>
</div>
<div class="row" style="text-align:center;font-weight:700;margin-top:8px"><div style="flex:1"></div><div style="width:56px"></div><div style="flex:1">PR manual</div><div style="width:56px"></div><div style="flex:1">PR automático</div></div>
<p class="mute" style="font-style:italic;font-size:15px;margin-top:6px">gate = la validación comprueba en el nodo que la etapa anterior está <em>established</em> antes de dejar mergear la siguiente</p>

<!--
[10:00 · 1,5 min] Onboarding de un leaf nuevo = tres días. Cada etapa es un PR con su plan, verificación y rollback. La etapa 2 la propone el pipeline cuando la 1 está verificada (promoción automática, aprobación humana). Las gates evitan configurar el servicio sin overlay.
-->

---

<div class="kick cyan">Pilar 3 · Telemetría</div>

# Streaming (gNMI) frente a polling (SNMP)

| | SNMP | <span style="color:#fff">gNMI / gRPC</span> |
|---|---|---|
| Modelo | Pull: el colector pregunta | Push: el nodo publica (subscribe) |
| Datos | MIBs jerárquicas, parciales | YANG: 100 % del estado y la config |
| Latencia | Intervalos de minutos | Sub-segundo, on-change o sample |
| Coste en el equipo | CPU alta en cada poll | Eficiente, una sesión gRPC |

<p class="mute" style="font-style:italic;font-size:15px;margin-top:14px">Lo que el público verá en Grafana lo marca el intervalo de scrape (2 s en el lab): "en segundos, sin polling".</p>

<!--
[11:30 · 1,5 min] Cambio de paradigma: el nodo publica; el modelo YANG es el mismo que configuramos. Cuidado con prometer milisegundos: el extremo a extremo son segundos.
-->

---

<div class="kick cyan">Pilar 3 · Telemetría</div>

# El stack, todo open source

<div class="row" style="align-items:center;text-align:center;font-weight:800;font-size:24px">
  <div class="card" style="background:#E4007A;color:#fff;border:0">SR Linux<small style="display:block;font-weight:400;font-size:15px">YANG · gNMI</small></div><div>→</div>
  <div class="card" style="background:#17B3A3;color:#fff;border:0">gNMIc<small style="display:block;font-weight:400;font-size:15px">colector gNMI</small></div><div>→</div>
  <div class="card" style="background:#F5A524;border:0">Prometheus<small style="display:block;font-weight:400;font-size:15px">TSDB</small></div><div>→</div>
  <div class="card" style="background:#38BDF8;border:0">Grafana<small style="display:block;font-weight:400;font-size:15px">dashboards</small></div>
</div>
<p class="mute" style="text-align:center;margin-top:14px;font-size:16px">Logs: Alloy → Loki &nbsp;·&nbsp; Weathermap: FlowPanel &nbsp;·&nbsp; El mismo Prometheus/Grafana que ya usa tu equipo de sistemas</p>
<div class="callout"><b class="amber">Correlar cambio y efecto.</b> Cada deploy deja una anotación en Grafana: la línea vertical en el panel es el commit que acaba de mergearse. <span style="color:#CFE0F2">Paneles por etapa: underlay · overlay · servicio · MACs · tráfico del servidor.</span></div>

<!--
[13:00 · 2 min] Es el srl-telemetry-lab de srl-labs tal cual, con dos parches: estado de sesión por vecino BGP y un dashboard por etapas. Anotaciones: el pipeline marca en Grafana cada deploy, así se ve causa y efecto. Fin del bloque 2 en el minuto 15.
-->

---

<!-- _class: dark -->

<div class="kick amber">Bloque 3 · Demo en vivo</div>

# Llega un rack nuevo de Proxmox

## Onboarding de leaf3: de día 0 a servicio, por Git

<div class="row">
<div style="flex:1.25">
<svg width="560" height="290" viewBox="0 0 560 290" style="margin-top:-6px">
  <g stroke="#38BDF8" stroke-opacity=".6" stroke-width="1.5">
    <line x1="170" y1="35" x2="60" y2="150"/><line x1="170" y1="35" x2="280" y2="150"/><line x1="170" y1="35" x2="500" y2="150"/>
    <line x1="390" y1="35" x2="60" y2="150"/><line x1="390" y1="35" x2="280" y2="150"/><line x1="390" y1="35" x2="500" y2="150"/>
  </g>
  <g font-family="Calibri, Arial" font-size="14" font-weight="700" text-anchor="middle">
    <rect x="120" y="12" width="100" height="40" rx="6" fill="#38BDF8"/><text x="170" y="38" fill="#17233A">spine1</text>
    <rect x="340" y="12" width="100" height="40" rx="6" fill="#38BDF8"/><text x="390" y="38" fill="#17233A">spine2</text>
    <rect x="10" y="130" width="100" height="40" rx="6" fill="#17B3A3"/><text x="60" y="156" fill="#fff">leaf1</text>
    <rect x="230" y="130" width="100" height="40" rx="6" fill="#17B3A3"/><text x="280" y="156" fill="#fff">leaf2</text>
    <rect x="450" y="130" width="100" height="40" rx="6" fill="#F5A524"/><text x="500" y="156" fill="#17233A">leaf3</text>
    <line x1="60" y1="170" x2="60" y2="235" stroke="#7E92AE" stroke-width="1.5"/><line x1="280" y1="170" x2="280" y2="235" stroke="#7E92AE" stroke-width="1.5"/>
    <line x1="500" y1="170" x2="500" y2="235" stroke="#F5A524" stroke-width="2" stroke-dasharray="6 4"/>
    <rect x="5" y="235" width="110" height="40" rx="6" fill="#16304F" stroke="#7E92AE"/><text x="60" y="261" fill="#fff" font-size="13">client1</text>
    <rect x="225" y="235" width="110" height="40" rx="6" fill="#16304F" stroke="#7E92AE"/><text x="280" y="261" fill="#fff" font-size="13">client2</text>
    <rect x="435" y="235" width="130" height="40" rx="6" fill="#16304F" stroke="#F5A524" stroke-width="2"/><text x="500" y="261" fill="#fff" font-size="13">client3 · Proxmox</text>
  </g>
</svg>
</div>
<div style="flex:1">
  <div class="card" style="border-color:#7E92AE;padding:12px 18px;margin-bottom:10px"><span class="kick" style="color:#7E92AE">Día 0</span><b style="font-size:20px;display:block">underlay eBGP</b><small style="color:#CFE0F2">ya está (bootstrap)</small></div>
  <div class="card t" style="padding:12px 18px;margin-bottom:10px"><span class="kick teal">Día 1</span><b style="font-size:20px;display:block">overlay iBGP EVPN</b><small style="color:#CFE0F2">PR #1 · lo abro yo</small></div>
  <div class="card a" style="padding:12px 18px"><span class="kick amber">Día 2</span><b style="font-size:20px;display:block">servicio vrf-1 / VNI 1</b><small style="color:#CFE0F2">PR #2 · lo abre el pipeline</small></div>
</div>
</div>
<p style="color:#9FB4D0;font-style:italic;font-size:15px;margin-top:6px">Qué observar: sesiones BGP · vrf-1 UP · MACs · tráfico de client3 en leaf3 e1-1</p>

<!--
[15:00 · 1 min] Escenario: leaf3 es el leaf nuevo del rack de Proxmox (client3 = ese servidor). Tiene underlay y nada más. Vamos a adherirlo al overlay y al servicio con dos PRs. Luego cambia a pantalla de demo: make status, Grafana con día 1 en rojo y vrf-1 ausente.
-->

---

<!-- _class: dark -->

<div class="kick amber">Bloque 3 · Demo en vivo</div>

# Lo que vais a ver

<div class="row" style="margin-bottom:14px">
  <div class="card t"><span class="num" style="background:#17B3A3;color:#17233A;width:36px;height:36px;font-size:17px">1</span> <b>make push</b><br><small style="color:#CFE0F2">rama + PR #1 documentado</small></div>
  <div class="card"><span class="num" style="background:#38BDF8;color:#17233A;width:36px;height:36px;font-size:17px">2</span> <b>validate</b><br><small style="color:#CFE0F2">prerrequisito día 0 + plan</small></div>
  <div class="card a"><span class="num" style="background:#F5A524;color:#17233A;width:36px;height:36px;font-size:17px">3</span> <b>merge</b><br><small style="color:#CFE0F2">decisión humana</small></div>
  <div class="card t"><span class="num" style="background:#17B3A3;color:#17233A;width:36px;height:36px;font-size:17px">4</span> <b>deploy</b><br><small style="color:#CFE0F2">gnmic set · established</small></div>
</div>
<div class="row">
  <div class="card"><span class="num" style="background:#38BDF8;color:#17233A;width:36px;height:36px;font-size:17px">5</span> <b>promote</b><br><small style="color:#CFE0F2">abre PR #2 solo</small></div>
  <div class="card a"><span class="num" style="background:#F5A524;color:#17233A;width:36px;height:36px;font-size:17px">6</span> <b>validate</b><br><small style="color:#CFE0F2">gate: overlay OK</small></div>
  <div class="card t"><span class="num" style="background:#17B3A3;color:#17233A;width:36px;height:36px;font-size:17px">7</span> <b>merge + deploy</b><br><small style="color:#CFE0F2">vrf-1 UP · MACs</small></div>
  <div class="card"><span class="num" style="background:#38BDF8;color:#17233A;width:36px;height:36px;font-size:17px">8</span> <b>Grafana</b><br><small style="color:#CFE0F2">tráfico en leaf3 e1-1</small></div>
</div>
<p class="cyan" style="text-align:center;font-style:italic;font-size:20px;margin-top:26px">Dos pull requests. Cero comandos en el equipo.</p>

<!--
[16:00 · 30 s] Ocho pasos en una pantalla; luego a la terminal y a Gitea/Grafana. Demo: 8-9 min. Si el pipeline tarda, narra sobre el GIF de respaldo. Nunca sacrifiques el final (vrf-1 UP + tráfico).
-->

---

<div class="kick amber">Bloque 3 · Demo en vivo</div>

# Qué acaba de pasar

<p class="quote">“Cambié código en Git, hice push y la red se reconfiguró sola, mostrando su estado actualizado en pocos segundos.”</p>
<div class="row">
  <div class="card fact"><span class="big teal">2</span><b>pull requests</b><small>uno escrito por mí, otro por el pipeline</small></div>
  <div class="card fact"><span class="big red">0</span><b>comandos en el equipo</b><small>todo por gNMI, en transacciones</small></div>
  <div class="card fact"><span class="big amber">3</span><b>verificaciones</b><small>underlay · sesiones EVPN · servicio UP</small></div>
</div>

<!--
[24:30 · 30 s] Cierre del bloque 3 con la frase-resumen y tres números. Y recuerda: revertir cualquiera de los PRs deshace esa etapa en la red (prune). Fin del bloque 3 en el minuto 25.
-->

---

<div class="kick teal">Bloque 4 · El futuro</div>

# Hacia dónde va la industria

<div class="row">
  <div class="card teal-bg"><h3 style="color:#0E6E63">Kubenet <small class="mute" style="font-weight:400;font-size:14px">open source</small></h3>
    <ul><li>Kubernetes como motor de automatización</li><li>CRDs → YANG, reconciliación continua</li><li>GitOps nativo (Argo/Flux) por diseño</li><li class="mute"><em>Impulsado por Nokia; joven: para aprender y prototipar</em></li></ul></div>
  <div class="card red-bg"><h3 style="color:#A80E5C">Nokia EDA <small class="mute" style="font-weight:400;font-size:14px">comercial</small></h3>
    <ul><li>Intent-based, sobre Kubernetes</li><li>Digital Twin embebido con nodos simulados</li><li>Observabilidad y remediación integradas</li><li class="mute"><em>No es open source; corre sin licencia en modo Digital Twin</em></li></ul></div>
</div>
<p style="text-align:center;font-weight:700;margin-top:22px">Los mismos patrones de hoy (intención, gemelo, telemetría), industrializados.</p>

<!--
[25:00 · 1,5 min] Evenhanded: ni vender ni despreciar. Kubenet = los mismos conceptos en open source sobre k8s, aún joven. EDA = la versión producto, con gemelo integrado. Lo que hemos hecho hoy es la base conceptual de ambos.
-->

---

<div class="kick teal">Bloque 4 · El futuro</div>

# ¿Y la IA? Necesita una red determinista

<div class="row">
  <div class="card"><b class="red">Un agente de IA falla cuando razona sobre…</b>
    <ul><li>CLI y config como texto no estructurado</li><li>telemetría con esquemas distintos por vendor</li><li>ningún estado de referencia autoritativo</li></ul></div>
  <div class="card teal-bg"><b style="color:#0E6E63">Lo que acabamos de construir le da…</b>
    <ul><li>intención versionada en Git (fuente de verdad)</li><li>modelo YANG + gNMI: datos estructurados</li><li>un gemelo donde probar antes de actuar</li></ul></div>
</div>
<div class="callout"><b class="amber">Los LLM son probabilísticos; las operaciones de red deben ser deterministas.</b> GitOps + telemetría es el suelo (L2–L3) sobre el que la IA puede subir a L4–L5 sin alucinar la red.</div>

<!--
[26:30 · 1,5 min] Cierra el círculo con la escalera de la slide 2: sin fuente de verdad ni datos estructurados, un agente de IA solo automatiza el caos. Lo de hoy no compite con AIOps: es su prerrequisito.
-->

---

<!-- _class: dark -->

<div class="kick cyan">Conclusiones</div>

# Sense · Think · Act

<div class="row" style="align-items:center">
  <div class="card a"><h3 class="amber">Sense</h3><b style="font-size:21px">Telemetría gNMI</b><br><small style="color:#CFE0F2">la red publica su estado</small></div><div style="font-size:30px;color:#7E92AE">→</div>
  <div class="card"><h3 class="cyan">Think</h3><b style="font-size:21px">Validación en el gemelo</b><br><small style="color:#CFE0F2">plan y prerrequisitos</small></div><div style="font-size:30px;color:#7E92AE">→</div>
  <div class="card t"><h3 class="teal">Act</h3><b style="font-size:21px">Deploy desde Git</b><br><small style="color:#CFE0F2">transacción + verificación</small></div>
</div>
<p style="font-size:24px;font-weight:800;margin-top:30px">Código + telemetría + GitOps = bucle cerrado funcional.</p>
<p class="cyan" style="font-size:20px;font-style:italic">La red deja de ser el obstáculo y pasa a integrarse en el pipeline del negocio.</p>

<!--
[28:00 · 1 min] Sense/think/act = telemetría / validación / deploy. Tres pilares, un bucle cerrado. Y todo sobre un Proxmox modesto, sin licencias.
-->

---

<!-- _class: dark -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# <span style="font-size:60px">Gracias</span>

<p class="cyan" style="font-size:22px">Todo el laboratorio, open source y reproducible</p>

<div class="row" style="align-items:center;margin-top:30px">
  <div style="width:150px;height:150px;background:#fff;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#0E2038;font-weight:800;font-size:28px;flex:none">QR</div>
  <div style="padding-left:10px">
    <b style="font-size:24px">github.com/serranov/netops-demo</b><br>
    <span style="color:#AEC2DE;font-size:16px">Containerlab · SR Linux · gNMIc · Prometheus · Grafana · Gitea Actions</span><br>
    <span style="color:#AEC2DE;font-size:16px">Sobre un Proxmox modesto, sin gastar un euro en licencias.</span>
  </div>
</div>
<p style="color:#7E92AE;margin-top:60px">Víctor Serrano · Tecnocrática Tech Day 2026</p>

<!--
[29:00] Deja esta slide fija durante las preguntas. Sustituye el placeholder QR por el QR real del repo (por ejemplo: <img src="qr.png" width="150">).
-->
