/*
 * Store / Pro-Freischaltung – Verkauf der Arcade für 1,99 €.
 * ----------------------------------------------------------------------------
 * WICHTIG: Diese Datei verbindet einen externen Bezahldienst. Du musst KEINE
 * Server programmieren – du brauchst nur einen Bezahl-Link von einem Anbieter:
 *
 *  A) Stripe Payment Link  (https://dashboard.stripe.com/payment-links)
 *     - Produkt "Pixel Arcade Pro", Preis 1,99 € anlegen
 *     - Bei "Nach der Zahlung" -> Weiterleitung auf deine Seite mit ?pro=1
 *       z. B.  https://DEINNAME.github.io/llllll/?pro=1
 *     - Den erzeugten Link unten bei PAYMENT_LINK eintragen.
 *
 *  B) Gumroad / Ko-fi / Lemon Squeezy
 *     - Produkt 1,99 € anlegen, Weiterleitung/Redirect auf ...?pro=1 setzen
 *     - Produkt-Link unten eintragen.
 *
 * HINWEIS ZUR EHRLICHKEIT: Die Freischaltung läuft clientseitig (localStorage).
 * Das ist bei einem 1,99-€-Casual-Produkt ohne Server üblich, aber NICHT
 * kopiergeschützt – technisch versierte Nutzer können es umgehen. Für echten
 * Schutz bräuchtest du ein Backend, das Stripe-Webhooks prüft.
 */
const STORE = {
  price: "1,99 €",
  // Hier deinen echten Bezahl-Link eintragen:
  PAYMENT_LINK: "", // z. B. "https://buy.stripe.com/xxxxxxxx"

  isPro() {
    return localStorage.getItem("arcade_pro") === "1";
  },

  unlock() {
    localStorage.setItem("arcade_pro", "1");
  },

  // Nach Rückkehr vom Bezahldienst: ?pro=1 schaltet frei
  handleReturn() {
    const params = new URLSearchParams(location.search);
    if (params.get("pro") === "1") {
      this.unlock();
      // URL säubern, damit der Param nicht hängen bleibt
      history.replaceState({}, "", location.pathname);
      this.showThanks();
    }
  },

  showThanks() {
    const t = document.createElement("div");
    t.style.cssText =
      "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);" +
      "background:#2ecc71;color:#fff;padding:14px 20px;border-radius:10px;" +
      "box-shadow:0 6px 20px rgba(0,0,0,.4);z-index:90;font-weight:700;";
    t.textContent = "✅ Danke! Pixel Arcade Pro ist freigeschaltet – werbefrei!";
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 4000);
  },

  buy() {
    if (!this.PAYMENT_LINK) {
      alert(
        "Es ist noch kein Bezahl-Link hinterlegt.\n\n" +
        "Trage in js/store.js bei PAYMENT_LINK deinen Stripe-/Gumroad-Link ein, " +
        "dann funktioniert der Kauf für " + this.price + "."
      );
      return;
    }
    location.href = this.PAYMENT_LINK;
  },

  // Kauf-Banner auf dem Hub einfügen
  renderBanner() {
    if (this.isPro()) return; // Pro-Nutzer brauchen kein Banner
    const host = document.getElementById("store-banner");
    if (!host) return;
    host.innerHTML =
      '<div style="background:linear-gradient(160deg,#2d1b4e,#1a1c33);border:1px solid var(--accent);' +
      'border-radius:16px;padding:20px;text-align:center;box-shadow:var(--shadow);">' +
      '<h3 style="margin-bottom:6px;">⭐ Pixel Arcade Pro – ' + this.price + '</h3>' +
      '<p style="color:var(--muted);margin-bottom:12px;">Einmal zahlen: komplett werbefrei spielen & uns unterstützen.</p>' +
      '<button class="btn" id="buy-btn">Für ' + this.price + ' freischalten</button>' +
      "</div>";
    document.getElementById("buy-btn").addEventListener("click", () => this.buy());
  },

  // Pro-Badge im Header anzeigen
  renderBadge() {
    if (!this.isPro()) return;
    const h = document.querySelector("header.site h1");
    if (h && !h.dataset.pro) {
      h.dataset.pro = "1";
      const span = document.createElement("span");
      span.textContent = " PRO";
      span.style.cssText =
        "font-size:.4em;vertical-align:super;background:#2ecc71;color:#fff;" +
        "padding:2px 8px;border-radius:8px;-webkit-text-fill-color:#fff;margin-left:6px;";
      h.appendChild(span);
    }
  },
};

document.addEventListener("DOMContentLoaded", () => {
  STORE.handleReturn();
  STORE.renderBanner();
  STORE.renderBadge();
});
window.STORE = STORE;
