#!/usr/bin/env python3
"""Turn an upstream Documenso checkout into Documate. Fails loudly on anything unexpected.

Usage:  python3 rebrand.py <upstream-checkout>      (needs rsvg-convert and Pillow; build.sh runs it in a container)

What it does, in order:
  1. exact edits      — specific files where a plain rename is not enough (logo images, promo links, footer, meta);
  2. colour scheme    — the Documenso lime palette becomes the Documate teal palette (CSS vars, Tailwind, theme);
  3. names, links     — the visible word, documenso.com links and addresses, in app code AND translation catalogues,
                        with the same rule on both sides so Lingui message ids still match their translations;
  4. assets           — logo components, favicons, app icons, email/PDF logo, social images, backgrounds;
  5. residual check   — anything still saying Documenso in shipped UI code fails the build.

Never touched: packages/ee (Documenso's commercial licence covers that folder), copyright headers in source files,
code identifiers (isDocumensoCloud, IS_DOCUMENSO_CLOUD, @documenso/* packages), wire-level names other systems
depend on (X-Documenso-* webhook/email headers, recipient.N@documenso.com template placeholders, the
licence-server URL, seeded service-account emails).
"""
import io
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(sys.argv[1]).resolve()
HERE = Path(__file__).resolve().parent
BRAND = HERE / "brand"

NAME = "Documate"
DOMAIN = "documate.dontgetbroke.com"
SOURCE_URL = "https://github.com/MYKLWCS/documate"
SUPPORT_EMAIL = "contracts@dollarloanz.com"

changes = []


def log(msg):
    changes.append(msg)
    print("rebrand:", msg)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")


def edit(rel, old, new, count=1, regex=False):
    """Replace exactly `count` occurrences (literal unless regex=True) or fail."""
    src = read(rel)
    if regex:
        found = len(re.findall(old, src, flags=re.S))
        out = re.sub(old, new, src, flags=re.S)
    else:
        found = src.count(old)
        out = src.replace(old, new)
    if found != count:
        sys.exit(f"rebrand: FAILED {rel}: expected {count} match(es) of {old[:80]!r}, found {found}")
    write(rel, out)
    log(f"edit {rel} ({found})")


# ---------------------------------------------------------------------------------------------------------------
# 1. exact edits
# ---------------------------------------------------------------------------------------------------------------
APP = "apps/remix/app"

# Mobile menu: Documenso PNG logo -> Documate logo component; Documenso, Inc. copyright -> source/licence notice.
edit(f"{APP}/components/general/app-nav-mobile.tsx",
     "import LogoImage from '@documenso/assets/logo.png';",
     "import { BrandingLogo } from '~/components/general/branding-logo';")
edit(f"{APP}/components/general/app-nav-mobile.tsx",
     r'<img src=\{LogoImage\} alt="Documenso Logo" className="dark:invert" width=\{170\} height=\{25\} />',
     '<BrandingLogo className="h-7 w-auto" />', regex=True)
edit(f"{APP}/components/general/app-nav-mobile.tsx",
     r"<p className=\"text-muted-foreground text-sm\">\s*© \{new Date\(\)\.getFullYear\(\)\} Documenso, Inc\.\s*<br />\s*"
     r"<Trans>All rights reserved\.</Trans>\s*</p>",
     '<p className="text-muted-foreground text-sm">\n            <a href="' + SOURCE_URL + '" target="_blank" '
     'rel="noopener noreferrer" className="hover:underline">\n              ' + NAME + ' · AGPL-3.0 · Source code\n'
     '            </a>\n          </p>', regex=True)

# Public profile header: Documenso PNG icon -> Documate mark component.
edit(f"{APP}/routes/_profile+/_layout.tsx",
     "import LogoIcon from '@documenso/assets/logo_icon.png';",
     "import { BrandingLogoIcon } from '~/components/general/branding-logo-icon';")
edit(f"{APP}/routes/_profile+/_layout.tsx",
     r"<img\s+src=\{LogoIcon\}\s+alt=\"Documenso Logo\"\s+width=\{48\}\s+height=\{48\}\s+"
     r"className=\"h-10 w-auto sm:hidden dark:invert\"\s*/>",
     '<BrandingLogoIcon className="h-10 w-auto sm:hidden" />', regex=True)

