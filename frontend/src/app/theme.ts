import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

export const AiChatPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#f5f5f5',
      100: '#e5e5e5',
      200: '#d4d4d4',
      300: '#a3a3a3',
      400: '#737373',
      500: '#171717',
      600: '#000000',
      700: '#000000',
      800: '#000000',
      900: '#000000',
      950: '#000000',
    },
    focusRing: {
      width: '2px',
      style: 'solid',
      color: '#171717',
      offset: '2px',
    },
    disabledOpacity: '0.35',
    colorScheme: {
      light: {
        primary: {
          color: '{primary.500}',
          inverseColor: '#ffffff',
          hoverColor: 'color-mix(in srgb, var(--color-ink) 90%, var(--color-canvas))',
          activeColor: 'color-mix(in srgb, var(--color-ink) 90%, var(--color-canvas))',
        },
        highlight: {
          background: '#171717',
          focusBackground: '#171717',
          color: '#ffffff',
          focusColor: '#ffffff',
        },
        surface: {
          0: '#ffffff',
          50: '#fafafa',
          100: '#f5f5f5',
          200: '#eaeaea',
          300: '#d4d4d4',
        },
        formField: {
          color: 'var(--color-ink)',
          borderColor: 'var(--color-line)',
          hoverBorderColor: '#d4d4d4',
          placeholderColor: 'var(--color-subtext)',
          iconColor: 'var(--color-icon)',
        },
      },
    },
  },
  components: {
    button: {
      root: {
        borderRadius: '8px',
      },
      colorScheme: {
        light: {
          outlined: {
            secondary: {
              hoverBackground: 'color-mix(in srgb, var(--color-line) 40%, transparent)',
              activeBackground: 'color-mix(in srgb, var(--color-line) 60%, transparent)',
              borderColor: 'var(--color-line)',
              color: 'var(--color-ink)',
            },
          },
        },
      },
    },
    inputtext: {
      root: {
        borderRadius: '12px',
      },
    },
    password: {
      root: {
        borderRadius: '12px',
      },
    },
    textarea: {
      root: {
        background: 'transparent',
        borderColor: 'transparent',
        hoverBorderColor: 'transparent',
        focusBorderColor: 'transparent',
        color: '#171717',
        placeholderColor: '#666666',
        shadow: 'none',
        paddingX: '0',
        paddingY: '0',
        borderRadius: '12px',
        focusRing: {
          width: '0',
          style: 'none',
          color: 'transparent',
          offset: '0',
          shadow: 'none',
        },
      },
    },
    avatar: {
      root: {
        width: '1.5rem',
        height: '1.5rem',
        fontSize: '0.75rem',
        background: '#171717',
        color: '#ffffff',
      },
    },
    listbox: {
      root: {
        background: 'transparent',
        borderColor: 'transparent',
        color: '#171717',
        shadow: 'none',
        borderRadius: '12px',
      },
      list: {
        padding: '0',
        gap: '2px',
      },
      option: {
        color: '#171717',
        focusBackground: '#eaeaea',
        focusColor: '#171717',
        selectedBackground: '#eaeaea',
        selectedColor: '#171717',
        selectedFocusBackground: '#eaeaea',
        selectedFocusColor: '#171717',
        borderRadius: '8px',
        padding: '6px 10px',
      },
    },
    menu: {
      root: {
        background: '#ffffff',
        borderColor: '#eaeaea',
        borderRadius: '12px',
      },
      list: {
        padding: '6px',
        gap: '2px',
      },
      item: {
        color: '#171717',
        focusBackground: '#eaeaea',
        focusColor: '#171717',
        borderRadius: '8px',
        padding: '6px 10px',
      },
      separator: {
        borderColor: '#eaeaea',
      },
    },
    dialog: {
      root: {
        background: '#ffffff',
        borderColor: '#eaeaea',
        borderRadius: '12px',
      },
      header: {
        padding: '20px 24px 0',
      },
      content: {
        padding: '16px 24px 24px',
      },
      title: {
        color: '#171717',
      },
    },
    // Icon-only controls need a label on hover; the tooltip takes the same 8px
    // radius as every other control, over an Ink fill. Colours live under
    // colorScheme.light.root — that is where Aura keeps them.
    //
    // `gutter: 0` removes the tail: the arrow is a CSS-bordered triangle sized
    // by the gutter, so a zero gutter collapses it and drops the offset. The
    // theme styles no font-size, so the size comes from a `text-caption` class
    // on each usage.
    tooltip: {
      root: {
        gutter: '0px',
        borderRadius: '8px',
        padding: '5px 10px',
        maxWidth: '14rem',
      },
      colorScheme: {
        light: {
          root: {
            background: 'var(--color-ink)',
            color: 'var(--color-paper-white)',
          },
        },
      },
    },
  },
})
