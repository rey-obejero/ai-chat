# Design System
> A Machinist's Blueprint. Precision and function are paramount, with every element serving a clear purpose on a clean, technical surface. Based on v0 and MiniMax, adapted as a first-party system.

**Theme:** light

The design feels like a functional schematic on a stark white drafting table. Its nearly monochrome palette — #FFFFFF, #FAFAFA, #EAEAEA, #171717 — creates a utility-first atmosphere where color is reserved for semantic status and third-party identity. Typography is the main architectural element; a custom sans-serif is used everywhere, with tight negative letter-spacing at large sizes creating dense, impactful headlines. The UI is built from simple primitives: solid black CTAs with an 8px radius and subtly bordered white chips, distinguishing primary commands from secondary suggestions.

## Principles

1. Chrome is monochrome. Surfaces, borders, type, and controls use the neutral ramp only: Paper White, Canvas, Line, Subtext, Tertiary, Icon, Ink, Onyx.
2. Color is reserved for status and third-party identity. It is never decoration.
3. Hierarchy comes from fill and border, not color. Solid for primary, outlined for secondary, plain text for tertiary.
4. Type carries emphasis. Tight tracking at 24px and above; size and weight convey priority, never hue.
5. Whitespace is the default. Density is a deliberate choice.

## Foundations

### Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Paper White | `#ffffff` | `--color-paper-white` | Input fills, card and pill backgrounds. |
| Canvas | `#fafafa` | `--color-canvas` | Primary page background. |
| Line | `#eaeaea` | `--color-line` | Borders for inputs, headers, ghost buttons, and dividers. |
| Subtext | `#666666` | `--color-subtext` | Secondary text, navigation links, placeholder text. |
| Tertiary | `#3d3d3d` | `--color-tertiary` | Low-emphasis actions and links at rest. |
| Icon | `#7d7d7d` | `--color-icon` | Inactive icons and tertiary UI elements. |
| Ink | `#171717` | `--color-ink` | Primary text, headlines, and primary button backgrounds. |
| Onyx | `#000000` | `--color-onyx` | Logo, icons, highest contrast text. |
| Danger | `#b91c1c` | `--color-danger` | Destructive actions and error text. |

### Typography

#### GeistSans — The universal font for all UI text, from body copy to display headings. Weight 600 is used for major headlines, 500 for buttons, and 400 for body text. Its signature is the aggressive negative letter-spacing at large sizes, creating dense, block-like headlines. · `--font-geistsans`
- **Substitute:** Inter
- **Weights:** 400, 500, 600
- **Sizes:** 13px, 14px, 15px, 16px, 18px, 20px, 24px, 32px, 48px
- **Line height:** 1.00, 1.17, 1.25, 1.30, 1.33, 1.43, 1.50, 1.56
- **Letter spacing:** Ranges from -2.88px at 48px to normal at 16px. The progressively tighter tracking on larger sizes is a key brand identifier.
- **OpenType features:** `"zero", "ss09", "ss05"`

#### GeistMono — Used for small, technical annotations or user statistics where tabular alignment is beneficial. · `--font-geistmono`
- **Substitute:** IBM Plex Mono
- **Weights:** 400
- **Sizes:** 10px
- **Line height:** 1.50
- **OpenType features:** `"zero"`

### Type Scale

| Role | Size | Line Height | Letter Spacing | Token |
|------|------|-------------|----------------|-------|
| caption | 10px | 1.5 | — | `--text-caption` |
| body-sm | 14px | 1.43 | — | `--text-body-sm` |
| body | 16px | 1.5 | — | `--text-body` |
| subheading | 18px | 1.56 | — | `--text-subheading` |
| heading-sm | 20px | 1.25 | — | `--text-heading-sm` |
| heading | 24px | 1.33 | -0.48px | `--text-heading` |
| heading-lg | 32px | 1.17 | -1.28px | `--text-heading-lg` |
| display | 48px | 1 | -2.88px | `--text-display` |

### Spacing & Shapes

**Density:** compact

#### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 4 | 4px | `--spacing-4` |
| 6 | 6px | `--spacing-6` |
| 8 | 8px | `--spacing-8` |
| 10 | 10px | `--spacing-10` |
| 11 | 11px | `--spacing-11` |
| 12 | 12px | `--spacing-12` |
| 16 | 16px | `--spacing-16` |
| 20 | 20px | `--spacing-20` |
| 24 | 24px | `--spacing-24` |
| 32 | 32px | `--spacing-32` |
| 36 | 36px | `--spacing-36` |
| 40 | 40px | `--spacing-40` |
| 48 | 48px | `--spacing-48` |
| 50 | 50px | `--spacing-50` |
| 64 | 64px | `--spacing-64` |
| 80 | 80px | `--spacing-80` |

