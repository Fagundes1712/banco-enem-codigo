---
name: Banco ENEM
description: Apple Human Interface Guidelines system. SF Pro via the system stack, white/black grounds, a single system-blue accent, 18px continuous-corner cards, pill buttons, iOS segmented control and alert.
colors:
  # Light
  bg: "#ffffff"          # page ground
  bg-2: "#f5f5f7"        # card / panel surface (apple.com)
  label: "#1d1d1f"       # primary text
  label-2: "#6e6e73"     # secondary text
  label-3: "#86868b"     # tertiary text
  sep: "#d2d2d7"         # hairline separator
  blue: "#0071e3"        # the only accent
  blue-link: "#0066cc"
  ok: "#34c759"
  bad: "#ff3b30"

  # Dark
  bg-dark: "#000000"
  bg-2-dark: "#1d1d1f"
  label-dark: "#f5f5f7"
  label-2-dark: "#86868b"
  sep-dark: "#424245"
  blue-dark: "#2997ff"
  ok-dark: "#30d158"
  bad-dark: "#ff453a"

typography:
  sans: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
  mono: 'ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace'
  body: "17px / 1.4714 / 400"
  h1: "clamp(36px, 4.5vw, 48px) / 1.07 / 600 / -0.02em"
  h2: "clamp(28px, 3vw, 36px) / 1.1 / 600 / -0.015em"
  h3: "20px / 1.3 / 600 / -0.01em"

radius:
  sm: "12px"
  md: "18px"
  pill: "980px"

spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "32px"
  xl: "48px"
  2xl: "80px"
---

# Design System: Apple HIG

