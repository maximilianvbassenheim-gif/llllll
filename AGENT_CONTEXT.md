# Agent Context: Project Overview

## 1. Project identity
This project is a static browser game / arcade project with a monetization layer and a branded companion site.

Primary repository:
- `C:\Users\maxim\copilot-worktrees\llllll\maximilianvbassenheim-gif-fictional-chainsaw`

Repository purpose:
- Publish a collection of HTML5 browser games for free
- Host a game hub and branded landing pages
- Offer optional monetization via ads, paid Pro version, and future traffic growth

Project live URLs:
- Arcade: https://maximilianvbassenheim-gif.github.io/llllll/
- Shakker Kids: https://maximilianvbassenheim-gif.github.io/llllll/shakker-kids/

## 2. High-level status
Current repo state:
- Static HTML/CSS/JS website
- No framework required
- No build pipeline required
- Good for GitHub Pages / Netlify / Cloudflare Pages / static hosting

This is not a backend app and not a Node build system project.
The main requirements are website correctness, gameplay quality, monetization hooks, and usability.

## 3. Core file map
Important root files:
- `README.md` — primary project overview and business context
- `index.html` — arcade hub / entry point
- `css/style.css` — shared styling
- `js/ads.js` — ad slot logic
- `js/sfx.js` — sound engine and mute logic
- `js/store.js` — Pro purchase logic

Key game directories:
- `games/` — all browser games
- `games/weltherrschaft.html` — Pinky & Brain idle/clicker game
- `games/whack.html` — whack game
- `games/memory.html` — memory game
- `games/snake.html`
- `games/breakout.html`
- `games/2048.html`
- `games/flappy.html`

Production / documentation:
- `produktion/` — operational / production notes and how-to docs
- `produktion/00-START-HIER.md` — recommended start doc

## 4. What is already implemented
The repository already includes:
- an arcade hub landing page
- several classic browser games
- player sound engine
- ad slot system
- Pro purchase flow (client-side localStorage gating)
- game logic for a more advanced idle/clicker game
- achievements, prestige mechanics, and auto-save in browser

Specific known features:
- Pinky & Brain idle / strategy game with plans, upgrades, achievements, prestige
- sound engine with mute button
- static site monetization layer
- support for free hosting + optional paid version

## 5. Business and monetization logic
Important note from project docs:
- Code alone does not create revenue
- Real revenue depends on traffic and distribution
- The repo provides the product foundation and monetization hooks

Current monetization concepts already in repo:
- ad slots via `js/ads.js`
- Pro version upsell via `js/store.js`
- localStorage gating for premium state
- possibility to integrate Stripe or Gumroad payment links

The project is intentionally simple and static to maximize easy deployment.

## 6. Local run instructions
The simplest local approach:

```bash
python3 -m http.server 8000
```
Then open:
- `http://localhost:8000`

This is the expected local preview method for a static HTML project.

## 7. Deployment / hosting
This project is designed for static hosting.
Supported hosting patterns:
- GitHub Pages
- Netlify
- Vercel
- Cloudflare Pages

No complex build system is required.

## 8. Known constraints / important caveats
These are important for the agent:
- This is a static project; do not assume a backend exists.
- Monetization is intentionally simple and client-side.
- Pro unlocking is not cryptographically secure if you need strict revenue protection.
- Real earnings require traffic generation, not just code.
- The main value of this repository is the product + distribution foundation.

## 9. Suggested role for the coding agent
The agent should treat this as a lightweight product / web app project that is already functional and needs improvement, polishing, or expansion.

Primary tasks may include:
- fix broken game logic
- improve UX / visuals
- optimize page performance
- add new games or features
- refine monetization flow
- improve accessibility and mobile responsiveness
- improve documentation and release readiness

## 10. Recommended working principles for future work
- Keep the project static and simple
- Prefer directly editable HTML/CSS/JS over framework churn
- Preserve GitHub Pages compatibility
- Do not add heavy build dependencies unless absolutely required
- Keep business logic and monetization clear and understandable
- Prefer minimal, reliable changes over broad rewrites

## 11. Docker / environment note
There is no evidence of a production Docker setup in the current repo.
For this project, Docker is optional and unnecessary unless the user explicitly wants containerized local dev or deployment.

If containerization is needed later, the simplest approach is a lightweight static server image, not a complex app stack.

## 12. Key command summary
Useful commands for local use:

```bash
# start local static server
python3 -m http.server 8000

# open in browser
# http://localhost:8000
```

## 13. Compression summary for agent memory
If the agent has limited context, the most important facts to retain are:
1. This is a static HTML5 games repository.
2. It is intended for GitHub Pages and simple hosting.
3. Core logic lives in root `js/` and `games/` files.
4. Monetization is already partially implemented via ads and Pro purchase flow.
5. Revenue depends more on traffic than on code alone.
6. The project should stay lightweight and static unless a strong reason requires otherwise.

## 14. Next-step guidance
If a new agent continues from here, the best next move is to:
- inspect the main game files and entry points
- verify the games function in browser
- identify actual broken behavior or low-value friction
- make incremental improvements
- update the docs if the project direction changes

## 15. Additions to keep in future
If you want to keep this file useful over time, add:
- key findings from debugging sessions
- known bugs and fixes
- links to important branches / PRs
- notes on user requests or product decisions
- a short “what is still missing” section
- a “what the agent must not break” section

This file is intended as a compact memory dump for future autonomous work.