#### Border Radius

| Element | Value |
|---------|-------|
| cards | 12px |
| pills | 9999px |
| inputs | 12px |
| buttons | 8px |

#### Elevation

Shadows are reserved for cards and overlays, never for interactive elements.

| Name | Value | Token |
|------|-------|-------|
| subtle | `rgba(0, 0, 0, 0.08) 0px 0px 0px 1px, rgba(0, 0, 0, 0.04) 0px 2px 1px 0px` | `--shadow-subtle` |
| subtle-2 | `rgba(0, 0, 0, 0.08) 0px 0px 0px 1px` | `--shadow-subtle-2` |
| subtle-3 | `rgba(0, 0, 0, 0.04) 0px 2px 2px 0px, rgba(0, 0, 0, 0.04) 0px 8px 8px -8px` | `--shadow-subtle-3` |
| xl | `rgba(0, 0, 0, 0.25) 0px 25px 50px -12px` | `--shadow-xl` |

Named elevations: **Template Card** uses `0px 0px 0px 1px rgba(0, 0, 0, 0.08), 0px 2px 1px 0px rgba(0, 0, 0, 0.04)`. **Modal and Popover** use `0px 25px 50px -12px rgba(0, 0, 0, 0.25)`.

#### Layout

| Property | Value |
|----------|-------|
| Page max-width | 1440px |
| Section gap | 96px |
| Card padding | 16px |
| Element gap | 8px |

The layout is centered within a generous max-width container. The header is full-width with a 1px bottom border. Content sections are separated by large vertical whitespace (min. 96px) on the Canvas background.

## Color Categories

Chromatic color appears in exactly three categories.

| Category | Tokens | Rule |
|----------|--------|------|
| Chrome | The neutral ramp | Always achromatic. Surfaces, borders, text, and controls. |
| Status | `--color-danger` | Encodes state, not brand. Success, warning, and info join this category when needed. |
| Third-party identity | Provider marks | Used as provided, in full color. Not restyled into the neutral ramp. |

There is no accent hue. Links, focus rings, and selection remain achromatic. An accent, if ever adopted, is a new category with its own hover, active, and focus definitions. A color that fits none of these categories does not belong in the chrome.

## Interaction States

Every interactive element defines the same set of states.

| State | Treatment |
|-------|-----------|
| Rest | As specified by the component. |
| Hover | One achromatic step. Solid fills lighten; outlined surfaces fill with Line at 40%; tertiary text darkens to Ink. |
| Active | One step further in the same direction, typically Line at 60%. Variants that share one treatment for hover and press state so in their component spec. |
| Focus | 2px solid Ink ring, 2px offset, keyboard focus only. |
| Disabled | 35% opacity, no pointer events. |
| Loading | The label is replaced by a single spinner. Width is preserved so nothing reflows. `prefers-reduced-motion` is honored. |

The focus rule is mandatory. Focus styling is never removed without an equally visible replacement.

## Components

### Primary Button
**Role:** The main action on a page, such as 'Continue' or 'Sign Up'.

