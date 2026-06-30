/*
 * Monetization layer.
 * ----------------------------------------------------------------------------
 * Werbeplätze (.ad-slot) sind im Markup vorbereitet. Um echtes Geld zu
 * verdienen, hinterlege deine Ad-Network-ID und ersetze den Platzhalter durch
 * den echten Anzeigen-Code (z. B. Google AdSense).
 *
 * Schnellstart Google AdSense:
 *   1. Konto erstellen: https://adsense.google.com
 *   2. Deine Publisher-ID (ca-pub-XXXXXXXX) unten eintragen.
 *   3. AdSense-Script im <head> jeder Seite einbinden.
 *   4. Diese Datei rendert die Anzeigen dann automatisch in jeden .ad-slot.
 */
const MONETIZATION = {
  // Trage hier deine echte Publisher-ID ein, um Anzeigen zu aktivieren:
  adsenseClientId: "", // z. B. "ca-pub-1234567890123456"
  adsenseSlotId: "",   // z. B. "1234567890"
};

function renderAds() {
  const slots = document.querySelectorAll(".ad-slot");

  // Pro-Käufer (1,99 €) spielen werbefrei: Werbeplätze entfernen.
  if (window.STORE && window.STORE.isPro()) {
    slots.forEach((slot) => slot.remove());
    return;
  }

  const active = MONETIZATION.adsenseClientId && MONETIZATION.adsenseSlotId;

  slots.forEach((slot) => {
    if (active) {
      const ins = document.createElement("ins");
      ins.className = "adsbygoogle";
      ins.style.display = "block";
      ins.setAttribute("data-ad-client", MONETIZATION.adsenseClientId);
      ins.setAttribute("data-ad-slot", MONETIZATION.adsenseSlotId);
      ins.setAttribute("data-ad-format", "auto");
      ins.setAttribute("data-full-width-responsive", "true");
      slot.innerHTML = "";
      slot.appendChild(ins);
      try {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      } catch (e) {
        slot.textContent = "Werbeplatz";
      }
    } else {
      slot.textContent =
        "Werbeplatz – hier erscheinen Anzeigen, sobald du in js/ads.js deine Ad-Network-ID einträgst.";
    }
  });
}

document.addEventListener("DOMContentLoaded", renderAds);
