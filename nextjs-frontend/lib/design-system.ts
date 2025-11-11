// Design System Constants
// This file centralizes design values to ensure consistency across the application

// Colors
export const colors = {
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  red: {
    500: '#ef4444',
    600: '#dc2626',
  },
  green: {
    500: '#10b981',
    600: '#059669',
  },
  yellow: {
    500: '#f59e0b',
    600: '#d97706',
  },
} as const;

// Spacing
export const spacing = {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '1rem',       // 16px
  lg: '1.5rem',     // 24px
  xl: '2rem',       // 32px
  '2xl': '3rem',    // 48px
  '3xl': '4rem',    // 64px
} as const;

// Border radius
export const borderRadius = {
  sm: '0.25rem',    // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  full: '9999px',
} as const;

// Shadows
export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
} as const;

// Typography
export const typography = {
  fontSizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  },
  fontWeights: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeights: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
} as const;

// Transitions
export const transitions = {
  fast: '150ms ease-in-out',
  normal: '200ms ease-in-out',
  slow: '300ms ease-in-out',
} as const;

// Z-index
export const zIndex = {
  dropdown: 1000,
  modal: 1050,
  tooltip: 1100,
} as const;

// Component-specific constants
export const components = {
  modal: {
    backdropOpacity: '0.5',
    maxWidth: {
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-xl',
      '2xl': 'max-w-2xl',
    },
    padding: spacing.lg,
    borderRadius: borderRadius.lg,
  },
  card: {
    padding: spacing.lg,
    borderRadius: borderRadius.lg,
    shadow: shadows.md,
    hoverShadow: shadows.lg,
  },
  button: {
    padding: {
      sm: `${spacing.sm} ${spacing.md}`,
      md: `${spacing.md} ${spacing.lg}`,
      lg: `${spacing.lg} ${spacing.xl}`,
    },
    borderRadius: borderRadius.md,
    transition: transitions.fast,
  },
  input: {
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: borderRadius.md,
    borderColor: colors.gray[300],
    focusBorderColor: colors.primary[500],
    focusRingColor: colors.primary[500],
  },
  dropdown: {
    borderRadius: borderRadius.md,
    shadow: shadows.lg,
    zIndex: zIndex.dropdown,
  },
} as const;

// Layout constants
export const layout = {
  sidebar: {
    width: '4rem', // 64px
  },
  header: {
    height: '4rem', // 64px
  },
  container: {
    maxWidth: '1200px',
    padding: spacing.xl,
  },
} as const;

// Notebook-specific constants
export const notebook = {
  card: {
    minHeight: '180px',
    iconSize: '1.5rem', // 24px
    titleMaxLines: 1,
    descriptionMaxLines: 2,
  },
  modal: {
    maxWidth: components.modal.maxWidth.md,
  },
  colors: {
    icon: colors.primary[600],
    badge: colors.gray[100],
    badgeText: colors.gray[500],
  },
} as const; 