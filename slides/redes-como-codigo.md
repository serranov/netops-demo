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
section table { width: max-content; max-width: 100%; margin-left: auto; margin-right: auto; }   /* el tema de Marp pinta la tabla como bloque; asi queda centrada */
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

<div class="chips" style="margin-top:28px"><span>Proxmox VE</span><span>Git</span><span>Containerlab</span><span>Telemetría</span></div>

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
Marp: Automatización de las slides.
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
<p class="mute" style="font-style:italic;font-size:16px;margin-top:22px">→ Modelo YANG: lo que configuras es lo que consultas.</p>
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
    <p style="font-size:18px">Como motor de automatización y de emulación de miles de nodos y enlaces para validar el comportamiento real de la red ante cada cambio.</p></div>
</div>
<div class="callout" style="text-align:center"><b class="cyan">El gemelo digital no es solo para la charla:</b> es el entorno de validación de cada cambio.</div>

<!--
[07:00 · 1min y 30s] El gemelo no es un truco de charla, es práctica habitual empresas como los hiperescalares.
-->

---

<div class="kick cyan">Pilar 3 · Telemetría</div>

# Streaming (gNMI) frente a polling (SNMP)

| | SNMP | <span style="color:#fff">gNMI / gRPC</span> |
|---|---|---|
| Modelo | Pull: el colector pregunta | Push: el nodo publica (subscribe) |
| Datos | MIBs jerárquicas, parciales | YANG: 100% del estado y la config |
| Latencia | Intervalos de segundos o minutos | Sub-segundo, on-change o muestreo |
| Coste en el equipo | CPU alta en cada sondeo | Eficiente, una sesión gRPC |

<p class="mute" style="text-align:center;font-style:italic;font-size:14px;margin-top:4px">OCP 2026: Interfaces gRPC de OpenConfig (gNMI/gNOI/gNSI) son ya las interfaces comunes de switches, de conmutadores ópticos y hasta del BMC del switch.</p>

<!--
[08:30 · 1min y 30s] Cambio de paradigma: el nodo publica; el modelo YANG es el mismo que configuramos.
Contexto OCP 2026: gNMI se ha convertido en la lengua franca sobre interfaces estandarizadas (gRPC/YANG) no solo para configuración sino también para telemetría.
"data swamp": Recoger métricas irrelevantes sin agregación no da contexto real. Es mejor tener pocas señales, pero realmente las que importan.
-->

---

<!-- _class: dark -->

<div class="kick amber">Bloque 3 · Demo en vivo</div>

# Llega un servidor nuevo

## Onboarding de leaf3: de día 0 a servicio, por Git

<div class="row">
<div style="flex:1.25">
<svg width="580" height="290" viewBox="0 0 580 290" style="margin-top:-6px;overflow:visible">
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
  <div class="card" style="border-color:#7E92AE;padding:12px 18px;margin-bottom:10px"><span class="kick" style="color:#7E92AE">Día 0</span><b style="font-size:20px;display:block">Onboarding</b><small style="color:#CFE0F2">Conexión física y underlay eBGP</small></div>
  <div class="card t" style="padding:12px 18px;margin-bottom:10px"><span class="kick teal">Día 1</span><b style="font-size:20px;display:block">Overlay iBGP EVPN</b><small style="color:#CFE0F2">PR #1 · Abierto a mano</small></div>
  <div class="card a" style="padding:12px 18px"><span class="kick amber">Día 2</span><b style="font-size:20px;display:block">Servicio de nivel 2</b><small style="color:#CFE0F2">PR #2 · Abierto automáticamente por el pipeline</small></div>
</div>
</div>

<!--
[10:00 · 10 min] Es el srl-telemetry-lab de srl-labs tal cual, con dos parches: estado de sesión por vecino BGP y un dashboard por etapas.
Escenario: leaf3 es el leaf nuevo del rack de Proxmox (client3 = ese servidor). Tiene underlay y nada más. Vamos a adherirlo al overlay y al servicio con dos PRs. Cada etapa es un PR con su plan, verificación y rollback. La etapa 2 la propone el pipeline cuando la 1 está verificada (promoción automática, aprobación humana).
Ejecución de la demo.
Anotaciones: el pipeline marca en Grafana cada deploy, así se ve causa y efecto.
-->

---

<div class="kick teal">Bloque 4 · El futuro</div>

# ¿Y la IA?

## Necesita una red determinista

