# Design System
> A Machinist's Blueprint. Precision and function are paramount, with every element serving a clear purpose on a clean, technical surface. Based on v0 and MiniMax, adapted as a first-party system.

**Theme:** light

The design feels like a functional schematic on a pale drafting surface. Its nearly monochrome palette — #FFFFFF, #FAFAFA, #EAEAEA, #171717 — creates a utility-first atmosphere where color is reserved for semantic status and third-party identity. The page sits on Canvas, and Paper White is held back for the surfaces that sit above it: the composer, inputs, menus and dialogs. Typography is the main architectural element; a custom sans-serif is used everywhere, with tight negative letter-spacing at large sizes creating dense, impactful headlines. The UI is built from simple primitives: solid black CTAs on an 8px radius, bordered secondary controls, and unfilled tertiary ones, separating primary commands from supporting actions.

## Principles

1. Chrome is monochrome. Surfaces, borders, type, and controls use the neutral ramp only: Paper White, Canvas, Line, Subtext, Tertiary, Icon, Ink, Onyx.
2. Color is reserved for status and third-party identity. It is never decoration.
3. Hierarchy comes from fill and border, not color. Solid for Primary, bordered for Secondary, unfilled for Tertiary.
4. Type carries emphasis. Tight tracking at 24px and above; size and weight convey priority, never hue.
5. Whitespace is the default. Density is a deliberate choice.

## Foundations

### Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Paper White | `#ffffff` | `--color-paper-white` | Raised surfaces only: input fills, cards, menus, dialogs. |
| Canvas | `#fafafa` | `--color-canvas` | Page background and side navigation. |
| Line | `#eaeaea` | `--color-line` | Borders for inputs, headers, ghost buttons, and dividers. |
| Subtext | `#666666` | `--color-subtext` | Secondary text, navigation links, placeholder text. |
| Tertiary | `#3d3d3d` | `--color-tertiary` | Low-emphasis actions and links at rest. |
| Icon | `#7d7d7d` | `--color-icon` | Inactive icons and tertiary UI elements. |
| Ink | `#171717` | `--color-ink` | Primary text, headlines, and primary button backgrounds. |
| Onyx | `#000000` | `--color-onyx` | Logo, icons, highest contrast text. |
| Danger | `#b91c1c` | `--color-danger` | Destructive actions and error text. |

### Typography

#### GeistSans — The universal font for all UI text, from body copy to display headings. Weight 600 is used for section headings, 500 for the hero headline and for buttons, and 400 for body text. Its signature is the aggressive negative letter-spacing at large sizes, creating dense, block-like headlines. · `--font-sans`
- **Substitute:** Inter
- **Weights:** 400, 500, 600
- **Sizes:** 13px, 14px, 15px, 16px, 18px, 20px, 24px, 32px, 48px
- **Line height:** 1.00, 1.17, 1.25, 1.30, 1.33, 1.43, 1.50, 1.56
- **Letter spacing:** Ranges from -2.88px at 48px to normal at 16px. The progressively tighter tracking on larger sizes is a key brand identifier.
- **OpenType features:** `"zero", "ss09", "ss05"`

#### GeistMono — Used for small, technical annotations or user statistics where tabular alignment is beneficial. · `--font-mono`
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

**Status: specified, not implemented.** No `--spacing-*` variables exist in `src/assets/main.css`; the application reaches these values through Tailwind's spacing utilities. The Token column is therefore the intended contract rather than a description of the stylesheet, and it is kept for two reasons: the scale is the answer to "is this gap allowed?", and it is what a future token layer would implement.

In practice Tailwind v4 derives every spacing step from a single `--spacing: 0.25rem` base, so step *n* is *n* × 4px and every value in the table is reachable without configuration.

**Naming caveat.** The Name column is the value in pixels, not a Tailwind step key. `p-4` is 16px — the 16px row — and not the 4px row. A `--spacing-4` variable, were one ever defined, would be 4px. Reading the Name column as a utility will produce a value four times too large.

The app currently departs from the scale in two places: 2px (`mt-0.5`, below the 4px floor) and 28px (`sm:pt-7`, not listed). Both are small enough to absorb into the scale rather than argue about.

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

Shadows are reserved for cards and overlays, never for controls. The `subtle-3` layers are directional and read only at the bottom edge; `elevated` pairs a tight contact shadow with an ambient one so a card lifts on every side. It carries no ring, because a bordered surface would double its own edge.

