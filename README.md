# 🕹️ Pixel Arcade & 🎵 Shakker Kids

**🌐 LIVE:**
- Arcade: https://maximilianvbassenheim-gif.github.io/llllll/
- Shakker Kids (Song-Marke): https://maximilianvbassenheim-gif.github.io/llllll/shakker-kids/
- 📦 Produktions-Handbuch: [`produktion/00-START-HIER.md`](produktion/00-START-HIER.md) 🔦

Eine startklare, monetarisierbare Sammlung kostenloser HTML5-Browserspiele:
**Snake, Breakout, 2048 und Flappy**. Reines HTML/CSS/JavaScript – keine
Frameworks, keine Build-Tools, läuft auf jedem statischen Hosting.

```
.
├── index.html          # Arcade-Hub
├── css/style.css       # Styling
├── js/ads.js           # Monetarisierungs-Layer (Werbeplätze)
├── js/sfx.js           # Sound-Engine (Web Audio) + Mute-Button
├── js/store.js         # Verkauf "Pro" für 1,99 € (werbefrei)
└── games/
    ├── weltherrschaft.html  # 🧠🐭 Pinky & Brain – Idle-Clicker (Prestige, Erfolge, Upgrades)
    ├── whack.html           # 🔨 Whack-a-Pinky
    ├── memory.html          # 🧩 Brain-Memory
    ├── snake.html
    ├── breakout.html
    ├── 2048.html
    └── flappy.html
```

> ⭐ **Highlight:** *Pinky & Brain – Plan zur Weltherrschaft* ist ein voll ausgebautes
> Idle-/Clicker-Spiel:
> - **Pläne** (Pinky, Geheimlabor, Roboter-Armee, Hypno-Satellit, Mond-Rakete, Zeitmaschine, Klonarmee)
> - **Upgrades** (mehr pro Klick, Auto-Klicker, ×2-Produktion)
> - **Goldene Ideen** für Bonus-Klicks
> - **10 Erfolge/Achievements**
> - **Prestige** („Welt neu erobern" → Hirnzellen geben +10% Produktion pro Stück, dauerhaft)
> - Auto-Save im Browser (localStorage)

## ▶️ Lokal starten

Einfach `index.html` im Browser öffnen – oder ein Mini-Server:

```bash
python3 -m http.server 8000
# dann http://localhost:8000 öffnen
```

## 🌐 Kostenlos veröffentlichen (5 Minuten)

- **GitHub Pages**: Repo-Settings → Pages → Branch `main` → `/ (root)`.
- **Netlify / Vercel / Cloudflare Pages**: Repo verbinden, fertig (statische Seite).

---

## 💶 Ehrlich zum Thema „50.000 € einbringen"

**Wichtig und ehrlich:** Code allein bringt kein Geld. Auch das beste Spiel
verdient 0 €, solange es niemand spielt. Umsatz entsteht aus
**Reichweite × Monetarisierung**. Niemand kann „direkt 50.000 €" garantieren –
das hängt komplett von Traffic, Nische und Vermarktung ab.

Diese Sammlung gibt dir aber die **technische Grundlage**, die du dafür
brauchst. Realistische Wege zu Umsatz:

### 0. Verkauf für 1,99 € (Pro-Version)
Ein Kauf-Flow ist eingebaut (`js/store.js`): Banner „Pixel Arcade Pro – 1,99 €",
Käufer spielen **werbefrei** und bekommen ein PRO-Badge. So aktivierst du den
echten Verkauf (ohne eigenen Server):

1. Bezahl-Link anlegen – am einfachsten **Stripe Payment Link**
   (https://dashboard.stripe.com/payment-links) oder **Gumroad** – Produkt 1,99 €.
2. Beim Anbieter die Weiterleitung **nach der Zahlung** auf deine Seite mit
   `?pro=1` setzen, z. B. `https://DEINNAME.github.io/llllll/?pro=1`.
3. Diesen Link in `js/store.js` bei `PAYMENT_LINK` eintragen. Fertig.

> ⚠️ Ehrlich: Die Freischaltung läuft clientseitig (localStorage) und ist bei
> 1,99 € ohne Server bewusst simpel – nicht kopiergeschützt. Für harten Schutz
> bräuchtest du ein Backend, das Stripe-Webhooks prüft.

### 1. Werbung (am einfachsten)
Die Werbeplätze (`.ad-slot`) sind bereits eingebaut. So aktivierst du sie:

1. [Google AdSense](https://adsense.google.com)-Konto anlegen.
2. In `js/ads.js` deine `adsenseClientId` und `adsenseSlotId` eintragen.
3. Das AdSense-Script in den `<head>` jeder Seite einbinden.

**Größenordnung:** Browserspiel-Traffic bringt grob **1–5 € pro 1.000
Seitenaufrufe** (RPM). Für 50.000 € bräuchtest du also realistisch
**10–50 Millionen Seitenaufrufe** über die Laufzeit. Das ist erreichbar, aber
nur mit konstantem Traffic über Monate/Jahre.

### 2. Reichweite aufbauen (der eigentliche Hebel)
- Spiele auf Portalen einreichen: **CrazyGames, Poki, GameDistribution, itch.io**
  (teilen Werbeeinnahmen mit dir, bringen sofort Spieler).
- SEO: eigene Domain, gute Titel/Beschreibungen, Lighthouse-Score hoch halten.
- TikTok/YouTube Shorts/Reels mit Gameplay-Clips – billigster Traffic-Kanal.

### 3. Weitere Monetarisierung
- **Sponsoring/Lizenz**: Manche Portale kaufen exklusive Spiele für Pauschalen.
- **In-Game-Käufe**: Skins, Extra-Leben (z. B. via Stripe).
- **Verkauf des Quellcodes** als Template auf Marktplätzen (CodeCanyon o. ä.).

### Realistischer Fahrplan
| Schritt | Aufwand | Effekt |
|--------|---------|--------|
| Veröffentlichen + AdSense | Stunden | Grundlage |
| Auf 3–4 Spieleportale stellen | Tage | erster echter Traffic |
| 5–10 weitere Spiele ergänzen | Wochen | mehr Verweildauer & Aufrufe |
| Social-Media-Clips regelmäßig | laufend | skalierender Traffic |

Kurz: Die 50.000 € sind ein **Marketing- und Durchhalte-Ziel**, kein
Code-Knopf. Diese Repo liefert dir das Produkt – der Rest ist Distribution.
