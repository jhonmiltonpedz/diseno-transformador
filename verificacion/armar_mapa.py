"""Arma docs/mapa-condiciones.html con el catálogo (reglas.json) y la última revisión (resultado_mapa.json)."""
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
cat = json.loads((AQUI / "reglas.json").read_text(encoding="utf-8"))
res = json.loads((AQUI / "resultado_mapa.json").read_text(encoding="utf-8"))
for f in res["filas"].values():
    f.pop("detalle_js", None)
    f.pop("errores", None)
datos = json.dumps({"cat": cat, "res": res}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = (AQUI / "plantilla_mapa.html").read_text(encoding="utf-8").replace("/*__DATOS__*/", datos)
ESQUELETO = '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="description" content="Mapa de las condiciones del programa de diseño de transformadores, con su origen y la prueba que las dispara en Python y en la web.">\n<meta name="author" content="Jhon Peralta">\n<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0}[hidden]{display:none!important}</style>\n'
salida = AQUI.parent / "docs" / "mapa-condiciones.html"
salida.parent.mkdir(exist_ok=True)
salida.write_text(ESQUELETO + html + "\n</body>\n</html>\n", encoding="utf-8")
print(salida, round(len(html.encode()) / 1024), "KB")
