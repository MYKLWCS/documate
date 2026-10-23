#!/usr/bin/env python3
"""Documate brand assets. Single source of truth for the mark, the wordmark and the colour tokens.

Same family as Chatmate (teal squircle, gold accent, lowercase Inter Display Bold wordmark with "mate" in teal).
Run from this folder:  python3 gen.py   (needs fontTools and the Inter Display Bold font; build.sh runs it in Alpine)
Writes the SVGs and the two React components the rebrand drops into the app (generated, not committed).
PNG/ICO/JPG files are rendered from these SVGs at build time by rebrand.py (rsvg-convert + Pillow).
"""
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

# --- tokens (shared with Chatmate) ------------------------------------------------------------------------
TEAL_LIGHT = "#2DD4BF"
TEAL = "#0D9488"
TEAL_DEEP = "#0B4F4A"
GOLD = "#E3B341"
GOLD_DEEP = "#C08A1E"
INK_LIGHT = "#0F172A"
INK_DARK = "#F8FAFC"
FONT = os.environ.get("FONT") or next(p for p in ("/usr/share/fonts/inter/InterDisplay-Bold.otf",          # Alpine font-inter
                                                 "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf")  # Debian fonts-inter
                                         if os.path.exists(p))


def defs(uid):
    return f"""<defs>
  <linearGradient id="{uid}bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{TEAL_LIGHT}"/><stop offset="0.45" stop-color="{TEAL}"/><stop offset="1" stop-color="{TEAL_DEEP}"/>
  </linearGradient>
  <radialGradient id="{uid}hl" cx="0.22" cy="0.12" r="0.75">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.38"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="{uid}sheet" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#E6FFFA"/>
  </linearGradient>
  <linearGradient id="{uid}gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD_DEEP}"/>
  </linearGradient>
</defs>"""


# Document sheet with a folded top-right corner (512 x 512 grid).
SHEET = ("M184 100 H300 L364 164 V380 C364 398 350 412 332 412 H184 "
         "C166 412 152 398 152 380 V132 C152 114 166 100 184 100 Z")
FOLD = "M300 100 V140 C300 153 311 164 324 164 H364 Z"
# A signature flourish written across the sheet, then a gold signing line underneath.
SIGNATURE = ("M190 320 C204 284 222 278 228 302 C233 324 244 330 258 304 "
             "C266 290 277 290 279 306 C281 322 296 324 312 306")


def mark(uid):
    """The icon: gradient squircle, soft-shadowed document sheet, text lines, teal signature, gold signing line."""
    return (defs(uid)
            + f'<rect x="0" y="0" width="512" height="512" rx="118" fill="url(#{uid}bg)"/>'
            + f'<rect x="0" y="0" width="512" height="512" rx="118" fill="url(#{uid}hl)"/>'
            + f'<rect x="6" y="6" width="500" height="500" rx="113" fill="none" stroke="#FFFFFF" stroke-opacity="0.14" stroke-width="4"/>'
            + f'<path d="{SHEET}" fill="#042F2C" fill-opacity="0.10" transform="translate(0 20)"/>'
            + f'<path d="{SHEET}" fill="#042F2C" fill-opacity="0.14" transform="translate(0 10)"/>'
            + f'<path d="{SHEET}" fill="url(#{uid}sheet)"/>'
            + f'<path d="{FOLD}" fill="#99F6E4"/>'
            + f'<rect x="190" y="190" width="120" height="18" rx="9" fill="{TEAL}" fill-opacity="0.30"/>'
            + f'<rect x="190" y="228" width="84" height="18" rx="9" fill="{TEAL}" fill-opacity="0.30"/>'
            + f'<path d="{SIGNATURE}" fill="none" stroke="{TEAL}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>'
            + f'<rect x="188" y="350" width="140" height="12" rx="6" fill="url(#{uid}gold)"/>')


def svg(w, h, body, vb=None):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb or f"0 0 {w} {h}"}" width="{w}" height="{h}">{body}</svg>'