<div class="row">
  <!-- Los titulos tienen la misma altura fija (2 lineas) para que los bullets de ambas tarjetas queden a la misma altura -->
  <div class="card"><b class="red" style="display:block;min-height:2.6em">Un agente de IA falla cuando razona sobre…</b>
    <ul><li>CLI y config como texto no estructurado</li><li>Telemetría con esquemas por fabricante</li><li>Ningún estado de referencia autoritativo</li></ul></div>
  <div class="card teal-bg"><b style="color:#0E6E63;display:block;min-height:2.6em">Lo que acabamos de construir le da…</b>
    <ul><li>Git como fuente de verdad versionada</li><li>Modelo YANG + gNMI: datos estructurados</li><li>Un gemelo donde probar antes de actuar</li></ul></div>
</div>
<div class="callout" style="text-align:center"><b class="amber" style="display:block;margin-bottom:8px">Los LLM son probabilísticos; las operaciones de red deben ser deterministas.</b>
GitOps + telemetría es el suelo (L2–L3) sobre el que la IA puede construir para llegar a L4–L5.</div>

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

<!-- Diagrama "Networks that sense, think and act" (recreado como SVG a partir de la slide 3 de Automation.pptx) -->
<svg viewBox="0 0 760 350" width="760" height="350" style="display:block;margin:0 auto" font-family="Calibri, 'Segoe UI', Arial, sans-serif">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#fff"/></marker>
    <marker id="arc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#38BDF8"/></marker>
  </defs>
  <!-- Sense / Think / Act -->
  <g fill="none" stroke="#fff" stroke-width="2">
    <rect x="70" y="150" width="120" height="60" rx="10" stroke="#F5A524"/>
    <rect x="320" y="150" width="120" height="60" rx="10" stroke="#38BDF8"/>
    <rect x="570" y="150" width="120" height="60" rx="10" stroke="#17B3A3"/>
    <line x1="192" y1="180" x2="316" y2="180" marker-end="url(#ar)"/>
    <line x1="442" y1="180" x2="566" y2="180" marker-end="url(#ar)"/>
  </g>
  <g font-size="22" font-weight="800" fill="#fff" text-anchor="middle">
    <text x="130" y="178" fill="#F5A524">Sense</text><text x="380" y="178" fill="#38BDF8">Think</text><text x="630" y="178" fill="#17B3A3">Act</text>
  </g>
  <g font-size="13" font-weight="700" fill="#CFE0F2" text-anchor="middle">
    <text x="130" y="200">Telemetría</text><text x="380" y="200">Validación</text><text x="630" y="200">Despliegue</text>
  </g>
  <!-- Red (nube) y bucle -->
  <g transform="translate(342,238) scale(3.5)"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" fill="#16304F" stroke="#fff" stroke-width="0.6"/></g>
  <text x="384" y="296" font-size="16" font-weight="800" fill="#fff" text-anchor="middle">Red</text>
  <g fill="none" stroke="#fff" stroke-width="2">
    <path d="M346 292 C 240 292, 170 270, 150 214" marker-end="url(#ar)"/>
    <path d="M630 214 C 630 270, 540 292, 430 292" marker-end="url(#ar)"/>
  </g>
  <text x="236" y="254" font-size="14" font-style="italic" fill="#CFE0F2" text-anchor="middle">Datos</text>
  <!-- Cerebro (Think) con salidas: analítica · automatización · asistencia a humanos -->
  <g transform="translate(358.4,76.4) scale(1.8)" fill="none" stroke="#fff" stroke-width="1.2" stroke-linejoin="round" stroke-linecap="round">
    <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
    <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
    <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>
    <path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/>
  </g>
  <g fill="none" stroke="#38BDF8" stroke-width="2" stroke-dasharray="3 5">
    <line x1="352" y1="98" x2="196" y2="98" marker-end="url(#arc)"/>
    <line x1="408" y1="98" x2="564" y2="98" marker-end="url(#arc)"/>
    <line x1="380" y1="74" x2="380" y2="50" marker-end="url(#arc)"/>
  </g>
  <!-- Analítica -->
  <g fill="#fff"><rect x="150" y="96" width="6" height="12"/><rect x="160" y="88" width="6" height="20"/><rect x="170" y="92" width="6" height="16"/></g>
  <text x="142" y="104" font-size="15" fill="#fff" text-anchor="end">Analítica</text>
  <!-- Automatización (brazo robot) -->
  <g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M580 110h26"/><path d="M593 110v-12l10-10h8"/><circle cx="593" cy="98" r="3" fill="#16304F"/><circle cx="611" cy="88" r="3" fill="#16304F"/>
  </g>
  <text x="618" y="104" font-size="15" fill="#fff" text-anchor="start">Automatización</text>
  <!-- Asistencia a humanos -->
  <g transform="translate(360.8,7.6) scale(1.6)" fill="none" stroke="#fff" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></g>
  <text x="356" y="31" font-size="15" fill="#fff" text-anchor="end">Asistencia a humanos</text>
  <!-- Agentes IA (robot) -->
  <g fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round">
    <rect x="598" y="18" width="24" height="18" rx="4"/><line x1="610" y1="10" x2="610" y2="18"/><circle cx="610" cy="8" r="2" fill="#fff"/>
    <circle cx="605" cy="27" r="2" fill="#fff"/><circle cx="615" cy="27" r="2" fill="#fff"/><path d="M602 44h16"/>
  </g>
  <text x="630" y="31" font-size="15" fill="#fff" text-anchor="start">Agentes IA</text>
  <!-- Fuentes externas: web · librerías -->
  <g fill="none" stroke="#fff" stroke-width="2"><circle cx="30" cy="262" r="11"/><ellipse cx="30" cy="262" rx="5" ry="11"/><line x1="19" y1="262" x2="41" y2="262"/></g>
  <text x="48" y="267" font-size="15" fill="#fff">Web</text>
  <g fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"><rect x="20" y="296" width="20" height="22" rx="2"/><line x1="26" y1="296" x2="26" y2="318"/></g>
  <text x="48" y="311" font-size="15" fill="#fff">Librerías</text>
  <path d="M88 262 C 128 262, 122 238, 108 214" fill="none" stroke="#fff" stroke-width="2" marker-end="url(#ar)"/>