# Signer pages: drop the "Want to send slick signing links like this one? Check out Documenso" promo.
edit(f"{APP}/routes/_recipient+/sign.$token+/_index.tsx",
     r"\(\s*<p className=\"mt-36 text-muted-foreground/60 text-sm\">\s*<Trans>\s*Want to send slick signing links like this one\?"
     r".*?</Trans>\s*</p>\s*\)",
     "null", count=2, regex=True)

# "Powered by" badges: wordmark text (the logo's teal half would vanish on the teal badge); link -> source code.
for f in (f"{APP}/components/general/document-signing/document-signing-page-view-v2.tsx",
          f"{APP}/components/general/document-signing/document-signing-mobile-widget.tsx",
          f"{APP}/components/embed/embed-document-signing-page-v1.tsx",
          f"{APP}/components/embed/embed-direct-template-client-page.tsx"):
    edit(f, '<BrandingLogo className="ml-2 inline-block h-[14px]" />',
         f'<span className="ml-1 font-semibold">{NAME}</span>')
edit(f"{APP}/routes/embed+/v1+/multisign+/_index.tsx", '<BrandingLogo className="ml-2 inline-block h-[14px]" />',
     f'<span className="ml-1 font-semibold">{NAME}</span>', count=2)

# Sign-up side panel: the upstream founder's profile card ("User profiles are here!") -> Documate brand card.
edit(f"{APP}/components/forms/signup.tsx",
     "import { UserProfileTimur } from '~/components/general/user-profile-timur';",
     "import { BrandingLogo } from '~/components/general/branding-logo';")
edit(f"{APP}/components/forms/signup.tsx",
     r'<div className="rounded-2xl border bg-background px-4 py-1 font-medium text-sm">\s*<Trans>User profiles are here!</Trans>\s*</div>'
     r'\s*<div className="w-full max-w-md">\s*<UserProfileTimur rows=\{2\} className="rounded-2xl border border-border bg-background shadow-md" />\s*</div>',
     '<div className="w-full max-w-md rounded-2xl border border-border bg-background p-8 text-center shadow-md">\n'
     '            <BrandingLogo className="mx-auto h-10 w-auto" />\n'
     '            <p className="mt-4 text-muted-foreground text-sm">\n'
     '              <Trans>Secure electronic signing for your contracts and agreements.</Trans>\n'
     '            </p>\n          </div>', regex=True)

# Sign-in, sign-up and password pages: Documate logo above the card; background rings stay teal in dark mode
# (upstream inverts the image, which would turn teal into coral).
LAYOUT = f"{APP}/routes/_unauthenticated+/_layout.tsx"
edit(LAYOUT, "import { Outlet } from 'react-router';",
     "import { Outlet } from 'react-router';\n\nimport { BrandingLogo } from '~/components/general/branding-logo';")
edit(LAYOUT, '<div className="relative w-full flex items-center justify-center">\n          <Outlet />',
     '<div className="relative flex w-full flex-col items-center justify-center">\n'
     '          <BrandingLogo className="mb-8 h-10 w-auto text-foreground" />\n          <Outlet />')
edit(LAYOUT, 'className="dark:brightness-95 dark:contrast-[70%] dark:invert dark:sepia"', 'className="dark:opacity-60"')
edit(f"{APP}/components/general/generic-error-layout.tsx", 'dark:contrast-[70%] dark:invert dark:sepia"', 'dark:opacity-60"')

# Email footer: no Documenso, Inc. postal address on our emails (company details come from organisation branding).
edit("packages/email/template-components/template-footer.tsx",
     r"\{!branding\.brandingEnabled && \(\s*<Text className=\"my-8 text-muted-foreground text-sm\">\s*Documenso, Inc\.\s*<br />\s*"
     r"2261 Market Street, #5211, San Francisco, CA 94114, USA\s*</Text>\s*\)\}",
     "", regex=True)