| Name | Value | Token |
|------|-------|-------|
| subtle | `rgba(0, 0, 0, 0.08) 0px 0px 0px 1px, rgba(0, 0, 0, 0.04) 0px 2px 1px 0px` | `--shadow-subtle` |
| subtle-2 | `rgba(0, 0, 0, 0.08) 0px 0px 0px 1px` | `--shadow-subtle-2` |
| subtle-3 | `rgba(0, 0, 0, 0.04) 0px 2px 2px 0px, rgba(0, 0, 0, 0.04) 0px 8px 8px -8px` | `--shadow-subtle-3` |
| elevated | `rgba(0, 0, 0, 0.04) 0px 1px 2px 0px, rgba(0, 0, 0, 0.08) 0px 8px 20px -8px` | `--shadow-elevated` |
| xl | `rgba(0, 0, 0, 0.25) 0px 25px 50px -12px` | `--shadow-xl` |

Named elevations: **Composer Card** uses `elevated`. **Modal and Popover** use `xl`. **Template Card** is specified but not implemented; it would use `subtle`.

#### Layout

| Property | Value |
|----------|-------|
| Page max-width | 1440px |
| Section gap | 96px |
| Card padding | 12px |
| Element gap | 8px |

The layout is centered within a generous max-width container. Content sections are separated by large vertical whitespace (min. 96px) on the Canvas background. The application header carries no rule beneath it — it is separated from the content by whitespace alone.

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
| Selected | Line at 60% fill with Ink (#171717) text at 500 weight. Applies to the row representing the current item in a list or navigation, and never to a hover state. |
| Loading | The label is replaced by a single spinner. Width is preserved so nothing reflows. `prefers-reduced-motion` is honored. |

The focus rule is mandatory. Focus styling is never removed without an equally visible replacement. Selection is carried by fill and weight rather than color, and is announced through `aria-current`.

## Components

Buttons come in exactly three levels of emphasis: **Primary**, **Secondary** and **Tertiary**. A control that is not a button is named as its own component below. Two rules cross-cut the set:

- **Shape.** Every button is a rounded rectangle on the 8px radius. The single exception is a button whose entire content is a glyph, which is a circle — see Icon Button.
- **Not everything is a button.** A control that carries a value, a filter or a selected state is a chip, and a control that navigates is a Link. Neither is a button tier.

The sidebar is deliberately outside this hierarchy. Nav Item and Group Header carry their own styling, which happens to match Tertiary; that is a coincidence and not a relationship.

### Primary Button
**Role:** The main action on a page.

Solid Ink (#171717) background with Paper White (#ffffff) text. Font is 14px GeistSans at 500 weight. Padding is approximately 8px vertically and 12px horizontally, with an 8px border radius. Hover and press intentionally share one treatment: Ink at 90% over Canvas, approximately #2e2e2e. The composer's Send button is Primary for the same reason.

### Secondary Button
**Role:** Supporting actions beside a primary one.

Transparent background, with a 1px Line (#eaeaea) border and Ink (#171717) text. Hover fills with Line at 40%; active fills with Line at 60%. Font is 14px GeistSans at 500 weight, with an 8px border radius. Social sign-in buttons are Secondary.

The suggestion row under the composer is a Secondary variant: the same border and hover, at a compact 6px/10px padding with a 14px leading glyph. It is a button, not a chip, because it performs an action — it seeds the composer — rather than carrying a value. It would become a chip the moment it held a persistent mode, at which point it would take the Selected state.

Secondary is transparent rather than filled, and that is a single answer for every use. A transparent control is defined by whatever sits behind it, so its appearance would change if the page background changed. White is reserved for raised surfaces: the Composer Card, inputs, menus and dialogs.

### Tertiary Button
**Role:** Low-emphasis actions with no fill of their own.

No background and no border at rest; hover fills with Line at 40%, press with Line at 60%. Ink (#171717) text at 14px GeistSans, with an 8px border radius, or a circle when icon-only. The attach control, the sidebar collapse toggle and the header conversation button are Tertiary.

### Link
**Role:** Navigating to another view, or a low-emphasis text action.

Text only — no fill, no border, and never an underline, at rest or on hover. Tertiary (#3d3d3d) at 14px GeistSans, darkening to Ink (#171717) on hover, with the standard focus ring. 'Forgot password?' and the sign-in/sign-up cross-links are Links.

A Link is not a button: it has no surface of its own to fill on hover, only a color change. When a Link sits inside a sentence it is set at 500 weight, so it reads as distinct from the surrounding Subtext (#666666) by tone and weight rather than by color alone. 'Forgot password?' is an action rather than navigation, so it renders a button element wearing the Link treatment — never an anchor to nowhere.

### Nav Item
**Role:** A row in the side navigation, such as 'New conversation', 'Search' or 'Library'.

A full-width row with an 8px border radius and 14px GeistSans label, preceded by a 16px Icon (#7d7d7d) glyph. Three variants share the geometry:

- **Plain** — transparent at rest, fills with Line at 40% on hover, and takes the Selected state when it represents the current location.
- **Filled** — Line at 40% at rest, darkening to Line at 60% on hover. Reserved for the single standing action at the top of the navigation, such as 'New conversation'.
- **Search** — the row carries a real `<input>` where the label would be, so 'Search' is a field rather than a row that opens one. It is a Plain row at rest and takes the Text Input treatment once it holds focus (Paper White fill, 1px Line edge, Ink text) with the search glyph as its leading icon; the focus ring follows the row, because the row is the control. The placeholder is 'Search' and the accessible name is 'Search conversations'.

When the navigation collapses, the label leaves the visual layout but stays in the accessibility tree as `sr-only` — a row must never lose its accessible name. The glyph centers, and a tooltip supplies the label on hover.

A row may also carry a **trailing action slot**: a single 24×24px Icon Button at the end of the row, invisible at rest and revealed on hover or keyboard focus anywhere in the row (`:hover` / `:focus-within`, never `group-*`, which is inert in this build), exactly as Message Actions reveals its row. It keeps its space whether or not it is visible, so revealing it moves nothing, and it stays keyboard-reachable at rest so focus can bring it into view. Conversation Row below is the worked example.

A collapsed rail carries navigation only. Grouped lists need the width their labels do, so the groups are removed rather than truncated; the Search row goes with them, since a 64px row cannot hold a field. The rail gets no separate expand button: a 64px header row cannot hold the logo and the toggle at once without squashing the glyph, so the toggle takes the logo's place and appears on hover or keyboard focus. Either way the toggle is a Tertiary Button and a circle.

### Group Header
**Role:** A collapsible heading above a run of navigation rows, such as 'Projects' or 'Recents'.

A 14px label in Subtext (#666666) at 400 weight — the same size as the navigation rows it heads, kept quiet by color rather than by being made smaller. It darkens to Ink (#171717) on hover. A 12px chevron follows the label, 6px after it, and rotates a quarter turn when the group is open. The chevron is not shown at rest: it appears on hover or keyboard focus, so a collapsed group does not advertise itself in the resting state.

The header is a real button carrying `aria-expanded`, not a heading element: the global h1–h3 rule sets weight 600, which a 14px label must not inherit. Collapsed state is remembered per group. A group that is open must still be reachable by keyboard, and its rows stay in the accessibility tree order the header implies.

### Conversation Row
**Role:** A conversation in the sidebar's Pinned, Recents or Archived group.

The nav row's geometry — 8px radius, 10px/8px padding, title at 14px — with the row itself as the hover and selection target and the title a plain button inside it, so the trailing action has somewhere to sit. Plain at rest (transparent, darkening to Ink on hover), Line at 40% on hover, and the Selected state — Line at 60% with the title at 500 weight — for the conversation currently open.

- **Favourite badge** — a 12px star glyph in Icon (#7d7d7d) after the title, carrying the accessible name 'Favourite'. It is a badge and not a control: the menu is where the state changes.
- **Archived** — the title is set in Subtext (#666666), the row sits in the Archived group whose header names the state, and the title also carries '(archived)' in `sr-only` so the row's own accessible name does not depend on color.
- **Menu trigger** — the Nav Item trailing action slot: a 24×24px Icon Button with a 16px '…' glyph, the accessible name 'Conversation actions' and a tooltip. It opens Rename, Pin/Unpin, Add to favourites/Remove from favourites, Archive/Unarchive, then a rule, then Delete.
- **Rename** — swaps the title for a Text Input at 14px inside the row. Enter saves, Escape cancels, and a blank or unchanged title closes the field without a write. When the field closes, focus returns to the row's title.

A list with more pages behind it ends with a 'Load more' row in the Group Header treatment: 14px in Subtext, darkening to Ink on hover.

### Composer Card
**Role:** The message input surface, such as the chat composer.

Paper White (#ffffff) fill with a 1px Line (#eaeaea) border, a 12px radius, and 12px padding, raised by `elevated`. Controls sit on a single row beneath the text: attachments to the left, model selector and send to the right.

On the empty state the composer is centered horizontally but anchored near the top of the page, with the headline and suggestion chips as one group. It is not vertically centered: a composer at the midline leaves a void beneath it on short pages, and the group belongs in the upper-middle where the eye lands first.

The card takes no focus ring of its own. It is a container of several controls, not a focusable control, and the caret is the text field's focus indicator; a ring drawn around the card would appear on every keystroke, because a text input matches `:focus-visible` even when focus is set programmatically. The controls inside it each carry the standard focus ring.

The composer is a card, not an input, so the shadow rule permits it. Its border and fill follow the same low-contrast tradeoff as Text Input.

### Command Palette
**Role:** The slash-command list, anchored above the Composer Card.

It opens when the draft begins with `/` and the text field holds the caret. The filter is what sits between the slash and the first space, matched case-insensitively against each command's name and id. Deleting the slash closes it, and so does Escape, which leaves the draft untouched — dismissing is never clearing. A slash anywhere else in the draft is ordinary prose (`/api/v1`); only a leading one is an invocation.

Selecting a command — the highlighted one on Enter or Tab, or the clicked one — replaces the leading `/filter` with that command's template and returns the caret to the end of the draft, so the user can add detail before sending. The palette never sends a message: a command is a local prompt template, not a server feature, so its invocation is editable text the user still has to send. Enter therefore belongs to the palette while it is open, matched or not, and a lone slash cannot submit. Shift+Enter stays with the draft, since it never submits.

**Surface.** Paper White fill, 1px Line border, 12px radius, `elevated` shadow, and 6px padding, anchored above the card with an 8px gap. It is capped at 16rem tall and scrolls past that. Rows are 8px/12px with an 8px radius, one command each: the label in Ink and the description in Subtext, both at body-sm.

The row under the highlight fills with Line at 40%. That is the hover step rather than the Selected state: the highlight is a transient cursor, and Line at 60% would claim a persistence a popup cursor does not have.

**Keyboard.** Up and Down move the highlight and wrap at either end; Enter or Tab inserts the highlighted command; Escape closes. The text field keeps focus throughout — the highlight is announced through `aria-activedescendant` on that field, over `role="listbox"` with `role="option"` rows, rather than by moving focus into the popup. Because the popup names itself, the field's accessible name is unchanged.

A filter that matches nothing is not an empty box: the palette states 'No matching commands.' in Subtext at body-sm, in a polite live region.

### Conversation Turn
**Role:** A single message in the transcript.

The two roles are told apart by alignment and fill, not by color:

- **User** — right-aligned, in a Line at 60% fill with a 12px radius and 16px/10px padding, capped at 85% of the column so long text wraps. The role label sits right-aligned above it.
- **Assistant** — left-aligned, no fill, no border, full column width. The role label sits above it.

Both labels are a 10px caption in Subtext (#666666). The transcript is bottom-anchored, so a short conversation rests just above the composer instead of leaving a gap.

An assistant turn's body is **Markdown Content**; a user turn's body stays literal text, with any fenced block shown as a bare monospace block on the bubble fill.

A **system** message is not a turn: it is a caption, centred in the column and set in Subtext at body-sm, with no role label, no fill and no Message Actions. It reports what the transcript did rather than saying anything — a model switch writes 'Model set to <model>' (FR-23) — and it stays literal, so a model name is never read as Markdown.

### Message Actions
**Role:** The action row beneath a conversation turn.

A row of tertiary icon buttons, 4px apart, sitting under the turn: Copy and Quote on both roles, Edit on a user turn, Regenerate on an assistant turn. It is invisible at rest and revealed on hover or keyboard focus anywhere in the turn (`:hover` / `:focus-within`, never `group-*`, which is inert in this build), and it is always visible under `(pointer: coarse)`, where there is no hover to reveal it. The row keeps the turn's alignment, so a user turn's actions sit right and an assistant turn's sit left.

The buttons follow Icon Button exactly — 32×32 circles with a 16px glyph, no padding, every one of them tooltipped. Each control's accessible name states its action ("Copy message", "Edit message"), never its glyph. Revealing the row must not move anything: the buttons occupy their space whether or not they are visible, and they stay keyboard-focusable at rest so focus can bring them into view.

Copying writes the message's exact text and flips that control to a check mark for 1.5 seconds, the Code Block's pattern; the confirmation is also announced through a polite live region. Edit and Regenerate are silent — the transcript truncates to the affected turn and streams a replacement, with no confirmation dialog.

### Markdown Content
**Role:** The rendered body of an assistant turn.

Prose inside the turn's column: paragraphs at 16px with 12px between; headings at 20px and 18px, weight 600; lists indented 20px with 6px between items; blockquotes with a 2px Line left border at the tertiary tone; inline code on a Line-at-60% fill at 0.9em Geist Mono; links in the Link treatment, opening in a new tab; tables full width with 1px Line borders and a header row on Line at 40%; and images served through the API's own proxy (ADR-0051) — up to 100% wide, 12px radius, 1px Line border, alt text preserved, lazily loaded.

Streamed content re-renders on every chunk, so a partially streamed reply must degrade to readable text rather than break; malformed markup renders as literal text and rendered content never executes code.

### Code Block
**Role:** A fenced code block in an assistant reply.

Paper White fill, 1px Line border, 12px radius — the same shell as the Composer Card. A header row carries the language label (body-sm in Subtext, lowercase as written, falling back to `code`) and a copy control on the right (24×24, tertiary treatment, `aria-label="Copy code"`, tooltipped), over a 1px Line bottom border. The body is Geist Mono 14px at 1.5 line height, capped at 24rem tall and scrolling past that.

Past 20 lines a footer row appears with a tertiary "Show more" control that flips to "Show less" with `aria-expanded`, lifting the height cap. Copying flips the control to a check mark for 1.5 seconds. A fence still streaming in stays plain — no highlighting — and keeps its header, copy control, and scroll.

### Icon Button
**Role:** A control whose entire content is a glyph, such as attach, send, or the sidebar collapse toggle.

A 32×32px circle carrying a 16px glyph at a 2px stroke, with no padding of its own — the padding is what turns a glyph button into an oval, so it is zeroed explicitly. Icons carry an explicit stroke width; left to the SVG default they render as hairlines at this size. Variants: bordered ghost (transparent, filling with Line at 40% on hover), solid (Ink fill with a Paper White glyph, hover Ink at 90% over Canvas), and stopped (Square glyph replacing the send arrow while a reply streams).

The icon button is the **only** control in the system with fully-rounded corners. Every other button takes the standard 8px radius.

Every icon-only control carries a Tooltip. Glyphs that read without one — a password visibility toggle, a dialog close — are the exception, not the rule.

### Tooltip
**Role:** Naming an icon-only control on hover.

A label in Paper White (#ffffff) on an Ink (#171717) fill, at the 14px body-sm size with 5px/10px padding. Its radius is the standard 8px — a tooltip is not a circle, and matching the icon button it names would over-round it.

It carries no tail. A tooltip is offset from its control by an arrow; that gap is what the `gutter` token controls, and zeroing it collapses the arrow to nothing and closes the gap. The arrow is drawn from CSS borders rather than a background, so nothing else removes it.

A tooltip supplements rather than replaces the accessible name: the control still carries `aria-label`, and the tooltip is for sighted mouse users. It is omitted where a glyph is already unambiguous — a password visibility toggle, a dialog close.

### Model Selector
**Role:** Naming the model that will answer the next message.

A Tertiary Button — no fill at rest, filling with Line at 40% on hover, no border, 8px radius — carrying the model name in Ink (#171717) and a 16px Icon chevron. It opens a menu and carries `aria-haspopup`.

The menu lists the models the server serves, labelled as served, with the server's default annotated `(default)` — so a conversation with no choice of its own still says which model will answer. The button names that model; with several served and no choice made it names the default, and with a single served model it reads `Auto`.

The choice belongs to the conversation, not to the account, and it is applied one of two ways. Before the first message it rides on the conversation's creation, so nothing has to be rewritten afterwards. Once the conversation exists, choosing another model updates the conversation and applies from the next reply, and the switch is disclosed by a **system caption** the server persists (see Conversation Turn) — a silent switch is structurally impossible. Choosing the model the conversation already has changes nothing at all: no write, and so no caption. The control is disabled while a reply streams, so the caption never interrupts one, and while no models are served, because then there is nothing to pick.

### Text Input
**Role:** Single-line text entry.

Paper White (#ffffff) fill with a 1px Line (#eaeaea) border and a 12px radius. Ink (#171717) text with a Subtext (#666666) placeholder. Padding is 8px vertically and 12px horizontally. On focus, the border becomes Ink and the standard focus ring applies. A placeholder may carry the field's purpose, but the field still requires an accessible name.

The sidebar's search field (see Nav Item) is the one Text Input that is not a Paper White box at rest: it wears the nav row's geometry until it holds focus, and only then takes the fill and the Line edge above, so the sidebar keeps a single row shape. Its term is queried on the server after a 250ms debounce rather than filtered locally, so while it is in flight the previous rows stay on screen; a term with no matches states 'No matches' rather than showing an empty list. Escape clears the term. The inline rename on a Conversation Row is this component too, at 14px on the row.

### Password Input
**Role:** Text input for secrets, with a visibility toggle.

Everything from Text Input, plus a trailing toggle: a 24×24px target carrying a 16px Icon (#7d7d7d) glyph. It shows a closed eye while the value is hidden and an open eye while it is visible. Toggling must not move focus. The toggle is keyboard-reachable and carries the accessible name "Show password" or "Hide password".

### Filter Pill Button
**Role:** Filtering content categories like 'Landing Pages'.

A pill-shaped button (9999px radius) with a Paper White (#ffffff) background and Ink (#171717) text. Features a faint 1px border of `rgba(0, 0, 0, 0.08)`.

**Status:** not implemented. The entry is retained because the 9999px radius and a Paper White fill both need a stated precedent, but note that the white fill now conflicts with the rule that white belongs to raised surfaces — a filter pill sitting on Canvas should either take that conflict consciously or be re-specified as transparent with a border, like Secondary.

### Header Divider
**Role:** Separates the sticky header from page content.

A full-width 1px solid border using the Line color (#eaeaea).

**Status:** not in use. The application header draws no rule; see Layout.

### Personalization Section
**Role:** The account's standing instructions and response style, as a section of the Settings dialog (FR-24, FR-25).

Two fields and a Save. Instructions are a Textarea at the dialog's width, with a character counter on the label row: a mono caption — a technical annotation, which is what GeistMono is for — reading `<used>/<cap>` against the 2000-character cap the API enforces. The field carries `maxlength` for the same cap, so a value the API would refuse cannot be typed. The response style is a Select offering Default, Concise, Detailed, Formal and Casual, opened on the stored value.

Save is the section's Primary Button. It is disabled while nothing differs from the stored value and while a save is in flight, and it takes the Loading state while it runs; a polite `Saved.` in Subtext confirms the write. A refusal from the API states what the API said in Danger, beside the action rather than in a dialog of its own. Editing after either message retires it, because it described a value this one no longer is.

The section is the anchor the account menu's **Personalization** item opens the dialog at, and the dialog scrolls it into view rather than leaving the reader to find it.

### Name Field
**Role:** The account's name (FR-7), in the settings dialog's Profile section and in the first-run prompt.

The **Text Input** treatment — Paper White fill, 1px Line border, 12px radius and Ink text — with a 50-character cap. The cap is `maxlength` rather than the Personalization Section's counter: a name is short enough that a value the API would refuse cannot be typed, and a counter on every account's own name would be noise. The field is prefilled with the name the account already has — the one derived from the email, on a first sign-in — so both the prompt's actions answer a value the reader can see rather than a blank.

A name the API refuses, or a value that could not be saved at all, is stated on a line below the field at body-sm in Danger; a whitespace-only value is refused by the field itself, in the same place and the same treatment, because the API would refuse it too. Editing retires the message. Like the Personalization Section, the field never reports success by colour alone: `Saved.` is written in Subtext beside the Save action.

The prompt is that field in a Dialog, under the heading 'What should we call you?', with Save as its Primary Button and Skip as a Tertiary one. The dialog carries no close control, and Escape and a click on the mask do nothing: dismissing it without answering would leave the prompt to return on the next sign-in, so Save and Skip are the only ways out.

## Accessibility

Text contrast clears WCAG AA: Ink (#171717) and Onyx (#000000) exceed 4.5:1 on Paper White and Canvas; Tertiary (#3d3d3d) exceeds 9:1; large text (24px and above) clears 3:1; Danger (#b91c1c) clears 4.5:1 on both.

Resting input and secondary-button borders fall below the 3:1 minimum for non-text contrast — Line on Canvas is approximately 1.06:1. This is an accepted tradeoff: the surface fill and the focus ring carry the affordance. Those borders are not to be made lighter.

Focus behavior follows Interaction States: a 2px solid Ink ring at a 2px offset on keyboard focus, never removed without an equally visible replacement.

Interactive targets are at least 24×24px. The password visibility toggle is the reference case.

Color never carries meaning alone; status is stated in text and reinforced by color. A Link within a sentence is distinguished by tone and weight, not by hue.

Motion respects `prefers-reduced-motion`; looping or decorative animation is reduced or hidden.

Every input has an accessible name, visible or via `aria-label`. Icon-only controls carry `aria-label`; decorative icons are `aria-hidden`; the document title reflects the current route.

A streaming transcript is a log region: `role="log"` with `aria-live="polite"` and an accessible name. Where a header repeats the conversation title, the transcript is scoped by its own role rather than by page-wide text, so the title and the first message do not read as a single string.

## Do's and Don'ts

### Do
- Use GeistSans for all text, without exception.
- Apply aggressive negative letter-spacing to headings 24px and larger.
- Keep the chrome monochrome; color is reserved for status and third-party identity.
- Use 8px radius for every button except icon-only buttons, which are circles; 9999px only for true pills; 12px for cards and inputs.
- Use 1px solid #eaeaea for all visual dividers.
- Differentiate action hierarchy using fills and borders: solid for Primary, bordered for Secondary, unfilled for Tertiary.
- Maintain generous whitespace (min. 96px) between content sections.

### Don't
- Do not use color to decorate or brand; it is reserved for status and third-party identity.
- Do not rest a link or button on an underline; reveal it on hover and focus.
- Do not use system fonts or other brand fonts.
- Do not use shadows on controls such as buttons or inputs; reserve them for cards, including the Composer Card.
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
3. **Composer Card:** `Design a message composer with a 12px border-radius, a white background, a 1px #eaeaea border, 12px padding, and a box-shadow of '0px 1px 2px 0px rgba(0,0,0,0.04), 0px 8px 20px -8px rgba(0,0,0,0.08)'.`

## Similar Brands

- **Linear** — Shares the high-contrast, black/white/gray palette and surgically precise typography.
- **GitHub** — Similar utilitarian, developer-centric aesthetic with a focus on functional components over decoration.
- **Read.cv** — Extreme typography-first approach on a minimal, monochrome canvas.
- **Height** — Clean, high-contrast UI with a similar approach to minimal buttons and inputs.

## Quick Start

### CSS Custom Properties

A plain-CSS translation of the same system, for use outside Tailwind. Its variable names are deliberately more conventional than the Tailwind ones below — `--leading-caption` rather than `--text-caption--line-height`, `--page-max-width` and `--card-padding` rather than nothing. **The Tailwind v4 block is the authoritative one**: it matches `src/assets/main.css`, which is what the application actually implements. The layout values below are conventions for a plain-CSS consumer and are not defined as variables in the app.


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
  --font-sans: 'Geist', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

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
  --shadow-elevated: rgba(0, 0, 0, 0.04) 0px 1px 2px 0px, rgba(0, 0, 0, 0.08) 0px 8px 20px -8px;
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
  --font-sans: 'Geist', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

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

  /* Border Radius */
  --radius-md: 4px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-3xl: 35px;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px, rgba(0, 0, 0, 0.04) 0px 2px 1px 0px;
  --shadow-subtle-2: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px;
  --shadow-elevated: rgba(0, 0, 0, 0.04) 0px 1px 2px 0px, rgba(0, 0, 0, 0.08) 0px 8px 20px -8px;
  --shadow-xl: rgba(0, 0, 0, 0.25) 0px 25px 50px -12px;
  --shadow-subtle-3: rgba(0, 0, 0, 0.04) 0px 2px 2px 0px, rgba(0, 0, 0, 0.04) 0px 8px 8px -8px;
}
```
