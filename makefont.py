#!/usr/bin/env python
from pathlib import Path, PurePosixPath
import json, uuid
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.colorLib.builder import buildCPAL, buildCOLR
from fontTools.pens.ttGlyphPen import TTGlyphPen
from cu2qu.pens import Cu2QuPen

SRC_FONT   = Path("Inconsolata-Regular.otf")
SCHEMES    = Path("cleancolors.json")
FONTNAME   = "Protsolata"
BASE       = "clustal2"
FALLBACK   = "#000000FF"
OUT_WOFF   = f"{FONTNAME}.woff"
OUT_WOFF2  = f"{FONTNAME}.woff2"
OUT_CSS    = f"{FONTNAME}_palettes.css"
OUT_HTML   = f"{FONTNAME}_test.html"

def blank():
    return TTGlyphPen(None).glyph()

def to_quad(src_g):
    """cubic to quadratic"""
    p = TTGlyphPen(None)
    src_g.draw(Cu2QuPen(p, 1.0, False))
    return p.glyph()

def h2rgba(hex8):
    r = int(hex8[1:3],16)/255
    g = int(hex8[3:5],16)/255
    b = int(hex8[5:7],16)/255
    a = int(hex8[7:9],16)/255
    return (r, g, b, a)

def hex6(hex8):
    return "#" + hex8[1:7]

schemes = json.loads(SCHEMES.read_text())
ordered = [BASE] + sorted([k for k in schemes if k != BASE])

src  = TTFont(str(SRC_FONT))
gset = src.getGlyphSet()
cmap = src.getBestCmap()

letters = sorted({c.upper() for m in schemes.values() for c in m})
pid     = {ltr: i for i, ltr in enumerate(letters)}

palettes = []
for name in ordered:
    palettes.append([
        schemes[name].get(ltr, FALLBACK) for ltr in letters
    ])

digits_punct = list("0123456789-.|+")
SPACE_GLYPH  = "space"
advW, _ = src["hmtx"].metrics[cmap[ord('A')]]

glyph_order = [".notdef", SPACE_GLYPH]
glyphs      = {".notdef": blank(), SPACE_GLYPH: blank()}
hmtx        = {".notdef": (advW,0), SPACE_GLYPH:(advW,0)}
layers      = {SPACE_GLYPH: []}

for L in letters:
    cid = pid[L]

    for ch in (L, L.lower()):
        code = ord(ch)
        if code not in cmap: continue
        base, layer = ch, ch + ".layer"
        glyph_order += [base, layer]

        outline = to_quad(gset[cmap[code]])
        glyphs[base]  = blank()
        glyphs[layer] = outline
        hmtx[base] = hmtx[layer] = src["hmtx"].metrics[cmap[code]]
        layers[base] = [(layer, cid)]


# plain digits / punctuation
def add_plain_recursive(gname: str):
    """Copy glyph and (if TrueType composite) its component glyphs."""
    if gname in glyphs:
        return

    # copy this glyph
    glyph_order.append(gname)
    glyphs[gname] = to_quad(gset[gname])
    hmtx[gname]   = src["hmtx"].metrics.get(gname, (advW, 0))

    # TrueType composites only: bring referenced components as well
    src_glyph_obj = getattr(gset[gname], "_glyph", None)
    if src_glyph_obj and getattr(src_glyph_obj, "components", None):
        for comp in src_glyph_obj.components:
            add_plain_recursive(comp.glyphName)

for ch in digits_punct:
    code = ord(ch)
    if code not in cmap:
        continue
    add_plain_recursive(cmap[code])

fb = FontBuilder(src["head"].unitsPerEm, isTTF=True)
fb.setupGlyphOrder(glyph_order)
fb.setupGlyf(glyphs)
fb.setupHorizontalMetrics(hmtx)
fb.setupHorizontalHeader(ascent=src["hhea"].ascent, descent=src["hhea"].descent)
fb.setupMaxp()
fb.setupPost()

cmap_full = {ord(l): l for l in letters}
cmap_full.update({ord(l.lower()): l.lower() for l in letters})
for c in digits_punct:
    cmap_full[ord(c)] = cmap[ord(c)]
