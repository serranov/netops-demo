# Slides de la charla (Marp)

`redes-como-codigo.md` es la presentación completa en [Marp](https://marp.app): Markdown + tema CSS embebido, 17 slides, y **notas de orador** con marcas de tiempo en los comentarios HTML de cada slide (modo presentador: tecla **P** en el HTML).

Los artefactos se generan en `dist/` (ignorado por git) desde la raíz del repositorio:

```bash
make slides          # dist/redes-como-codigo.html  (autocontenido; abrir en el navegador y presentar)
make slides-pdf      # dist/redes-como-codigo.pdf
make slides-pptx     # dist/redes-como-codigo.pptx (con las notas de orador)
make slides-all      # los tres
make slides-watch    # servidor con recarga en caliente en http://localhost:8080 mientras editas el .md
```

Por defecto usan la imagen Docker oficial `marpteam/marp-cli` (incluye Chromium: no hace falta Node ni navegador).
Sin Docker, con Node ≥ 18 y un navegador instalado: `make slides MARP="npx -y @marp-team/marp-cli@latest"`.

Las slides usan HTML inline para los diagramas; los targets ya pasan `--html`. En VS Code (extensión *Marp for VS Code*) activa `"markdown.marp.enableHtml": true` para la vista previa.

Retoques pendientes: sustituir el recuadro "QR" de la última slide por la imagen real (`<img src="qr.png" width="150">`, el fichero en `slides/`), y el cargo/handle de la portada.
