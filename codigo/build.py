#!/usr/bin/env python3
"""Genera la app instalable (dist/) y la versión de vista previa (artifact.html) a partir de src/."""
import json, os, hashlib
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
os.makedirs(os.path.join(DIST, "icons"), exist_ok=True)

app = open(os.path.join(ROOT, "src/app.html"), encoding="utf-8").read()
verbs = open(os.path.join(ROOT, "src/verbs.js"), encoding="utf-8").read()
app = app.replace("/*VERBS*/", verbs)
head, body = app.split("<!--BODY-->", 1)

# Vista previa para claude.ai (sin service worker ni manifest)
open(os.path.join(ROOT, "artifact.html"), "w", encoding="utf-8").write(head + body)

# Iconos
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def icon(size, maskable=False):
    im = Image.new("RGB", (size, size), "#5b3fd1")
    d = ImageDraw.Draw(im)
    pad = size * (0.2 if maskable else 0.1)
    inner = size - 2 * pad
    colors = ["#fbe58a", "#f9cdd3", "#a9e5d6"]
    words = ["GO", "WENT", "GONE"]
    h = inner / 3
    for i, (c, w) in enumerate(zip(colors, words)):
        y0 = pad + i * h + h * 0.08
        d.rounded_rectangle([pad, y0, size - pad, y0 + h * 0.84], radius=h * 0.25, fill=c)
        fs = int(h * 0.55)
        f = ImageFont.truetype(BOLD, fs)
        while d.textlength(w, font=f) > inner * 0.85:
            fs -= 2; f = ImageFont.truetype(BOLD, fs)
        d.text((size / 2, y0 + h * 0.42), w, font=f, fill="#23202b", anchor="mm")
    return im
for s in (192, 512):
    icon(s).save(os.path.join(DIST, f"icons/icon-{s}.png"))
icon(512, True).save(os.path.join(DIST, "icons/maskable-512.png"))
icon(180).save(os.path.join(DIST, "icons/apple-touch-icon.png"))

manifest = {
    "name": "Verbos Irregulares",
    "short_name": "Verbos",
    "description": "Aprende los verbos irregulares en inglés con tarjetas y tests.",
    "lang": "es",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f6f1ea",
    "theme_color": "#5b3fd1",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
json.dump(manifest, open(os.path.join(DIST, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

index = ("<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
         "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
         "<meta name=\"theme-color\" content=\"#5b3fd1\">\n"
         "<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n"
         "<meta name=\"mobile-web-app-capable\" content=\"yes\">\n"
         "<meta name=\"apple-mobile-web-app-title\" content=\"Verbos\">\n"
         "<link rel=\"manifest\" href=\"manifest.webmanifest\">\n"
         "<link rel=\"icon\" href=\"icons/icon-192.png\">\n"
         "<link rel=\"apple-touch-icon\" href=\"icons/apple-touch-icon.png\">\n"
         "<script>window.__PWA = true;</script>\n"
         + head + "</head>\n<body>\n" + body + "</body>\n</html>\n")
open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(index)

files = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png",
         "icons/maskable-512.png", "icons/apple-touch-icon.png"]
version = hashlib.sha1(index.encode()).hexdigest()[:8]
sw = f"""// Guarda la app en el móvil para que funcione sin conexión.
const CACHE = "verbos-{version}";
const FILES = {json.dumps(files)};
self.addEventListener("install", e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request, {{ ignoreSearch: true }}).then(hit => {{
      const net = fetch(e.request).then(res => {{
        if (res && (res.ok || res.type === "opaque")) {{ const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }}
        return res;
      }}).catch(() => hit || (e.request.mode === "navigate" ? caches.match("index.html") : undefined));
      return hit || net;
    }})
  );
}});
"""
open(os.path.join(DIST, "sw.js"), "w", encoding="utf-8").write(sw)
print("ok", version)