cmap_full[0x20] = cmap_full[0xA0] = SPACE_GLYPH
fb.setupCharacterMap(cmap_full)
fb.setupOS2()

fb.setupNameTable({"familyName": FONTNAME, "styleName":"Regular"})
for rec in src["name"].names:
    if rec.nameID == 0:
        fb.font["name"].names.append(rec)
name = fb.font["name"]

ENGLISH=0x0409
def add_name(nameID, string, langID=ENGLISH):
    # platform 3 = Windows, encID 1 = Unicode BMP
    name.setName(string, nameID, 3, 1, langID)
    # platform 1 = Macintosh, encID 0 = Roman
    try:
        mac_str = string.encode("mac_roman").decode("mac_roman")
    except UnicodeEncodeError:
        mac_str = string
    name.setName(mac_str, nameID, 1, 0, 0)

family      = FONTNAME
style       = "Regular"
unique_id   = f"{family}-{style}-{uuid.uuid4().hex[:6]}"
version_str = "Version 1.0"

add_name(1, family)               # Font Family
add_name(2, style)                # Sub‑family
add_name(3, unique_id)            # Unique ID
add_name(4, f"{family} {style}")  # Full name
add_name(5, version_str)          # Version
add_name(6, f"{family}-{style}")  # PostScript name

fb.font["CPAL"] = buildCPAL([[h2rgba(c) for c in pal] for pal in palettes])
colr = buildCOLR(layers, version=0)
colr.version = 0
fb.font["COLR"] = colr

fb.font.flavor=None
fb.font.save(f"{FONTNAME}.ttf")
print("✓", f"{FONTNAME}.ttf")

fb.font.flavor="woff"
fb.font.save(OUT_WOFF)
print("✓", OUT_WOFF)

fb.font.flavor="woff2"
fb.font.save(OUT_WOFF2)
print("✓", OUT_WOFF2)

css = [
    f"/* {FONTNAME} palettes */",
    "@font-face {",
    f"  font-family: '{FONTNAME}';",
    f"  src: url('./{OUT_WOFF}') format('woff'), url('./{OUT_WOFF2}') format('woff2');",
    "}\n"
]

for idx,name in enumerate(ordered):
    css += [
        f"@font-palette-values --{name} {{",
        f"  font-family: '{FONTNAME}';",
        f"  base-palette: {idx};",
        "}\n"
    ]
    css += [
        f"@font-palette-values --{name}-override {{",
        f"  font-family: '{FONTNAME}';",
        f"  base-palette: 0;",
        "  override-colors:"
    ]
    overrides = [f"    {pid[l]} {hex6(schemes[name].get(l,FALLBACK))}"
                 for l in letters]
    css.append(",\n".join(overrides)+";")
    css.append("}\n")

    css += [
        f".{name}              {{ font-family:'{FONTNAME}'; font-palette: --{name}; }}",
        f".{name}-override     {{ font-family:'{FONTNAME}'; font-palette: --{name}-override; }}\n"
    ]

Path(OUT_CSS).write_text("\n".join(css))
print("✓", OUT_CSS)

sample = "ARNDCQEGHILKMFPSTWYVBZX arncdqeghilkmfpstwyvbzx 0123456789 -.|"
html = [
    "<!doctype html><meta charset=utf-8>",
    f"<title>{FONTNAME} demo</title>",
    f"<link rel=stylesheet href={PurePosixPath(OUT_CSS)}>",
    f"<style>body{{font:32px/1.4 '{FONTNAME}',monospace;margin:2rem}}</style>",
    f"<h2>Base palette ({BASE})</h2>",
    f"<p class='{BASE}'>{sample}</p>",
    "<h2>Each scheme built-in + override</h2>"
]
for n in ordered:
    html.append(f"<p class='{n}'>{n}: {sample}</p>")
    html.append(f"<p class='{n}-override'>{n}-override: {sample}</p>")
Path(OUT_HTML).write_text("\n".join(html))
print("✓", OUT_HTML)