Reference: [developer.apple.com/design](https://developer.apple.com/design) and the Human Interface Guidelines. `styles.css` is the source of truth; this file is the portable description of it. If a token here disagrees with the CSS, the CSS wins — fix this file.

The old **Neo Kinpaku** system (lacquer black, kinpaku gold, verdigris patina, OKLCH tokens) is retired. Do not reintroduce its colors, uppercase tracked labels, or decorative display fonts.

## 1. Overview

A study tool used on a phone, often at night, often on a bad connection. The interface stays out of the way: white or black ground, one accent, text-first hierarchy, native-feeling controls. Personality comes from typography and spacing, not from color or texture.

Principles:

1. **Content first.** The question text is the largest thing on the screen. Chrome is quiet.
2. **One accent.** System blue `#0071e3` / `#2997ff` marks the primary action, selection and focus. Nothing else competes.
3. **Familiar controls.** Tabs look like an iOS segmented control, buttons like iOS pills, the confirm step like an iOS alert. No custom affordance requires learning.
4. **Both themes are first-class.** Light and dark are designed together through `prefers-color-scheme`.

## 2. Colors

Only tokens declared in `:root` and the dark `@media` block exist. Never write a raw hex in a component rule.

### Ground and surfaces

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--bg` | `#ffffff` | `#000000` | page ground |
| `--bg-2` | `#f5f5f7` | `#1d1d1f` | cards, panels, inputs |
| `--bar-bg` | `rgb(255 255 255 / .8)` | `rgb(0 0 0 / .8)` | blurred sticky bar |
| `--sel-bg` / `--sel-ink` | `#ffffff` / `#1d1d1f` | `#636366` / `#ffffff` | selected segment |

### Text

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--label` | `#1d1d1f` | `#f5f5f7` | headings, body |
| `--label-2` | `#6e6e73` | `#86868b` | metadata, notes |
| `--label-3` | `#86868b` | `#a1a1a6` | faintest labels |

### Accent and state

- `--blue` `#0071e3` / `#2997ff` — primary action, selection ring, focus ring. `--blue-link` for inline links.
- `--ok` `#34c759` / `#30d158` with `--ok-ink` on `--ok-bg` — correct answers.
- `--bad` `#ff3b30` / `#ff453a` with `--bad-ink` on `--bad-bg` — wrong answers.
- `--nil-bg` — unanswered tag.
- `--fill` / `--fill-2` — translucent gray for secondary buttons and segmented rails.

Rules:

- Tinted backgrounds for tags, never a full saturated fill behind text.
- Color is never the only signal: the correction tags say "Acertou", "Errou", "Em branco".
- No gradients, no colored shadows, no glassmorphism beyond the header blur.

## 3. Typography

- **Family:** `--f-sans` puts the real **SF Pro** first (`-apple-system`, `BlinkMacSystemFont`), then **Inter** (Google Fonts) for Windows/Android. SF Pro cannot be redistributed, so Inter is the sanctioned substitute — never add another display face.
- **Scale:** body `17px/1.4714`, h1 `48px/1.07/600/-0.02em`, h2 `36px/1.1/600/-0.015em`, h3 `20px/1.3/600/-0.01em`. Below h3 use 15px or 13px, weights 400–500.
- **Numbers** (score, timer, stats, counters) use `font-variant-numeric: tabular-nums` so digits stop jittering.
- **Rules:** `text-wrap: balance` on headings; no uppercase tracked labels; no weight above 600; keep line length under ~70 characters by constraining the content column, not by shrinking type.

## 4. Shape, spacing, elevation

- Radii: `--r-sm` 12px (inputs, chips), `--r-md` 18px (cards, panels), `--r-pill` 980px (buttons, tags).
- Spacing scale 8/16/24/32/48/80. Section gaps use `--s-lg` or `--s-xl`; never invent a 13px gap.
- Cards have **no border**; they separate by surface color. Lists separate by hairline (`1px solid var(--sep)`).
- Shadows are for floating things only (segmented selection, sticky bar). They stay neutral — no colored glow.

## 5. Components

### Segmented control (area tabs)

`role="tablist"` rail on `--fill-2`, radius 9px, padding 2px. Each `role="tab"` is a button with `aria-selected` and roving `tabindex`. The selected item gets `--sel-bg`, a 0 3px 8px `/0.12` shadow and `--sel-ink` text. Arrow keys, Home and End move selection.

### Buttons

Pill shaped, min-height 44px (48px for the primary CTA), 17px text, 600 weight on primary.

- `.btn.primary` — `--blue` fill, white text.
- `.btn` — `--fill-2` translucent gray with `--blue` text.
- Disabled — 40% opacity, `cursor: not-allowed`, no hover lift.

### Cards and panels

`--bg-2` surface, 18px radius, 24px padding. The exam setup panel is one card; alternatives are individual cards.

### Answer alternatives

Radio input visually hidden, 44px row, `--bg-2` card. Selected: `box-shadow: 0 0 0 2px var(--blue)` plus filled bubble. In the correction view, `.gab` gets a green ring and `.err` a red one, always paired with the "gabarito"/"sua resposta" label.

### Sticky exam bar

`backdrop-filter: saturate(180%) blur(20px)` over `--bar-bg`, hairline bottom border, contains the question counter, the timer and a 2px progress bar animated with `transform: scaleX()`.

### Alert dialog

Native `<dialog class="modal">` at 270px, 14px radius, 17px semibold title, body at 13–15px, actions in a row split by hairlines, primary action semibold. `Esc` and backdrop cancel. Never `confirm()` or `alert()`.

### Tags and dots

Tags are pill-shaped tinted pills (`.tag.ok`, `.tag.bad`, `.tag.nil`). Question dots are 36px squares with 10px radius; answered dots get the blue tint, the current one gets `aria-current` plus a ring.

## 6. Motion

- Transitions only on `transform` and `opacity`, 150–300ms, `--ease` = `cubic-bezier(0.25, 0.1, 0.25, 1)`.
- Screen entry fades/translates the `#app` container once (`mount()` re-triggers `.in`).
- `prefers-reduced-motion: reduce` disables entry animation and non-essential transitions.
- No parallax, no auto-playing motion, never animate layout properties.

## 7. Accessibility contract

- Focus ring: `:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px }`. Never `outline: none`.
- Every interactive element is a real `<button>`, `<a>`, `<input>` or `<select>`.
- Screen changes move focus to `#app` (`tabindex="-1"`), so screen readers announce the new heading.
- Text contrast: `--label` and `--label-2` clear 4.5:1 on both grounds; `--label-3` only for non-essential metadata.
- Targets at least 44×44px.

## 8. Icon and PWA surface

- `icon.svg` — full-bleed `#0071e3` field, white geometric mark (an "E" of three bars inside a rounded seal), no text, safe inside the maskable area.
- `manifest.json` — `display: standalone`, `theme_color`/`background_color` `#ffffff`, `lang` `pt-BR`.
- HTML `theme-color` switches `#ffffff`/`#000000` by `prefers-color-scheme`.

## 9. Don'ts

- Don't add a second accent color.
- Don't bring back Alumni Sans, Albert Sans, gold, OKLCH tokens or uppercase tracked micro-labels.
- Don't put borders, heavy shadows or gradients on cards.
- Don't use weight 700+ in body copy or tracking below `-0.03em`.
- Don't ship a control that only looks native — it must behave native (keyboard, focus, states).
