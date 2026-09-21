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
          hoverColor: '{primary.600}',
          activeColor: '{primary.700}',
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
      },
    },
  },
  components: {
    button: {
      root: {
        borderRadius: '8px',
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
  },
})
