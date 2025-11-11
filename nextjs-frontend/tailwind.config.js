/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",

    // Or if using `src` directory:
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontSize: {
        // More reader-friendly font sizes
        'xs': ['0.875rem', { lineHeight: '1.25rem' }],      // 14px (was 12px)
        'sm': ['1rem', { lineHeight: '1.5rem' }],           // 16px (was 14px)
        'base': ['1.125rem', { lineHeight: '1.75rem' }],    // 18px (was 16px)
        'lg': ['1.25rem', { lineHeight: '1.75rem' }],       // 20px (was 18px)
        'xl': ['1.5rem', { lineHeight: '2rem' }],           // 24px (was 20px)
        '2xl': ['1.875rem', { lineHeight: '2.25rem' }],     // 30px (was 24px)
        '3xl': ['2.25rem', { lineHeight: '2.5rem' }],       // 36px (was 30px)
        '4xl': ['3rem', { lineHeight: '1' }],               // 48px (was 36px)
        '5xl': ['3.75rem', { lineHeight: '1' }],            // 60px (was 48px)
        '6xl': ['4.5rem', { lineHeight: '1' }],             // 72px (was 60px)
      },
      spacing: {
        // Larger spacing for better readability
        '18': '4.5rem',    // 72px
        '88': '22rem',     // 352px
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        chart: {
          1: "hsl(var(--chart-1))",
          2: "hsl(var(--chart-2))",
          3: "hsl(var(--chart-3))",
          4: "hsl(var(--chart-4))",
          5: "hsl(var(--chart-5))",
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
