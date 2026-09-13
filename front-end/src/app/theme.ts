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
  },
})