</svg>
<p style="font-size:24px;font-weight:800;margin-top:14px">Código + telemetría + GitOps = bucle cerrado funcional.</p>
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

<p class="cyan" style="font-size:22px">Todo el laboratorio está basado en componentes open source y es totalmente reproducible</p>
<div class="row" style="align-items:center;margin-top:30px">
  <div style="width:170px;height:170px;background:#fff;border-radius:10px;display:flex;align-items:center;justify-content:center;flex:none"><!-- QR: https://github.com/serranov/netops-demo (generado con segno; también en slides/qr.png y qr.svg) -->
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 29 29" width="146" height="146" shape-rendering="crispEdges"><path fill="#0e2038" d="M0 0h7v1h-7zM10 0h3v1h-3zM14 0h2v1h-2zM19 0h1v1h-1zM22 0h7v1h-7zM0 1h1v1h-1zM6 1h1v1h-1zM10 1h1v1h-1zM14 1h3v1h-3zM22 1h1v1h-1zM28 1h1v1h-1zM0 2h1v1h-1zM2 2h3v1h-3zM6 2h1v1h-1zM9 2h2v1h-2zM12 2h1v1h-1zM14 2h1v1h-1zM17 2h3v1h-3zM22 2h1v1h-1zM24 2h3v1h-3zM28 2h1v1h-1zM0 3h1v1h-1zM2 3h3v1h-3zM6 3h1v1h-1zM10 3h3v1h-3zM14 3h2v1h-2zM18 3h3v1h-3zM22 3h1v1h-1zM24 3h3v1h-3zM28 3h1v1h-1zM0 4h1v1h-1zM2 4h3v1h-3zM6 4h1v1h-1zM11 4h1v1h-1zM14 4h3v1h-3zM18 4h1v1h-1zM22 4h1v1h-1zM24 4h3v1h-3zM28 4h1v1h-1zM0 5h1v1h-1zM6 5h1v1h-1zM8 5h2v1h-2zM11 5h3v1h-3zM15 5h2v1h-2zM19 5h1v1h-1zM22 5h1v1h-1zM28 5h1v1h-1zM0 6h7v1h-7zM8 6h1v1h-1zM10 6h1v1h-1zM12 6h1v1h-1zM14 6h1v1h-1zM16 6h1v1h-1zM18 6h1v1h-1zM20 6h1v1h-1zM22 6h7v1h-7zM10 7h1v1h-1zM12 7h1v1h-1zM14 7h2v1h-2zM17 7h2v1h-2zM20 7h1v1h-1zM0 8h1v1h-1zM3 8h1v1h-1zM5 8h2v1h-2zM8 8h1v1h-1zM10 8h1v1h-1zM12 8h5v1h-5zM21 8h1v1h-1zM23 8h1v1h-1zM2 9h1v1h-1zM5 9h1v1h-1zM7 9h1v1h-1zM9 9h1v1h-1zM20 9h1v1h-1zM22 9h1v1h-1zM25 9h1v1h-1zM28 9h1v1h-1zM1 10h3v1h-3zM5 10h4v1h-4zM10 10h1v1h-1zM16 10h2v1h-2zM19 10h1v1h-1zM21 10h1v1h-1zM24 10h4v1h-4zM1 11h1v1h-1zM3 11h1v1h-1zM8 11h1v1h-1zM10 11h4v1h-4zM20 11h1v1h-1zM24 11h1v1h-1zM26 11h2v1h-2zM0 12h2v1h-2zM3 12h2v1h-2zM6 12h1v1h-1zM10 12h1v1h-1zM14 12h1v1h-1zM17 12h1v1h-1zM21 12h2v1h-2zM25 12h1v1h-1zM27 12h2v1h-2zM0 13h1v1h-1zM2 13h3v1h-3zM7 13h6v1h-6zM19 13h3v1h-3zM2 14h1v1h-1zM6 14h1v1h-1zM11 14h2v1h-2zM16 14h1v1h-1zM20 14h1v1h-1zM22 14h7v1h-7zM0 15h2v1h-2zM3 15h2v1h-2zM7 15h1v1h-1zM9 15h2v1h-2zM13 15h1v1h-1zM15 15h1v1h-1zM17 15h2v1h-2zM20 15h3v1h-3zM25 15h1v1h-1zM27 15h1v1h-1zM0 16h4v1h-4zM5 16h2v1h-2zM8 16h1v1h-1zM11 16h4v1h-4zM16 16h2v1h-2zM20 16h1v1h-1zM23 16h1v1h-1zM27 16h1v1h-1zM2 17h4v1h-4zM7 17h1v1h-1zM14 17h1v1h-1zM16 17h1v1h-1zM18 17h1v1h-1zM20 17h4v1h-4zM25 17h1v1h-1zM28 17h1v1h-1zM0 18h1v1h-1zM2 18h1v1h-1zM4 18h1v1h-1zM6 18h2v1h-2zM9 18h1v1h-1zM13 18h1v1h-1zM17 18h1v1h-1zM21 18h1v1h-1zM23 18h2v1h-2zM27 18h2v1h-2zM2 19h4v1h-4zM7 19h1v1h-1zM11 19h3v1h-3zM17 19h1v1h-1zM20 19h2v1h-2zM23 19h2v1h-2zM27 19h2v1h-2zM0 20h1v1h-1zM3 20h1v1h-1zM5 20h3v1h-3zM14 20h3v1h-3zM18 20h7v1h-7zM26 20h1v1h-1zM8 21h6v1h-6zM16 21h1v1h-1zM19 21h2v1h-2zM24 21h1v1h-1zM26 21h3v1h-3zM0 22h7v1h-7zM10 22h5v1h-5zM17 22h1v1h-1zM20 22h1v1h-1zM22 22h1v1h-1zM24 22h1v1h-1zM27 22h1v1h-1zM0 23h1v1h-1zM6 23h1v1h-1zM8 23h2v1h-2zM13 23h1v1h-1zM15 23h2v1h-2zM18 23h1v1h-1zM20 23h1v1h-1zM24 23h3v1h-3zM28 23h1v1h-1zM0 24h1v1h-1zM2 24h3v1h-3zM6 24h1v1h-1zM10 24h1v1h-1zM12 24h1v1h-1zM14 24h1v1h-1zM17 24h1v1h-1zM20 24h5v1h-5zM27 24h2v1h-2zM0 25h1v1h-1zM2 25h3v1h-3zM6 25h1v1h-1zM8 25h1v1h-1zM10 25h1v1h-1zM13 25h2v1h-2zM19 25h2v1h-2zM22 25h6v1h-6zM0 26h1v1h-1zM2 26h3v1h-3zM6 26h1v1h-1zM11 26h2v1h-2zM19 26h2v1h-2zM24 26h3v1h-3zM28 26h1v1h-1zM0 27h1v1h-1zM6 27h1v1h-1zM10 27h2v1h-2zM15 27h3v1h-3zM19 27h3v1h-3zM24 27h1v1h-1zM27 27h1v1h-1zM0 28h7v1h-7zM8 28h2v1h-2zM13 28h1v1h-1zM17 28h1v1h-1zM20 28h6v1h-6zM27 28h1v1h-1z"/></svg>
  </div>
  <div style="padding-left:10px">
    <b style="font-size:24px">github.com/serranov/netops-demo</b><br>
    <span style="color:#AEC2DE;font-size:16px">Containerlab · SR Linux · gNMIc · Prometheus · Grafana · Gitea Actions</span><br>
    <span style="color:#AEC2DE;font-size:16px">Sobre un Proxmox modesto, sin gastar un euro en licencias.</span>
  </div>
</div>
<p style="color:#7E92AE;margin-top:60px">Víctor Serrano Bazán · Tecnocrática Tech Day 2026</p>