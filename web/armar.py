"""Une plantilla + calc.js + optimiza.js + modelo3d.js + ui.js + ui_busqueda.js + vista3d.js en una sola página: docs/index.html.
Sin dependencias, salvo three.js para la vista 3D, que se carga de internet solo al abrir esa pestaña."""
import pathlib
aqui = pathlib.Path(__file__).parent
plantilla = (aqui / "plantilla.html").read_text(encoding="utf-8")
calc = (aqui / "calc.js").read_text(encoding="utf-8")
calc = calc.replace('if (typeof module !== "undefined") module.exports', '// (Node) if (typeof module !== "undefined") module.exports')
ui = (aqui / "ui.js").read_text(encoding="utf-8")
# la búsqueda va en el mismo script, antes del arranque
corte = ui.index("// ---------- arranque ----------")
nodo = lambda f: (aqui / f).read_text(encoding="utf-8").replace('if (typeof module !== "undefined") module.exports', '// (Node) if (typeof module !== "undefined") module.exports')
opt, m3d = nodo("optimiza.js"), nodo("modelo3d.js")
ui = ui[:corte] + (aqui / "ui_busqueda.js").read_text(encoding="utf-8") + "\n" + (aqui / "vista3d.js").read_text(encoding="utf-8") + "\n" + ui[corte:]
calc = calc + "\n" + opt + "\n" + m3d
assert "</script" not in calc and "</script" not in ui
pagina = plantilla.replace("/*CALC*/", calc).replace("/*UI*/", ui)
ESQUELETO = '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="description" content="Diseño de transformadores de distribución: núcleo, devanados, distancias, Vcc, pérdidas y esfuerzos dieléctricos, con búsqueda por Vcc.">\n<meta name="author" content="Jhon Peralta">\n<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0}[hidden]{display:none!important}</style>\n'
salida = aqui.parent / "docs" / "index.html"
salida.parent.mkdir(exist_ok=True)
salida.write_text(ESQUELETO + pagina + "\n</body>\n</html>\n", encoding="utf-8")
print(salida, len(pagina), "bytes")
