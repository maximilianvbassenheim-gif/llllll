/*
 * Mini-Soundengine (Web Audio, keine externen Dateien).
 * Erzeugt kurze Töne prozedural. Fügt automatisch einen Mute-Button hinzu.
 * Einbindung: <script src="../js/sfx.js"></script>  (auf Hub: js/sfx.js)
 * Nutzung:    SFX.click(), SFX.eat(), SFX.hit(), SFX.die(), SFX.score(),
 *             SFX.match(), SFX.buy(), SFX.ach(), SFX.win()
 */
const SFX = {
  enabled: localStorage.getItem("sfx_muted") !== "1",
  ctx: null,

  ac() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
    return this.ctx;
  },

  tone(freq, dur, type = "square", vol = 0.15, slideTo = null) {
    if (!this.enabled) return;
    const ctx = this.ac();
    if (!ctx) return;
    const t = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t);
    if (slideTo) osc.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    gain.gain.setValueAtTime(vol, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t);
    osc.stop(t + dur);
  },

  seq(notes) { // notes: [[freq,dur,type?,vol?], ...]
    if (!this.enabled) return;
    let delay = 0;
    notes.forEach(([f, d, type, vol]) => {
      setTimeout(() => this.tone(f, d, type || "square", vol || 0.15), delay * 1000);
      delay += d;
    });
  },

  click() { this.tone(220, 0.05, "square", 0.10); },
  eat()   { this.tone(520, 0.08, "square", 0.14, 760); },
  hit()   { this.tone(180, 0.06, "sawtooth", 0.14); },
  score() { this.tone(660, 0.10, "triangle", 0.16, 990); },
  die()   { this.seq([[300, 0.12, "sawtooth"], [200, 0.16, "sawtooth"], [120, 0.22, "sawtooth"]]); },
  match() { this.seq([[523, 0.08, "triangle"], [784, 0.12, "triangle"]]); },
  buy()   { this.seq([[440, 0.05], [660, 0.08]]); },
  ach()   { this.seq([[523, 0.09, "triangle"], [659, 0.09, "triangle"], [880, 0.16, "triangle"]]); },
  win()   { this.seq([[523, 0.12], [659, 0.12], [784, 0.12], [1046, 0.28, "triangle"]]); },

  toggle() {
    this.enabled = !this.enabled;
    localStorage.setItem("sfx_muted", this.enabled ? "0" : "1");
    this.updateBtn();
    if (this.enabled) this.click();
  },

  updateBtn() {
    if (this.btn) this.btn.textContent = this.enabled ? "🔊" : "🔇";
  },

  initButton() {
    const b = document.createElement("button");
    b.id = "sfx-toggle";
    b.title = "Ton an/aus";
    b.style.cssText =
      "position:fixed;left:16px;bottom:16px;z-index:80;width:44px;height:44px;" +
      "border-radius:50%;border:1px solid rgba(255,255,255,.15);cursor:pointer;" +
      "background:#20233f;color:#fff;font-size:1.2rem;box-shadow:0 6px 20px rgba(0,0,0,.4);";
    b.addEventListener("click", () => this.toggle());
    this.btn = b;
    document.body.appendChild(b);
    this.updateBtn();
  },
};

window.SFX = SFX;
document.addEventListener("DOMContentLoaded", () => SFX.initButton());
// Audio-Kontext beim ersten User-Input freischalten (Browser-Policy)
document.addEventListener("pointerdown", () => SFX.ac(), { once: true });