def wordmark_paths(text):
    font = TTFont(FONT)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    x, parts = 0, []
    for ch in text:
        g = gs[cmap[ord(ch)]]
        pen = SVGPathPen(gs)
        g.draw(pen)
        if pen.getCommands():
            parts.append((x, pen.getCommands()))
        x += g.width
    return parts, x, font["OS/2"].sxHeight


TRACKING = -12  # font units, slightly tight


def layout():
    docu, docu_w, xh = wordmark_paths("docu")
    mate, mate_w, _ = wordmark_paths("mate")
    s = 26.0 / xh                      # x-height 26 px on a 64 px tall logo
    gap, icon = 16, 64
    width = int(icon + gap + (docu_w + mate_w + TRACKING * 7) * s + 6)

    def group(parts, offset):
        return "".join(f'<path transform="translate({x + offset + i * TRACKING},0)" d="{d}"/>'
                       for i, (x, d) in enumerate(parts))
    return s, icon, gap, width, group(docu, 0), group(mate, docu_w + TRACKING * 4)


def logo(ink, mate_fill, uid):
    """Icon + wordmark "documate" ("mate" in the brand colour), 64 px tall."""
    s, icon, gap, width, docu, mate = layout()
    body = (f'<svg x="0" y="0" width="64" height="64" viewBox="0 0 512 512">{mark(uid)}</svg>'
            f'<g transform="translate({icon + gap},45) scale({s:.5f},{-s:.5f})">'
            f'<g fill="{ink}">{docu}</g><g fill="{mate_fill}">{mate}</g></g>')
    return svg(width, 64, body)


def jsx(svg_text):
    """SVG attribute names React accepts as-is, except the few that need camelCase."""
    for a, b in (("stop-color", "stopColor"), ("stop-opacity", "stopOpacity"), ("fill-opacity", "fillOpacity"),
                 ("stroke-opacity", "strokeOpacity"), ("stroke-width", "strokeWidth"),
                 ("stroke-linecap", "strokeLinecap"), ("stroke-linejoin", "strokeLinejoin")):
        svg_text = svg_text.replace(a + "=", b + "=")
    return svg_text


def react_logo():
    """BrandingLogo: "docu" follows the surrounding text colour, "mate" is brand teal (lighter in dark mode)."""
    s, icon, gap, width, docu, mate = layout()
    inner = jsx(f'<svg x="0" y="0" width="64" height="64" viewBox="0 0 512 512">{mark("documateLogo")}</svg>'
                f'<g transform="translate({icon + gap},45) scale({s:.5f},{-s:.5f})">'
                f'<g fill="currentColor">{docu}</g>'
                f'<g className="text-documenso-600 dark:text-documenso-400" fill="currentColor">{mate}</g></g>')
    return ("import type { SVGAttributes } from 'react';\n\n"
            "export type LogoProps = SVGAttributes<SVGSVGElement>;\n\n"
            "// Documate wordmark — generated by documate/brand/gen.py. Do not edit by hand.\n"
            "export const BrandingLogo = ({ ...props }: LogoProps) => {\n"
            "  return (\n"
            f'    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" {{...props}}>\n'
            f"      {inner}\n"
            "    </svg>\n  );\n};\n")


def react_icon():
    inner = jsx(mark("documateIcon"))
    return ("import type { SVGAttributes } from 'react';\n\n"
            "export type LogoProps = SVGAttributes<SVGSVGElement>;\n\n"
            "// Documate mark — generated by documate/brand/gen.py. Do not edit by hand.\n"
            "export const BrandingLogoIcon = ({ ...props }: LogoProps) => {\n"
            "  return (\n"
            '    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" {...props}>\n'
            f"      {inner}\n"
            "    </svg>\n  );\n};\n")


def og_image():
    """1270 x 760 social preview: soft teal field, centred logo."""
    s, icon, gap, width, docu, mate = layout()
    scale = 760 / width
    x = (1270 - width * scale) / 2
    y = (760 - 64 * scale) / 2
    body = (f'<rect width="1270" height="760" fill="#F0FDFA"/>'
            f'<g transform="translate({x:.1f},{y:.1f}) scale({scale:.4f})">'
            f'<svg x="0" y="0" width="64" height="64" viewBox="0 0 512 512">{mark("og")}</svg>'
            f'<g transform="translate({icon + gap},45) scale({s:.5f},{-s:.5f})">'
            f'<g fill="{INK_LIGHT}">{docu}</g><g fill="{TEAL}">{mate}</g></g></g>')
    return svg(1270, 760, body)