# Page meta: our own title/description; signing system pages are never indexed.
write(f"{APP}/utils/meta.ts", f"""import {{ NEXT_PUBLIC_WEBAPP_URL }} from '@documenso/lib/constants/app';
import {{ i18n, type MessageDescriptor }} from '@lingui/core';

export const appMetaTags = (title?: MessageDescriptor) => {{
  const description = '{NAME} — secure electronic signing for your contracts and agreements.';

  return [
    {{
      title: title ? `${{i18n._(title)}} - {NAME}` : '{NAME}',
    }},
    {{
      name: 'description',
      content: description,
    }},
    {{
      name: 'application-name',
      content: '{NAME}',
    }},
    {{
      name: 'robots',
      content: 'noindex, nofollow',
    }},
    {{
      name: 'theme-color',
      content: '#0D9488',
    }},
    {{
      property: 'og:title',
      content: '{NAME}',
    }},
    {{
      property: 'og:description',
      content: description,
    }},
    {{
      property: 'og:image',
      content: `${{NEXT_PUBLIC_WEBAPP_URL()}}/opengraph-image.jpg`,
    }},
    {{
      property: 'og:type',
      content: 'website',
    }},
    {{
      name: 'twitter:card',
      content: 'summary_large_image',
    }},
    {{
      name: 'twitter:description',
      content: description,
    }},
    {{
      name: 'twitter:image',
      content: `${{NEXT_PUBLIC_WEBAPP_URL()}}/opengraph-image.jpg`,
    }},
  ];
}};
""")
log(f"write {APP}/utils/meta.ts")

# Share page meta copy and its off-site redirect.
SHARE = f"{APP}/routes/_share+/share.$slug.tsx"
edit(SHARE, "'Documenso - Join the open source signing revolution'", f"'{NAME} - Secure electronic signing'")
edit(SHARE, "'I just signed a document in style with Documenso!'", "'A document was signed with " + NAME + ".'")
edit(SHARE, "'I just signed with Documenso!'", "'Signed with " + NAME + "'", count=2)
edit(SHARE, "throw redirect('https://documenso.com');", "throw redirect('/');")

# Licence wording without the vendor name (admin-only; meaning unchanged).
edit(f"{APP}/components/general/admin-license-card.tsx", "<Trans>Documenso License</Trans>", "<Trans>Enterprise License</Trans>")
edit(f"{APP}/root.tsx", "<Trans>This is an expired license instance of Documenso</Trans>",
     "<Trans>This instance's enterprise license has expired</Trans>")

# Static files served as-is.
write("apps/remix/public/robots.txt", "User-agent: *\nDisallow: /\n")
write("apps/remix/public/.well-known/security.txt",
      f"# Report security issues privately via GitHub Security Advisories.\n"
      f"Contact: {SOURCE_URL}/security/advisories/new\n"
      f"Preferred-Languages: en\nCanonical: https://{DOMAIN}/.well-known/security.txt\n")
MANIFEST = ('{\n  "name": "' + NAME + '",\n  "short_name": "' + NAME + '",\n  "icons": [\n'
            '    { "src": "./android-chrome-192x192.png", "sizes": "192x192", "type": "image/png" },\n'
            '    { "src": "./android-chrome-512x512.png", "sizes": "512x512", "type": "image/png" }\n  ],\n'
            '  "theme_color": "#0D9488",\n  "background_color": "#FFFFFF",\n  "display": "standalone"\n}\n')
for m in ("apps/remix/public/site.webmanifest", "packages/assets/site.webmanifest"):
    write(m, MANIFEST)
log("write robots.txt, security.txt, site.webmanifest x2")

# ---------------------------------------------------------------------------------------------------------------
# 2. colour scheme: Documenso lime -> Documate teal (same tokens as Chatmate)
# ---------------------------------------------------------------------------------------------------------------
LIME_HSL = "95.08 71.08% 67.45%"
theme = read("packages/ui/styles/theme.css")
SPLIT = ".dark:not(.dark-mode-disabled) {"
if theme.count(SPLIT) != 1:
    sys.exit("rebrand: FAILED theme.css dark block not found")
light, dark = theme.split(SPLIT, 1)
light = (light.replace(f"--primary: {LIME_HSL};", "--primary: 175 84% 32%;")
              .replace("--primary-foreground: 95.08 71.08% 10%;", "--primary-foreground: 0 0% 100%;")
              .replace(f"--ring: {LIME_HSL};", "--ring: 175 84% 32%;")
              .replace(f"--field-card-border: {LIME_HSL};", "--field-card-border: 172 66% 50%;")
              .replace("--field-card: 95 74% 90%;", "--field-card: 166 76% 94%;")
              .replace("--card-border-tint: 112 205 159;", "--card-border-tint: 45 212 191;"))