Solid Ink (#171717) background with Paper White (#ffffff) text. Font is 14px GeistSans at 500 weight. Padding is approximately 8px vertically and 12px horizontally, with an 8px border radius. Hover and press intentionally share one treatment: Ink at 90% over Canvas, approximately #2e2e2e.

### Secondary Button
**Role:** Supporting actions beside a primary one, such as 'Continue with Google'.

Transparent background, which reads as Canvas on the page, with a 1px Line (#eaeaea) border and Ink (#171717) text. Hover fills with Line at 40%; active fills with Line at 60%. Font is 14px GeistSans at 500 weight, with an 8px border radius.

### Tertiary Button
**Role:** Low-emphasis actions and navigation, such as 'Forgot password?' and 'Sign up'.

No fill and no border. Tertiary (#3d3d3d) text at 14px GeistSans, darkening to Ink (#171717) on hover. No underline, at rest or on hover. Keyboard focus applies the standard focus ring. When set within a sentence, it is set at 500 weight so that it reads as distinct from the surrounding Subtext (#666666) by tone and weight rather than by color alone.

### Text Input
**Role:** Single-line text entry.

Paper White (#ffffff) fill with a 1px Line (#eaeaea) border and a 12px radius. Ink (#171717) text with a Subtext (#666666) placeholder. Padding is 8px vertically and 12px horizontally. On focus, the border becomes Ink and the standard focus ring applies. A placeholder may carry the field's purpose, but the field still requires an accessible name.

### Password Input
**Role:** Text input for secrets, with a visibility toggle.

Everything from Text Input, plus a trailing toggle: a 24×24px target carrying a 16px Icon (#7d7d7d) glyph. It shows a closed eye while the value is hidden and an open eye while it is visible. Toggling must not move focus. The toggle is keyboard-reachable and carries the accessible name "Show password" or "Hide password".

### Prompt Suggestion Chip
**Role:** Clickable suggestions below the main input.

Transparent background with a 1px Line (#eaeaea) border. Text is Subtext (#666666) at ~13px. Padding is 4px vertically and 8px horizontally, with a 6px border radius.

### Filter Pill Button
**Role:** Filtering content categories like 'Landing Pages'.

A pill-shaped button (9999px radius) with a Paper White (#ffffff) background and Ink (#171717) text. Features a faint 1px border of `rgba(0, 0, 0, 0.08)`.

### Header Divider
**Role:** Separates the sticky header from page content.

A full-width 1px solid border using the Line color (#eaeaea).

## Accessibility

Text contrast clears WCAG AA: Ink (#171717) and Onyx (#000000) exceed 4.5:1 on Paper White and Canvas; Tertiary (#3d3d3d) exceeds 9:1; large text (24px and above) clears 3:1; Danger (#b91c1c) clears 4.5:1 on both.

Resting input and secondary-button borders fall below the 3:1 minimum for non-text contrast — Line on Canvas is approximately 1.06:1. This is an accepted tradeoff: the surface fill and the focus ring carry the affordance. Those borders are not to be made lighter.

Focus behavior follows Interaction States: a 2px solid Ink ring at a 2px offset on keyboard focus, never removed without an equally visible replacement.

Interactive targets are at least 24×24px. The password visibility toggle is the reference case.

Color never carries meaning alone; status is stated in text and reinforced by color. A Tertiary link within a sentence is distinguished by tone and weight, not by hue.

Motion respects `prefers-reduced-motion`; looping or decorative animation is reduced or hidden.

Every input has an accessible name, visible or via `aria-label`. Icon-only controls carry `aria-label`; decorative icons are `aria-hidden`; the document title reflects the current route.

## Do's and Don'ts

### Do
- Use GeistSans for all text, without exception.
- Apply aggressive negative letter-spacing to headings 24px and larger.
- Keep the chrome monochrome; color is reserved for status and third-party identity.
- Use 8px radius for buttons and 12px for cards and inputs.
- Use 1px solid #eaeaea for all visual dividers.
- Differentiate action hierarchy using fills and borders: solid for primary, bordered for secondary, text-only for tertiary.
- Maintain generous whitespace (min. 96px) between content sections.

### Don't
- Do not use color to decorate or brand; it is reserved for status and third-party identity.
- Do not rest a link or button on an underline; reveal it on hover and focus.
- Do not use system fonts or other brand fonts.
- Do not use shadows on interactive elements like buttons or inputs; reserve them for cards.
- Do not use any border-radius values other than 6px, 8px, 12px, or 9999px (for pills).
- Do not use gradients or background images.
- Do not use bold (700+) font weights; rely on 600 weight and size for emphasis.
- Do not create dense layouts; prioritize clarity and space.

## Imagery

This design uses no decorative imagery. Visuals are confined to user-generated content previews within cards, presented as raw, unstyled content inside a 12px rounded container. The page is UI-dominant; imagery serves only to showcase product output, not to build atmosphere. Third-party identity marks are the sole exception, since they carry external meaning.

## Agent Prompt Guide

### Quick Color Reference
- **Page Background**: `#fafafa` (Canvas)
- **Primary Text**: `#171717` (Ink)
- **Subtle Text**: `#666666` (Subtext)
- **Tertiary Text**: `#3d3d3d` (Tertiary)
- **Border**: `#eaeaea` (Line)
- **CTA Background**: `#171717` (Ink)
- **CTA Text**: `#ffffff` (Paper White)
- **Error Text**: `#b91c1c` (Danger)

### Example Component Prompts
1. **Primary Button:** `Create a button with 'Get Started' text. It needs a #171717 background, #FFFFFF text, 8px corner radius, and font size 14px.`
2. **Display Headline:** `Generate a headline 'Start with a template'. Use GeistSans 32px weight 600, color #171717, and letter-spacing of -1.28px.`
3. **Template Card:** `Design a card container with a 12px border-radius, a white background, and a box-shadow of '0px 0px 0px 1px rgba(0,0,0,0.08), 0px 2px 1px 0px rgba(0,0,0,0.04)'.`

## Similar Brands

- **Linear** — Shares the high-contrast, black/white/gray palette and surgically precise typography.
- **GitHub** — Similar utilitarian, developer-centric aesthetic with a focus on functional components over decoration.
- **Read.cv** — Extreme typography-first approach on a minimal, monochrome canvas.
- **Height** — Clean, high-contrast UI with a similar approach to minimal buttons and inputs.

## Quick Start

### CSS Custom Properties

```css
:root {
  /* Colors */
  --color-paper-white: #ffffff;
  --color-canvas: #fafafa;
  --color-line: #eaeaea;
  --color-subtext: #666666;
  --color-tertiary: #3d3d3d;
  --color-icon: #7d7d7d;
  --color-ink: #171717;
  --color-onyx: #000000;
  --color-danger: #b91c1c;

  /* Typography — Font Families */
  --font-geistsans: 'GeistSans', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-geistmono: 'GeistMono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Typography — Scale */
  --text-caption: 10px;
  --leading-caption: 1.5;
  --text-body-sm: 14px;
  --leading-body-sm: 1.43;
  --text-body: 16px;
  --leading-body: 1.5;
  --text-subheading: 18px;
  --leading-subheading: 1.56;
  --text-heading-sm: 20px;
  --leading-heading-sm: 1.25;
  --text-heading: 24px;
  --leading-heading: 1.33;
  --tracking-heading: -0.48px;
  --text-heading-lg: 32px;
  --leading-heading-lg: 1.17;
  --tracking-heading-lg: -1.28px;
  --text-display: 48px;
  --leading-display: 1;
  --tracking-display: -2.88px;

  /* Typography — Weights */
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;

  /* Spacing */
  --spacing-4: 4px;
  --spacing-6: 6px;
  --spacing-8: 8px;
  --spacing-10: 10px;
  --spacing-11: 11px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-20: 20px;
  --spacing-24: 24px;
  --spacing-32: 32px;
  --spacing-36: 36px;
  --spacing-40: 40px;
  --spacing-48: 48px;
  --spacing-50: 50px;
  --spacing-64: 64px;
  --spacing-80: 80px;

  /* Layout */
  --page-max-width: 1440px;
  --section-gap: 96px;
  --card-padding: 16px;
  --element-gap: 8px;

  /* Border Radius */
  --radius-md: 4px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-3xl: 35px;

  /* Named Radii */
  --radius-cards: 12px;
  --radius-pills: 9999px;
  --radius-inputs: 12px;
  --radius-buttons: 8px;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px, rgba(0, 0, 0, 0.04) 0px 2px 1px 0px;
  --shadow-subtle-2: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px;
  --shadow-xl: rgba(0, 0, 0, 0.25) 0px 25px 50px -12px;
  --shadow-subtle-3: rgba(0, 0, 0, 0.04) 0px 2px 2px 0px, rgba(0, 0, 0, 0.04) 0px 8px 8px -8px;
}
```

### Tailwind v4

```css
@theme {
  /* Colors */
  --color-paper-white: #ffffff;
  --color-canvas: #fafafa;
  --color-line: #eaeaea;
  --color-subtext: #666666;
  --color-tertiary: #3d3d3d;
  --color-icon: #7d7d7d;
  --color-ink: #171717;
  --color-onyx: #000000;
  --color-danger: #b91c1c;

  /* Typography */
  --font-geistsans: 'GeistSans', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-geistmono: 'GeistMono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Typography — Scale */
  --text-caption: 10px;
  --text-caption--line-height: 1.5;
  --text-body-sm: 14px;
  --text-body-sm--line-height: 1.43;
  --text-body: 16px;
  --text-body--line-height: 1.5;
  --text-subheading: 18px;
  --text-subheading--line-height: 1.56;
  --text-heading-sm: 20px;
  --text-heading-sm--line-height: 1.25;
  --text-heading: 24px;
  --text-heading--line-height: 1.33;
  --text-heading--letter-spacing: -0.48px;
  --text-heading-lg: 32px;
  --text-heading-lg--line-height: 1.17;
  --text-heading-lg--letter-spacing: -1.28px;
  --text-display: 48px;
  --text-display--line-height: 1;
  --text-display--letter-spacing: -2.88px;

  /* Spacing */
  --spacing-4: 4px;
  --spacing-6: 6px;
  --spacing-8: 8px;
  --spacing-10: 10px;
  --spacing-11: 11px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-20: 20px;
  --spacing-24: 24px;
  --spacing-32: 32px;
  --spacing-36: 36px;
  --spacing-40: 40px;
  --spacing-48: 48px;
  --spacing-50: 50px;
  --spacing-64: 64px;
  --spacing-80: 80px;

  /* Border Radius */
  --radius-md: 4px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-3xl: 35px;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px, rgba(0, 0, 0, 0.04) 0px 2px 1px 0px;
  --shadow-subtle-2: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px;
  --shadow-xl: rgba(0, 0, 0, 0.25) 0px 25px 50px -12px;
  --shadow-subtle-3: rgba(0, 0, 0, 0.04) 0px 2px 2px 0px, rgba(0, 0, 0, 0.04) 0px 8px 8px -8px;
}
```