def logo_group(uid, x, y, height, ink=INK_LIGHT, mate_fill=TEAL):
    """The full logo placed at (x, y) with the given pixel height (for composite images)."""
    s, icon, gap, width, docu, mate = layout()
    k = height / 64
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})">'
            f'<svg x="0" y="0" width="64" height="64" viewBox="0 0 512 512">{mark(uid)}</svg>'
            f'<g transform="translate({icon + gap},45) scale({s:.5f},{-s:.5f})">'
            f'<g fill="{ink}">{docu}</g><g fill="{mate_fill}">{mate}</g></g></g>'), width * k


def rings(cx, cy, n, step, base, opacity):
    """Concentric squircle outlines echoing the mark — the signature background texture."""
    out = []
    for i in range(n):
        r = base + i * step
        out.append(f'<rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" rx="{r * 0.46:.1f}" '
                   f'fill="none" stroke="{TEAL}" stroke-opacity="{opacity * (1 - i / n):.3f}" stroke-width="2"/>')
    return "".join(out)


def background_pattern():
    """2366 x 1677 page background (sign-in and error pages): soft teal glow + faint squircle rings."""
    w, h = 2366, 1677
    body = (f'<defs><radialGradient id="g" cx="0.5" cy="0.45" r="0.55">'
            f'<stop offset="0" stop-color="{TEAL_LIGHT}" stop-opacity="0.16"/>'
            f'<stop offset="1" stop-color="{TEAL_LIGHT}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="{w}" height="{h}" fill="#FFFFFF" fill-opacity="0"/>'
            f'<rect width="{w}" height="{h}" fill="url(#g)"/>'
            + rings(w / 2, h * 0.45, 14, 46, 120, 0.16))
    return svg(w, h, body)


def share_frame():
    """1200 x 630 share card frame. The app draws the signature inside the white panel at (307,173) 590 x 337."""
    lg, lw = logo_group("sf", 0, 0, 48)
    lg = lg.replace('translate(0.0,0.0)', f'translate({1200 - 40 - lw:.1f},{630 - 40 - 48})')
    body = (f'<defs><radialGradient id="g" cx="0.5" cy="0.5" r="0.6">'
            f'<stop offset="0" stop-color="{TEAL_LIGHT}" stop-opacity="0.14"/>'
            f'<stop offset="1" stop-color="{TEAL_LIGHT}" stop-opacity="0"/></radialGradient>'
            f'<filter id="s" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="6" stdDeviation="10" '
            f'flood-color="#0F172A" flood-opacity="0.08"/></filter></defs>'
            f'<rect width="1200" height="630" fill="#FFFFFF"/><rect width="1200" height="630" fill="url(#g)"/>'
            + rings(600, 315, 9, 40, 80, 0.10)
            + f'<rect x="287" y="92" width="630" height="440" rx="28" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="2" filter="url(#s)"/>'
            f'<rect x="307" y="150" width="590" height="3" rx="1.5" fill="{TEAL}"/>'
            f'<rect x="307" y="173" width="590" height="337" rx="18" fill="#FFFFFF" stroke="#99F6E4" stroke-width="2"/>'
            + lg)
    return svg(1200, 630, body)


if __name__ == "__main__":
    open("background-pattern.svg", "w").write(background_pattern())
    open("share-frame.svg", "w").write(share_frame())
    open("icon.svg", "w").write(svg(512, 512, mark("i")))
    open("logo.svg", "w").write(logo(INK_LIGHT, TEAL, "l"))
    open("logo_dark.svg", "w").write(logo(INK_DARK, TEAL_LIGHT, "d"))
    open("og.svg", "w").write(og_image())
    open("branding-logo.tsx", "w").write(react_logo())
    open("branding-logo-icon.tsx", "w").write(react_icon())
    print("wrote icon.svg logo.svg logo_dark.svg og.svg share-frame.svg background-pattern.svg branding-logo.tsx branding-logo-icon.tsx")
