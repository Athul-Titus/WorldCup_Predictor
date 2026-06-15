---
name: KickStats
colors:
  surface: '#0d1516'
  surface-dim: '#0d1516'
  surface-bright: '#333a3c'
  surface-container-lowest: '#080f11'
  surface-container-low: '#151d1e'
  surface-container: '#192122'
  surface-container-high: '#242b2d'
  surface-container-highest: '#2e3638'
  on-surface: '#dce4e5'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#dce4e5'
  inverse-on-surface: '#2a3233'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#fff9ef'
  on-secondary: '#3a3000'
  secondary-container: '#ffdb3c'
  on-secondary-container: '#725f00'
  tertiary: '#ffeac0'
  on-tertiary: '#3e2e00'
  tertiary-container: '#fec931'
  on-tertiary-container: '#6f5500'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#ffe16d'
  secondary-fixed-dim: '#e9c400'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#544600'
  tertiary-fixed: '#ffdf96'
  tertiary-fixed-dim: '#f3bf26'
  on-tertiary-fixed: '#251a00'
  on-tertiary-fixed-variant: '#594400'
  background: '#0d1516'
  on-background: '#dce4e5'
  surface-variant: '#2e3638'
typography:
  display-lg:
    fontFamily: Archivo Narrow
    fontSize: 48px
    fontWeight: '900'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Archivo Narrow
    fontSize: 32px
    fontWeight: '900'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Archivo Narrow
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
  stat-huge:
    fontFamily: Archivo Narrow
    fontSize: 40px
    fontWeight: '900'
    lineHeight: '1'
    letterSpacing: 0.02em
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Archivo Narrow
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.1em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1280px
---

## Brand & Style
The design system is engineered for high-performance sports analytics, evoking the high-stakes atmosphere of a floodlit stadium. The aesthetic is inspired by premium football simulation titles (EA FC/PES), blending data-density with a cinematic, glowing interface.

**Style: High-Contrast / Data-Rich**
- **Emotional Response:** Professional, urgent, precise, and immersive.
- **Visual Narrative:** The UI should feel like a tactical "Command Center" for the World Cup. Use of dark glass surfaces, neon accents, and subtle pitch-inspired textures creates a sense of technological sophistication.
- **Surface Treatment:** Backgrounds are never flat; they utilize subtle radial gradients and faint grid overlays (reminiscent of pitch patterns) to provide depth.

## Colors
The palette is built on a "Stadium Night" logic, where high-energy accents pierce through deep navy shadows.

- **Primary (Cyan):** Used for interactive elements, primary call-to-actions, and active data states. It represents the "energy" of the pitch.
- **Secondary (Gold):** Reserved for prestige moments—MVPs, trophy statistics, and premium membership indicators.
- **Functional Colors:** Win Green and Danger Red are utilized strictly for performance indicators (Form guides, Win/Loss probability).
- **Surface Logic:** Backgrounds use `#0a1628`. Cards and containers use `#0d1f3c` to create a tiered elevation system without relying on shadows.

## Typography
The typography system balances the aggressive impact of sports broadcasting with the readability required for data science.

- **Headlines & Stats:** Use **Archivo Narrow** (Bold/Black). This condensed face allows for large, impactful numbers and headers that fit within tight data columns. Headlines should predominantly be uppercase.
- **Body & Metadata:** Use **Hanken Grotesk**. This contemporary sans-serif provides high legibility for long-form analysis and player bios against dark backgrounds.
- **Numbers:** Numerical data should always use Archivo Narrow to maintain the "Scoreboard" aesthetic.

## Layout & Spacing
The layout follows a **structured grid** philosophy, mimicking the tactical grids used in football coaching.

- **Grid:** A 12-column system for desktop, 6 for tablet, and 2 or 4 for mobile.
- **Rhythm:** An 8px base unit drives all spacing. This ensures consistent alignment of data points.
- **Density:** High density is preferred. Information should be grouped into logical "Modules" or "Pods" to allow for quick scanning of complex stats.
- **Pitch Overlays:** Large-scale background sections may feature a subtle, 5% opacity geometric line-art pattern representing different thirds of the football pitch.

## Elevation & Depth
In this design system, depth is achieved through **luminance and borders** rather than traditional shadows.

- **Tonal Layering:** The primary background is the lowest layer. Cards (#0d1f3c) sit one level above.
- **Glowing Borders:** Instead of shadows, use 1px borders using the Primary Cyan at 15-20% opacity. For "Active" or "Highlighted" cards, increase border opacity to 50% and add a subtle 8px Cyan outer glow (blur).
- **Glassmorphism:** Overlays and dropdowns should use a backdrop-blur (12px) with a semi-transparent version of the surface color to maintain the feeling of a sophisticated HUD.

## Shapes
The shape language is "Athletic-Geometric"—precise and modern.

- **Cards/Containers:** Use 8px (`rounded-lg`) corners. This provides a professional, modern feel that isn't too soft.
- **Interactive Small Elements:** Badges, tags, and small buttons use 4px (`rounded-sm`) to maintain a sharper, technical edge.
- **Indicators:** Progress bars and "Win Probability" meters should use flat, unrounded ends to reinforce the data-heavy, technical nature of the app.

## Components

- **Buttons:** Primary buttons use a solid Cyan fill with Black text for maximum contrast. Secondary buttons use a Cyan ghost style (Cyan border, no fill) with Cyan text.
- **Cards:** Dark navy surfaces with 1px Cyan borders (20% opacity). Headers within cards should have a subtle bottom divider.
- **Data Tables:** Row-based with no vertical lines. Use alternating row highlights (subtle 2% lighter navy) and a Cyan left-border highlight for "Selected" players/teams.
- **Badges/Chips:** Used for player positions (e.g., "FWD", "MID"). These use the 4px rounded corners and a low-opacity fill of the accent color.
- **Input Fields:** Darker than the card surface, with a 1px Cyan bottom-border only. On focus, the bottom border glows.
- **Stat Visualizers:** Radar charts and bar graphs must use the primary Cyan for the user's focus and Muted Navy for benchmarks. Gold is used only for "Top Performer" metrics.
- **Pitch Map:** A custom component representing the field. Lines should be 1px Cyan at 10% opacity, with players represented by glowing Cyan or Gold dots.