dark = (dark.replace(f"--primary: {LIME_HSL};", "--primary: 172 66% 50%;")
            .replace("--primary-foreground: 95.08 71.08% 10%;", "--primary-foreground: 176 70% 10%;")
            .replace(f"--secondary-foreground: {LIME_HSL};", "--secondary-foreground: 172 66% 50%;")
            .replace(f"--accent-foreground: {LIME_HSL};", "--accent-foreground: 172 66% 50%;")
            .replace(f"--ring: {LIME_HSL};", "--ring: 172 66% 50%;")
            .replace(f"--field-card-border: {LIME_HSL};", "--field-card-border: 172 66% 50%;")
            .replace("--card-border-tint: 112 205 159;", "--card-border-tint: 45 212 191;"))
theme = light + SPLIT + dark
left = theme.count("95.08 71.08%") + theme.count("95 74% 90%")
if left:
    sys.exit(f"rebrand: FAILED theme.css still has {left} lime colour value(s)")
write("packages/ui/styles/theme.css", theme)
log("theme.css: lime -> teal (light + dark)")

TEAL_SCALE = {"DEFAULT": "#0D9488", "50": "#F0FDFA", "100": "#CCFBF1", "200": "#99F6E4", "300": "#5EEAD4",
              "400": "#2DD4BF", "500": "#14B8A6", "600": "#0D9488", "700": "#0F766E", "800": "#115E59",
              "900": "#134E4A", "950": "#042F2E"}
tw = read("packages/tailwind-config/index.cjs")
m = re.search(r"documenso: \{\n(.*?)\n\s*\},", tw, flags=re.S)
if not m:
    sys.exit("rebrand: FAILED tailwind palette block not found")
block = m.group(1)
for k, v in TEAL_SCALE.items():
    block, n = re.subn(rf"(\b{k}: )'#[0-9A-Fa-f]{{6}}'", rf"\g<1>'{v}'", block)
    if n != 1:
        sys.exit(f"rebrand: FAILED tailwind palette key {k}")
write("packages/tailwind-config/index.cjs", tw[:m.start(1)] + block + tw[m.end(1):])
log("tailwind 'documenso' palette -> teal scale (class names unchanged)")

edit("packages/lib/constants/theme.ts", "fieldCard: '#e2f8d3',", "fieldCard: '#ecfdf8',")
edit("packages/lib/constants/theme.ts", "fieldCardBorder: '#a2e771',", "fieldCardBorder: '#2dd4bf',")
edit("packages/lib/constants/theme.ts", "primary: '#a2e771',", "primary: '#0d9488',")
edit("packages/lib/constants/theme.ts", "primaryForeground: '#162c07',", "primaryForeground: '#ffffff',")
edit("packages/lib/constants/theme.ts", "ring: '#a2e771',", "ring: '#0d9488',")
for f, n in ((f"{APP}/components/general/settings-upsell/branding-upsell.tsx", 1),
             (f"{APP}/components/general/settings-upsell/sso-portal-upsell.tsx", 2)):
    edit(f, "#A2E771", "#0D9488", count=n)

# ---------------------------------------------------------------------------------------------------------------
# 3. names, links, addresses — one rule for code and catalogues
# ---------------------------------------------------------------------------------------------------------------
WORD = re.compile(r"(?<![A-Za-z0-9_$\-])Documenso(?![A-Za-z0-9_$])")  # "Documenso-Konto" yes, "X-Documenso-Secret" no
PHRASES = [  # whitespace-tolerant so multi-line JSX and single-line catalogue entries change identically
    (re.compile(r"Your\s+Documenso\s+instance"), "Your instance"),
    (re.compile(r"Documenso,\s+Inc\."), NAME),
    (re.compile(r"Documenso\s+Cloud"), f"{NAME} Cloud"),
]
URL = re.compile(r"https?://(?!license\.)(?:[a-z-]+\.)?documenso\.com(?:/[^\s'\"`<>)\]]*[^\s'\"`<>)\].,])?")
SHORT = re.compile(r"https?://documen\.so(?:/[A-Za-z0-9_/-]*)?")
HOST = re.compile(r"(?<![@A-Za-z0-9.-])(?:stg-)?app\.documenso\.com")
EMAIL = re.compile(r"(?<![A-Za-z0-9.+$}-])([a-z0-9][a-z0-9.+-]*)@documenso\.com")
KEEP_EMAIL = {"deleted-account", "serviceaccount"}   # seeded service accounts the code looks up


