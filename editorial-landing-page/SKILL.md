---
name: editorial-landing-page
description: Use this skill when building a new marketing site or landing page, especially in Next.js 15 App Router + Tailwind v4 + TypeScript. Trigger it whenever the user wants a landing page, marketing site, or hero page that feels editorially designed (dark theme, one-idea-per-section) rather than template-sourced or AI-generated. Covers the color system, fonts, button/eyebrow patterns, and critical gotchas (stroke text, glow hover, Satori/next-og, Resend lazy init, iOS video autoplay, stripping AI co-author trailers).
---

# Skill: Editorial Landing Page System

## What problem it solves
Building marketing sites that feel designed — not AI-generated, not template-sourced.
The full system lives at `~/Desktop/LANDING_PAGE_PLAYBOOK.md`. This file is the condensed operational reference.

## When to use
Any new marketing site or landing page project. Paste the bootstrap prompt (section 18 of the playbook) into the first chat and the whole system loads.

## Bootstrap prompt (paste into any new chat)
> I'm building a landing page in Next.js 15 App Router + Tailwind v4 + TypeScript. Use the Landing Page Playbook system: dark theme by default with bg `#0F0F11`, surface `#1A1A1E`, text `#EEEEEF`/`#A0A0AB`/`#6C6C74`, one accent color (precious — used 2-3x max), one secondary accent (rarer, the emotional moment). Fonts: Syne 800 headlines + Space Grotesk 400 body + mono uppercase eyebrows with `tracking-[0.2em]`. Section wrapper is `py-28 px-6 border-t border-[#2A2A2F]` with `max-w-6xl mx-auto`. Buttons shrink on hover (`scale-95`) and flip to accent color — never grow. No pure black or white. No overlays on images. No emojis. No exclamation marks. Editorial > corporate. One idea per section. Stroke text uses inline `WebkitTextStroke`. Glow hover uses a React component with `useState`. Resend for email (lazy init inside handler). OG image via next/og with fonts passed in. Strip any AI co-author trailers before pushing. Full playbook at `LANDING_PAGE_PLAYBOOK.md`.

## Core color slots (fill per project)
| Slot | Dark default | Role |
|---|---|---|
| bg | `#0F0F11` | Page background |
| surface | `#1A1A1E` | Cards, inputs |
| surface-border | `#2A2A2F` | Section dividers |
| text-1 | `#EEEEEF` | Headlines |
| text-2 | `#A0A0AB` | Body |
| text-3 | `#6C6C74` | Eyebrow labels |
| accent-primary | project-specific | CTAs, hover, emphasis |
| accent-secondary | project-specific | Emotional accent — 1-2x per page |

## Critical gotchas

### Stroke text — MUST be inline style
```tsx
// ✅ Works
<span style={{ WebkitTextStroke: "2px #EEEEEF", color: "transparent" }}>word</span>
// ❌ Doesn't work reliably in Tailwind v4
<span className="dunner-stroke">word</span>
```

### Glow hover — MUST be React component
CSS text-shadow hover classes won't apply. Use `useState`:
```tsx
function GlowWord({ children, color = "#22D3EE" }) {
  const [hovered, setHovered] = useState(false);
  return (
    <span
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        color,
        transition: "text-shadow 0.3s ease",
        textShadow: hovered
          ? `0 0 20px ${color}E6, 0 0 50px ${color}99, 0 0 100px ${color}4D`
          : "none",
      }}
    >
      {children}
    </span>
  );
}
```

### Satori (next/og) limitations
- No `-webkit-text-stroke` — use solid color fill
- No `position: sticky`
- Must pass fonts array to `ImageResponse` options or text falls back to generic sans

### Resend lazy init (critical)
```ts
// ✅ Inside handler
export async function POST(request: Request) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return Response.json({ error: "Not configured." }, { status: 500 });
  const resend = new Resend(apiKey); // here, not at module level
}
// ❌ Module level — fails Next.js build with "Missing API key"
const resend = new Resend(process.env.RESEND_API_KEY);
```

### Video — iOS autoplay
All four attributes required or iOS Safari won't autoplay:
```tsx
<video autoPlay loop muted playsInline src="/videos/demo.mp4" />
```
Also: `.mov` doesn't play in Chrome. Always convert to `.mp4` (H.264).

### Git — strip AI co-author trailers
```bash
git filter-branch --msg-filter 'sed "/Co-Authored-By:/d"' -- --all
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
git reflog expire --expire=now --all && git gc --prune=now --aggressive
# verify:
git log --all --format="%an %ae %b" | grep -iE "claude|copilot|cursor" || echo "clean"
```

## Button law
Buttons **shrink** on hover — never grow:
```tsx
className="... hover:scale-95 active:scale-90 hover:bg-[#FF1A1A] hover:text-white"
```

## Section eyebrow pattern (used everywhere)
```tsx
<p className="font-mono text-xs tracking-[0.2em] text-[#6C6C74] uppercase mb-6">Label</p>
<h2 className="text-4xl md:text-5xl font-bold text-[#EEEEEF] tracking-tight leading-tight mb-6">Headline</h2>
<p className="text-[#A0A0AB] text-lg leading-relaxed mb-8">One supporting sentence.</p>
```

## Phone video frame
```tsx
<div
  className="relative rounded-[44px] overflow-hidden border-[8px] border-[#1A1A1E] shadow-[0_30px_80px_-20px_rgba(0,0,0,0.8)]"
  style={{ aspectRatio: "9/19.5", width: "100%", maxWidth: "320px" }}
>
  <video autoPlay loop muted playsInline src="/videos/demo.mp4" className="w-full h-full object-cover" />
  <div className="absolute top-3 left-1/2 -translate-x-1/2 w-24 h-7 bg-black rounded-full pointer-events-none" />
</div>
```

## Reference sites
Linear, Stripe, Vercel, Cursor, Resend, Mercury, Pitch, Raycast
Inspo: dark.design, heroinspo.com, Mobbin

## Reference: full playbook
`~/Desktop/LANDING_PAGE_PLAYBOOK.md` — 20 sections covering everything.
