---
marp: true
theme: default
size: 16:9
paginate: true
footer: 'Redes como Código · Tecnocrática Tech Day 2026'
title: 'Redes como Código: Aplicación de GitOps en gemelos digitales'
author: Víctor Serrano Bazán - Consulting System Engineer @ Nokia
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
          padding: 40px 56px 60px; font-size: 25px; line-height: 1.3; justify-content: flex-start; position: relative; }
section.dark { background: var(--navy); color: #fff; }
section h1 { font-size: 44px; font-weight: 800; margin: 2px 0 18px; color: var(--ink); letter-spacing: -0.3px; }
section.dark h1 { color: #fff; }
section h2 { font-size: 24px; font-weight: 600; color: var(--cyan); margin: -6px 0 18px; }
section p { margin: 6px 0; }
.kick { font-size: 15px; letter-spacing: 3px; text-transform: uppercase; font-weight: 700; margin: 0 0 2px; }
.red { color: var(--red); } .teal { color: var(--teal); } .cyan { color: var(--cyan); } .amber { color: var(--amber); } .mute { color: var(--mute); }
.row { display: flex; gap: 18px; align-items: stretch; }
.card { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 16px 22px; }
.card.teal-bg { background: #E7F6F4; border-color: var(--teal); } .card.red-bg { background: #FCE8F2; border-color: var(--red); }
.card.amber-bg { background: #FEF3DC; border-color: var(--amber); }
section.dark .card { background: var(--navy2); border-color: var(--cyan); color: #fff; }
section.dark .card.t { border-color: var(--teal); } section.dark .card.a { border-color: var(--amber); }
.card h3 { margin: 0 0 8px; font-size: 27px; font-weight: 800; }
.card ul { margin: 6px 0 0; padding-left: 22px; } .card li { margin: 10px 0; } ul { margin: 6px 0; }
.callout { background: var(--navy); color: #fff; border-radius: 12px; padding: 18px 26px; margin-top: 26px; font-size: 22px; }
section.dark .callout { background: var(--navy2); }
.chips span { display: inline-block; border: 1px solid var(--teal); border-radius: 999px; padding: 5px 16px; font-size: 16px; font-weight: 700; margin: 12px 8px 0 0; }
section.dark .chips span { background: var(--navy2); color: #fff; }
.num { display: inline-flex; width: 48px; height: 48px; border-radius: 50%; align-items: center; justify-content: center; font-weight: 800; color: #fff; font-size: 22px; }
.steps { display: flex; gap: 12px; } .step { flex: 1; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 24px 14px; text-align: center; }
.step b { display: block; font-size: 24px; margin: 14px 0 8px; } .step small { color: var(--mute); font-size: 18px; line-height: 1.25; display: block; }
.ladder { display: flex; gap: 10px; align-items: flex-end; height: 290px; margin-top: 10px; }
.lv { flex: 1; border-radius: 8px; color: #fff; font-weight: 800; font-size: 26px; text-align: center; padding-top: 8px; }
.lv.g { background: #C8D0DB; color: var(--ink); } .lv.t { background: var(--teal); } .lv.l { background: #8FD3CB; }
.lab { display: flex; gap: 10px; text-align: center; } .lab div { flex: 1; } .lab b { display: block; font-size: 17px; } .lab small { color: var(--mute); font-size: 13px; }
.tags { display: flex; gap: 10px; margin-bottom: 6px; } .tag { flex: 1; text-align: center; border-radius: 999px; padding: 4px 0; font-size: 14px; font-weight: 700; border: 1px solid; }
pre { background: var(--navy) !important; color: #fff; border-radius: 12px; padding: 22px 26px; font-size: 22px; line-height: 1.35; margin: 0; }
pre code { background: transparent; color: inherit; }
.k { color: var(--cyan); } .v { color: var(--amber); }
table { font-size: 24px; width: 100%; border-collapse: collapse; } th, td { padding: 16px 18px; border: 1px solid var(--line); text-align: left; }
th { background: var(--navy); color: #fff; } th.g { background: #0E6E63; } td:first-child { font-weight: 700; }
.big { font-size: 88px; font-weight: 800; line-height: 1; } .fact b { display: block; font-size: 25px; margin-top: 8px; } .fact small { color: var(--mute); font-size: 18px; }
.stage { flex: 1; border-radius: 12px; padding: 16px 20px; display: flex; flex-direction: column; justify-content: flex-end; }
.stage .d { font-size: 13px; letter-spacing: 2px; font-weight: 700; } .stage b { font-size: 28px; display: block; margin: 4px 0; } .stage small { font-size: 15px; }
.gate { width: 56px; align-self: center; border: 2px solid var(--red); color: var(--red); border-radius: 8px; text-align: center; font-size: 12px; font-weight: 800; padding: 10px 0; }
.quote { font-size: 32px; font-style: italic; margin: 20px 0 34px; }
footer { font-size: 12px; color: var(--gray); } section.dark footer { color: #7E92AE; }
section::after { font-size: 12px; color: var(--gray); } section.dark::after { color: #7E92AE; }
</style>

<!-- _class: dark -->
<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="kick cyan">Tecnocrática Tech Day 2026</div>

# <span style="font-size:60px">Redes como Código</span>

## Aplicación de mecanismos GitOps sobre Gemelos Digitales

<div class="chips" style="margin-top:28px"><span>Proxmox VE</span><span>Containerlab</span><span>Telemetría</span></div>

<p style="margin-top:70px;font-weight:700">Víctor Serrano Bazán - Consulting System Engineer @ Nokia</p>

<svg style="position:absolute;right:56px;top:60px" width="330" height="150" viewBox="0 0 330 150">
  <g stroke="#38BDF8" stroke-opacity=".55" stroke-width="1.2">
    <line x1="100" y1="20" x2="40" y2="130"/><line x1="100" y1="20" x2="130" y2="130"/><line x1="100" y1="20" x2="220" y2="130"/><line x1="100" y1="20" x2="300" y2="130"/>
    <line x1="230" y1="20" x2="40" y2="130"/><line x1="230" y1="20" x2="130" y2="130"/><line x1="230" y1="20" x2="220" y2="130"/><line x1="230" y1="20" x2="300" y2="130"/>
  </g>
  <circle cx="100" cy="20" r="11" fill="#38BDF8"/><circle cx="230" cy="20" r="11" fill="#38BDF8"/>
  <circle cx="40" cy="130" r="11" fill="#17B3A3"/><circle cx="130" cy="130" r="11" fill="#17B3A3"/><circle cx="220" cy="130" r="11" fill="#17B3A3"/><circle cx="300" cy="130" r="11" fill="#17B3A3"/>
</svg>

<!--
[00:00 · 1min] Bienvenida y presentación.
Gancho: "¿Cuántos seguís tocando la red por SSH cruzando los dedos?".
División por bloques.
Anuncio: Un tercio de la charla es demo en vivo y el repo se lo llevan en un QR.
-->

---

<div class="kick red">Bloque 1 · El problema</div>

# ¿En qué nivel de autonomía está tu red?

<div class="ladder">
  <div class="lv g" style="height:22%">L0</div><div class="lv g" style="height:36%">L1</div>
  <div class="lv t" style="height:50%">L2</div><div class="lv t" style="height:64%">L3</div>
  <div class="lv l" style="height:78%">L4</div><div class="lv l" style="height:92%">L5</div>
</div>
<div class="lab" style="margin-top:8px">
  <div><b>Manual</b><small>CLI / SSH</small></div><div><b>Asistida</b><small>Scripts, SNMP</small></div>
  <div><b>Parcial</b><small>IaC + Telemetría</small></div><div><b>Condicional</b><small>GitOps + Validación</small></div>
  <div><b>Alta</b><small>Asistida por agentes IA</small></div><div><b>Autónoma</b><small>Operada por agentes IA</small></div>
</div>
<p class="mute" style="font-size:13px;font-style:italic;margin-top:10px">Niveles de autonomía según TM Forum (IG1252)</p>
<div class="callout" style="text-align:center"> La mayoría de las redes se encuentran en los niveles inferiores.</div>

<!--
[01:00 · 2min] La mayoría de redes de producción siguen en L0/L1: cambios por CLI, monitorización por SNMP. Las apps llevan años en L3. Hoy subimos la red a L2/L3 con herramientas libres; la IA (L4/L5) la dejamos para el final.
Gancho de actualidad: en el OCP Global Summit 2026 (San José, 12-15 oct) la palabra de las keynotes fue "agentic" (AMD, Arm, NVIDIA: "infraestructura abierta para la IA agéntica"). Pero, cuando se habla de redes, siempre se mencionan gNMI, YANG, emulación y validación: los peldaños L2-L3 de esta escalera. Nadie salta a L5 sin pasar por aquí.
-->

---

<div class="kick red">Bloque 1 · El problema</div>

# Lo que cuesta hacerlo a mano

<div class="row">
  <div class="card"><span class="num" style="background:#E4007A">!</span><h3 style="margin-top:12px">¿Quién cambió qué?</h3><p class="mute">Sin trazabilidad: los cambios se aplican manualmente por CLI / SSH y no siempre se firman.</p></div>
  <div class="card"><span class="num" style="background:#F5A524">!</span><h3 style="margin-top:12px">Rollback = volver a teclear</h3><p class="mute">Los cambios se aplican tras validarlos en entornos mínimos, y no hay un estado autoritativo al que regresar.</p></div>
  <div class="card"><span class="num" style="background:#7E92AE">!</span><h3 style="margin-top:12px">MTTR alto</h3><p class="mute">Las incidencias se descubren tarde y se diagnostican a mano</p></div>
</div>
<div class="callout" style="text-align:center"><b class="amber">Las operaciones de red deben ser ágiles y deterministas:</b> Hace falta una fuente de verdad, un modelo de datos y una forma de validar antes de tocar producción.</div>

<!--
[03:00 · 2min] La red es el cuello de botella del CI/CD del negocio.
Contexto: desarrollo y sistemas ya adoptaron IaC, observabilidad en tiempo real y GitOps; la red sigue con CLI, SNMP y cambios sin validación previa.
Tres síntomas y una causa: Configuración como texto sin modelo ni estado autoritativo. Sin trazabilidad ni rollback, el MTTR se dispara.
El problema es de metodología principalmente. 
Promesa: todo esto se arregla hoy con open source, y lo vais a ver corriendo.
Actualidad (OCP 2026): la industria va justo en esta dirección. Se puede conseguir un "shift from legacy, CLI-driven operations to a fully automated, API-first model" con gRPC/YANG, ZTP y telemetría; sobre interfaces estandarizadas por OpenConfig (gNMI/gNOI).
Al final, la heterogeneidad se puede gestionar mejor o peor, pero la estandarización la hace abordable. Cada divergencia en pruebas, transporte o telemetría se vuelve "un trabajo de ingeniería". A escala hiperescalar, eso son equipos enteros; a nuestra escala es el ingeniero que teclea a mano.
-->

---

<!-- _class: dark -->

<div class="kick cyan">Bloque 2 · La solución</div>

# Tres pilares, un bucle cerrado

<div class="row" style="margin-top:16px">
  <div class="card t"><span class="num" style="background:#17B3A3;color:#17233A">1</span><h3 style="margin-top:14px">Red como Código</h3><p style="color:#CFE0F2">IaC: Git es la fuente de verdad (GitOps)</p></div>
  <div class="card a"><span class="num" style="background:#F5A524;color:#17233A">2</span><h3 style="margin-top:14px">Gemelo digital</h3><p style="color:#CFE0F2">Validar antes de desplegar mediante CI/CD</p></div>
  <div class="card"><span class="num" style="background:#38BDF8;color:#17233A">3</span><h3 style="margin-top:14px">Telemetría en streaming</h3><p style="color:#CFE0F2">Observabilidad y trazabilidad en tiempo real donde la red cuenta lo que pasa</p></div>
</div>
<p class="cyan" style="text-align:center;font-style:italic;margin-top:34px;font-size:20px">PR → Validación en el Gemelo Digital → Merge → Deploy por gNMI → Telemetría confirma el efecto</p>

<!--
[05:00 · 1min] Mapa del bloque 2: tres pilares y cómo se encadenan en un bucle cerrado. Cada uno tiene su slide.
-->

---

<div class="kick teal">Pilar 1 · Red como código</div>

# La intención vive en Git, no en el equipo

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
<p>Declarativo, mínimo, revisable en un Pull Request.</p>
<div class="kick red" style="margin-top:18px">Cómo se aplica</div>
<p>Reconciliación idempotente contra el estado real del nodo, en una transacción.</p>
<div class="chips"><span>gNMI</span><span style="border-color:#38BDF8">Ansible</span><span style="border-color:#F5A524">Nornir</span></div>
<p class="mute" style="font-style:italic;font-size:16px;margin-top:22px">→ Modelo YANG: lo que configuras es lo que consultas</p>
</div>
</div>

<!--
[06:00 · 1min] Intención vs estado.
El YAML es el cambio real.
Opciones para empujar: gnmic set (nativo gNMI/YANG), Ansible, Nornir; en la demo usamos gnmic.
Refuerzo: Teniendo un "modelo de configuración de la plataforma basado en datos y validado mediante un esquema" en lugar de ediciones manuales de configuración es la base para que un agente de IA genere configuraciones y tests "con mínima interacción humana". Misma idea que este YAML + YANG, a otra escala: la intención como dato estructurado es el requisito, no un lujo.
-->

---

<div class="kick amber">Pilar 2 · Gemelo digital</div>

# Así validan los grandes

<div class="row">
  <div class="card teal-bg"><h3 style="color:#0E6E63">Emulación <em>lógica</em></h3>
    <p style="font-size:18px">Ejecución de <b>software real</b> sobre nodos de cómputo, red, almacenamiento y orquestación para validar flujos extremo a extremo <b>antes de desplegar el hierro</b>.</p></div>
  <div class="card amber-bg"><h3 style="color:#9A6200">Emulación 1:1 de producción</h3>
    <p style="font-size:18px">Tres capas: tests por <b>cada PR en CI</b>, topologías multinodo y réplicas <b>1:1 con las configs reales</b> extraídas de la infraestructura viva.</p></div>
  <div class="card" style="border-color:#38BDF8"><h3 style="color:#0369A1">Topología a escala con Kubernetes</h3>
    <p style="font-size:18px">Kubernetes como motor de automatización y de emulación de miles de nodos y enlaces para validar el comportamiento real de la red ante cada cambio.</p></div>
</div>
<div class="callout" style="text-align:center"><b class="cyan">El gemelo no es solo para la charla:</b> es el entorno de validación de cada cambio.</div>

<!--
[07:00 · 1min y 30s] El gemelo no es un truco de charla, es práctica habitual empresas como los hiperescalares.
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

<p class="mute" style="font-style:italic;font-size:14px;margin-top:4px">OCP 2026: gNMI/gNOI/OpenConfig es ya la interfaz común de switches, de conmutadores ópticos (OCS) y hasta del BMC del switch (SONiC BMC) · Google presentó telemetría sub-milisegundo en SONiC.</p>

<!--
[08:30 · 1min y 30s] Cambio de paradigma: el nodo publica; el modelo YANG es el mismo que configuramos.
Contexto OCP 2026: gNMI se ha convertido en la lengua franca sobre interfaces estandarizadas (gRPC/YANG) no solo para configuración sino también para telemetría.
"data swamp": Recoger métricas irrelevantes sin agregación no da contexto real. Es mejor tener pocas señales, pero realmente las que importan.
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
[10:00 · 10 min] Es el srl-telemetry-lab de srl-labs tal cual, con dos parches: estado de sesión por vecino BGP y un dashboard por etapas.
Escenario: leaf3 es el leaf nuevo del rack de Proxmox (client3 = ese servidor). Tiene underlay y nada más. Vamos a adherirlo al overlay y al servicio con dos PRs. Cada etapa es un PR con su plan, verificación y rollback. La etapa 2 la propone el pipeline cuando la 1 está verificada (promoción automática, aprobación humana).
Ejecución de la demo.
Anotaciones: el pipeline marca en Grafana cada deploy, así se ve causa y efecto.
-->

---

<div class="kick teal">Bloque 4 · El futuro</div>

# ¿Y la IA? Necesita una red determinista

<div class="row">
  <div class="card"><b class="red">Un agente de IA falla cuando razona sobre…</b>
    <ul><li>CLI y config como texto no estructurado</li><li>Telemetría con esquemas distintos por vendor</li><li>Ningún estado de referencia autoritativo</li></ul></div>
  <div class="card teal-bg"><b style="color:#0E6E63">Lo que acabamos de construir le da…</b>
    <ul><li>Intención versionada en Git (fuente de verdad)</li><li>Modelo YANG + gNMI: datos estructurados</li><li>Un gemelo donde probar antes de actuar</li></ul></div>
</div>
<div class="callout"><b class="amber">Los LLM son probabilísticos; las operaciones de red deben ser deterministas.</b> GitOps + telemetría es el suelo (L2–L3) sobre el que la IA puede subir a L4–L5 sin alucinar la red.</div>
<p class="mute" style="font-style:italic;font-size:14px;margin-top:10px">OCP 2026, SONiC Workshop: el <em>pipeline</em> agéntico de Celestica = telemetría gNMI + <em>snapshots</em> de configuración + <b>reglas de fallo deterministas</b> + LLM local. AMD/AMI: «la IA sin gobierno no es fiable»: contexto versionado, <em>guardrails</em> y cambios revisables y reproducibles.</p>

<!--
[20:00 · 4min] Un agente es un software autónomo que recibe un objetivo y utiliza IA para percibir el entorno, razonar sobre sus metas y tomar sucesivas acciones para conseguir alcanzar el objetivo marcado.
Cierre del círculo con la escalera de la slide 2: sin fuente de verdad ni datos estructurados, un agente de IA solo automatiza el caos. Lo de hoy no compite con AIOps: es su prerrequisito.
Diferentes propuestas de "IA agéntica para operar la red" se apoyan en los tres pilares:
  - Combinar telemetría gNMI en tiempo real y snapshots de configuración con "reglas de fallo determinísticas y LLMs desplegados en local" para RCA y remediación, priorizando la soberanía del dato on-prem.
  - Predicción de fallos.
  - Devolver lo aprendido "de vuelta a la fuente de la verdad".
  - Contexto versionado en el repo, guardaraíles y playbooks de revisión para que cada cambio asistido por IA sea "revisable y reproducible". Traducción: Git como fuente de verdad, datos YANG/gNMI y un gemelo donde probar. Exactamente lo que muestra la demo.
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
<p class="cyan" style="font-size:20px;font-style:italic">La red pasa a integrarse en el pipeline del negocio.</p>

<!--
[24:00 · 1 min] Sense/think/act = telemetría / validación / deploy. Tres pilares, un bucle cerrado. Y todo sobre un Proxmox modesto, sin licencias.
Cierre con actualidad: Meta dice que la red para IA "es un problema de diseño cooperativo que ninguna empresa puede resolver por sí misma" y que las iniciativas abiertas hacen avanzar a todo el ecosistema. Lo mismo a nuestra escala: todo lo que habéis visto es open source y reproducible.
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
<p style="color:#7E92AE;margin-top:60px">Víctor Serrano Bazán · Tecnocrática Tech Day 2026</p>