def email_sub(m):
    local = m.group(1)
    if local in KEEP_EMAIL:
        return m.group(0)
    if local in {"support", "hi", "noreply", "security"}:
        return SUPPORT_EMAIL
    return f"{local}@example.com"


def rename(text):
    for rx, rep in PHRASES:
        text = rx.sub(rep, text)
    text = URL.sub(SOURCE_URL, text)
    text = SHORT.sub(SOURCE_URL, text)
    text = HOST.sub(DOMAIN, text)
    text = EMAIL.sub(email_sub, text)
    return WORD.sub(NAME, text)


SCOPE = ["apps/remix/app", "apps/remix/server", "packages/lib", "packages/ui", "packages/email",
         "packages/trpc", "packages/auth", "packages/api", "packages/signing"]
SKIP_DIR = {"node_modules", "translations", "__tests__", "e2e"}
EXTS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".html"}


def code_files():
    for base in SCOPE:
        for dirpath, dirnames, filenames in os.walk(ROOT / base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR]
            for fn in filenames:
                p = Path(dirpath) / fn
                if p.suffix in EXTS and ".test." not in fn and ".spec." not in fn:
                    yield p


def strip_header(text):
    """Leave a leading licence/copyright comment block untouched."""
    m = re.match(r"\s*(/\*.*?\*/\s*)", text, flags=re.S)
    if m and re.search(r"copyright|licen[cs]e", m.group(1), flags=re.I):
        return text[:m.end()], text[m.end():]
    return "", text


n_files = 0
for p in code_files():
    src = p.read_text(encoding="utf-8")
    head, body = strip_header(src)
    out = head + rename(body)
    if out != src:
        p.write_text(out, encoding="utf-8")
        n_files += 1
log(f"renamed brand word/links/addresses in {n_files} code files")
write("docker/start.sh", rename(read("docker/start.sh")))   # container start-up banner and log lines
log("renamed docker/start.sh banner")

# Translation catalogues: same rule on msgid (so ids still match the renamed code) and on msgstr.
STR = re.compile(r'^(msgid|msgstr|msgctxt|")(.*)$')
n_cat = 0
for po in sorted((ROOT / "packages/lib/translations").glob("*/web.po")):
    lines = po.read_text(encoding="utf-8").split("\n")
    out = [rename(ln) if STR.match(ln) else ln for ln in lines]
    if out != lines:
        po.write_text("\n".join(out), encoding="utf-8")
        n_cat += 1
log(f"renamed brand word/links in {n_cat} translation catalogues")

# Default signing reason and passkey/2FA labels are covered by the word rule; assert they changed.
for rel, needle in (("packages/lib/constants/app.ts", f"'Signed by {NAME}'"),
                    ("packages/lib/utils/authenticator.ts", f"rpName: '{NAME}'"),
                    ("packages/lib/server-only/2fa/setup-2fa.ts", f"ISSUER = '{NAME}'")):
    if needle not in read(rel):
        sys.exit(f"rebrand: FAILED expected {needle} in {rel}")

# ---------------------------------------------------------------------------------------------------------------
# 4. assets
# ---------------------------------------------------------------------------------------------------------------
for comp in ("branding-logo.tsx", "branding-logo-icon.tsx"):
    write(f"{APP}/components/general/{comp}", (BRAND / comp).read_text())
log("logo components replaced")


def render(svg, width=None, height=None):
    args = ["rsvg-convert", "--format=png"]
    if width:
        args += ["-w", str(width)]
    if height:
        args += ["-h", str(height)]
    return subprocess.run(args + [str(BRAND / svg)], check=True, capture_output=True).stdout


def put(rel, data):
    (ROOT / rel).write_bytes(data)


PUBLICS = ["apps/remix/public", "packages/assets"]
for base in PUBLICS:
    for name, size in (("favicon-16x16.png", 16), ("favicon-32x32.png", 32), ("apple-touch-icon.png", 180),
                       ("android-chrome-192x192.png", 192), ("android-chrome-512x512.png", 512)):
        put(f"{base}/{name}", render("icon.svg", size, size))
    ico = io.BytesIO()
    Image.open(io.BytesIO(render("icon.svg", 256, 256))).save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    put(f"{base}/favicon.ico", ico.getvalue())
    og = Image.open(io.BytesIO(render("og.svg", 1270, 760))).convert("RGB")
    buf = io.BytesIO()
    og.save(buf, format="JPEG", quality=90)
    put(f"{base}/opengraph-image.jpg", buf.getvalue())
put("packages/assets/logo.png", render("logo.svg", height=320))
put("packages/assets/logo_icon.png", render("icon.svg", 320, 320))
for rel in ("apps/remix/public/static/logo.png", "packages/assets/static/logo.png"):   # emails + PDF certificate
    put(rel, render("logo.svg", height=110))
put("apps/remix/public/static/og-share-frame2.png", render("share-frame.svg", 1200, 630))
put("packages/assets/static/og-share-frame.png", render("share-frame.svg", 1200, 630))
bg = Image.open(io.BytesIO(render("background-pattern.svg", 2366, 1677))).convert("RGBA")
buf = io.BytesIO()
bg.save(buf, format="PNG", optimize=True)
put("packages/assets/images/background-pattern.png", buf.getvalue())


def teal_hue(rel):
    """Shift the lime accents of a stock icon to Documate teal; whites, greys and reds stay as they are."""
    im = Image.open(ROOT / rel).convert("RGBA")
    alpha = im.getchannel("A")
    h, s, v = im.convert("RGB").convert("HSV").split()
    h = h.point(lambda x: 123 if 40 <= x <= 100 else x)
    out = Image.merge("HSV", (h, s, v)).convert("RGB")
    out.putalpha(alpha)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    (ROOT / rel).write_bytes(buf.getvalue())


for rel in ("apps/remix/public/static/completed.png", "packages/assets/static/completed.png",
            "apps/remix/public/static/mail-open.png", "packages/assets/images/signing-celebration.png",
            "packages/assets/images/community-cards.png"):
    teal_hue(rel)
badge = read("apps/remix/public/static/premium-user-badge.svg")
write("apps/remix/public/static/premium-user-badge.svg", badge.replace("#5AAE30", "#0F766E").replace("#96D766", "#2DD4BF"))
log("assets: favicons, app icons, logo PNGs, OG/share images, background pattern, teal icons")

# ---------------------------------------------------------------------------------------------------------------
# 5. residual check — nothing shipped to users may still say Documenso
# ---------------------------------------------------------------------------------------------------------------
ALLOW = re.compile(r"X-Documenso-|license\.documenso\.com|@documenso\.com`|recipient\\\.|"
                   r"deleted-account@documenso|serviceaccount@documenso")
bad = []
for p in code_files():
    head, body = strip_header(p.read_text(encoding="utf-8"))
    for i, ln in enumerate(body.split("\n"), 1):
        code = re.sub(r"//.*$", "", ln)            # comments are not shipped as UI text
        if code.strip().startswith(("*", "/*")):
            continue
        if (WORD.search(code) or URL.search(code) or SHORT.search(code)) and not ALLOW.search(code):
            bad.append(f"{p.relative_to(ROOT)}:{i}: {ln.strip()[:120]}")
for po in (ROOT / "packages/lib/translations").glob("*/web.po"):
    for i, ln in enumerate(po.read_text(encoding="utf-8").split("\n"), 1):
        if STR.match(ln) and WORD.search(ln):
            bad.append(f"{po.relative_to(ROOT)}:{i}: {ln[:120]}")
for name in ("site.webmanifest", "robots.txt", ".well-known/security.txt"):
    if re.search("documenso", read(f"apps/remix/public/{name}"), flags=re.I):
        bad.append(f"apps/remix/public/{name}")
if bad:
    print("\n".join(bad))
    sys.exit(f"rebrand: FAILED {len(bad)} residual Documenso reference(s) in shipped code")
print(f"rebrand: OK — {len(changes)} steps, no residual brand references in shipped code")
