// Beskjæringsverktøy for forsidebilder, uten avhengigheter.
// - Viser bildet du velger (eller det lagrede originalbildet) med en ramme i 16:9
// - Rammen kan dras og skaleres fra hjørnene med mus og berøring (pointer events),
//   og flyttes med piltastene / skaleres med + og −
// - Rammen kan aldri gå utenfor bildet eller få et annet format
// - Skriver utsnittet i prosent til de skjulte feltene utsnitt_x/y/bredde/hoyde
// - Tegner en forhåndsvisning av den smale banner-stripen på datamaskin og mobil
(() => {
    "use strict";

    // Typiske skjermer, brukt til forhåndsvisningen av banneret (se .hero i style.css)
    const SKJERMER = {
        datamaskin: { bredde: 1280, hoyde: 608, banner: 64 },
        mobil: { bredde: 390, hoyde: 540, banner: 56 },
    };

    const klem = (verdi, min, maks) => Math.min(Math.max(verdi, min), maks);

    function start() {
        document.querySelectorAll(".utsnitt").forEach(settOpp);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
    else start();

    function settOpp(rot) {
        const [fb, fh] = rot.dataset.forhold.split("/").map(Number);
        const forhold = fb / fh;
        const minBredde = Number(rot.dataset.minBredde);
        const skjema = rot.closest("form");
        const feltnavn = rot.dataset.felt; // «bilde», eventuelt med prefiks
        const prefiks = feltnavn.slice(0, feltnavn.length - "bilde".length);
        const filfelt = skjema.querySelector(`input[type="file"][name="${feltnavn}"]`);
        const felt = {};
        for (const navn of ["x", "y", "bredde", "hoyde"]) {
            felt[navn] = skjema.querySelector(`[name="${prefiks}utsnitt_${navn}"]`);
        }

        const bilde = rot.querySelector(".utsnitt-bilde");
        const flate = rot.querySelector(".utsnitt-flate");
        const ramme = rot.querySelector(".utsnitt-ramme");
        const feil = rot.querySelector(".utsnitt-feil");
        const status = rot.querySelector(".utsnitt-status");
        const lerreter = [...rot.querySelectorAll("canvas[data-visning]")];

        // Utsnittet i originalens piksler: venstre kant, øvre kant og bredde (høyden følger av formatet)
        let W = 0;
        let H = 0;
        let u = { x: 0, y: 0, b: 0 };
        let objektUrl = null;

        const hoyde = () => u.b / forhold;
        const maksBredde = () => Math.min(W, H * forhold);
        const minsteBredde = () => Math.min(maksBredde(), minBredde);

        function hold() {
            u.b = klem(u.b, minsteBredde(), maksBredde());
            u.x = klem(u.x, 0, W - u.b);
            u.y = klem(u.y, 0, H - hoyde());
        }

        function midtstill() {
            u.b = maksBredde();
            u.x = (W - u.b) / 2;
            u.y = (H - hoyde()) / 2;
        }

        function lesFelt() {
            const [x, y, b] = [felt.x, felt.y, felt.bredde].map((f) => parseFloat(f && f.value));
            if ([x, y, b].some(Number.isNaN)) return false;
            u = { x: (x / 100) * W, y: (y / 100) * H, b: (b / 100) * W };
            hold();
            return true;
        }

        function skrivFelt() {
            felt.x.value = ((u.x / W) * 100).toFixed(4);
            felt.y.value = ((u.y / H) * 100).toFixed(4);
            felt.bredde.value = ((u.b / W) * 100).toFixed(4);
            felt.hoyde.value = ((hoyde() / H) * 100).toFixed(4);
        }

        function tegn() {
            ramme.style.left = `${(u.x / W) * 100}%`;
            ramme.style.top = `${(u.y / H) * 100}%`;
            ramme.style.width = `${(u.b / W) * 100}%`;
            ramme.style.height = `${(hoyde() / H) * 100}%`;
            lerreter.forEach(tegnBanner);
            status.textContent =
                `Utsnitt ${Math.round(u.b)} × ${Math.round(hoyde())} piksler, ` +
                `${Math.round((u.x / W) * 100)} % fra venstre og ${Math.round((u.y / H) * 100)} % fra toppen.`;
        }

        // Banneret viser en smal stripe midt i utsnittet (se .hero-bilder i style.css)
        function tegnBanner(lerret) {
            const skjerm = SKJERMER[lerret.dataset.visning];
            const skjermForhold = skjerm.bredde / skjerm.hoyde;
            let breddeAndel = 1;
            let hoydeAndel;
            if (skjermForhold > forhold) {
                hoydeAndel = skjerm.banner / (skjerm.bredde / forhold);
            } else {
                breddeAndel = skjermForhold / forhold; // bildet beskjæres i sidene på smale skjermer
                hoydeAndel = skjerm.banner / skjerm.hoyde;
            }
            const sb = u.b * breddeAndel;
            const sh = hoyde() * hoydeAndel;
            const ctx = lerret.getContext("2d");
            ctx.drawImage(bilde, u.x + (u.b - sb) / 2, u.y + (hoyde() - sh) / 2, sb, sh, 0, 0, lerret.width, lerret.height);
            ctx.fillStyle = "rgba(0, 0, 0, 0.55)"; // samme slør som det ekte banneret
            ctx.fillRect(0, 0, lerret.width, lerret.height);
        }

        function oppdater() {
            hold();
            tegn();
            skrivFelt();
        }

        function last(kilde, nyttBilde) {
            bilde.onload = () => {
                W = bilde.naturalWidth;
                H = bilde.naturalHeight;
                rot.hidden = false;
                const forLite = W < minBredde || H < Math.round(minBredde / forhold);
                feil.hidden = !forLite;
                feil.textContent = forLite
                    ? `Bildet er for lite (${W} × ${H} piksler). Det må være minst ${minBredde} × ` +
                      `${Math.round(minBredde / forhold)} piksler for å bli skarpt på store skjermer.`
                    : "";
                if (nyttBilde || !lesFelt()) midtstill();
                oppdater();
            };
            bilde.onerror = () => { rot.hidden = true; }; // f.eks. HEIC i nettlesere som ikke kan vise det
            bilde.src = kilde;
        }

        filfelt.addEventListener("change", () => {
            const fil = filfelt.files && filfelt.files[0];
            if (!fil) return;
            if (objektUrl) URL.revokeObjectURL(objektUrl);
            objektUrl = URL.createObjectURL(fil);
            last(objektUrl, true);
        });
        if (rot.dataset.original) last(rot.dataset.original, false);

        // ---- Dra og skalere med mus og berøring --------------------------------

        let drag = null;

        ramme.addEventListener("pointerdown", (e) => {
            if (e.button !== 0) return;
            drag = {
                id: e.pointerId,
                start: { ...u },
                px: e.clientX,
                py: e.clientY,
                hjorne: e.target.dataset.hjorne || "",
                skala: W / flate.getBoundingClientRect().width, // skjermpiksler -> bildepiksler
            };
            ramme.setPointerCapture(e.pointerId);
            ramme.focus({ preventScroll: true });
            e.preventDefault();
        });

        ramme.addEventListener("pointermove", (e) => {
            if (!drag || e.pointerId !== drag.id) return;
            const dx = (e.clientX - drag.px) * drag.skala;
            const dy = (e.clientY - drag.py) * drag.skala;
            const s = drag.start;

            if (!drag.hjorne) {
                u = { x: s.x + dx, y: s.y + dy, b: s.b };
            } else {
                // Hjørnet på motsatt side ligger fast; bredden følger den største bevegelsen
                const venstre = drag.hjorne.includes("venstre");
                const oppe = drag.hjorne.includes("oppe");
                const fastX = venstre ? s.x + s.b : s.x;
                const fastY = oppe ? s.y + s.b / forhold : s.y;
                const fraX = s.b + (venstre ? -dx : dx);
                const fraY = (s.b / forhold + (oppe ? -dy : dy)) * forhold;
                let b = Math.abs(fraX - s.b) > Math.abs(fraY - s.b) ? fraX : fraY;
                const plass = Math.min(venstre ? fastX : W - fastX, (oppe ? fastY : H - fastY) * forhold);
                b = klem(b, minsteBredde(), Math.max(minsteBredde(), plass));
                u = { x: venstre ? fastX - b : fastX, y: oppe ? fastY - b / forhold : fastY, b };
            }
            oppdater();
        });

        const slipp = (e) => {
            if (drag && e.pointerId === drag.id) drag = null;
        };
        ramme.addEventListener("pointerup", slipp);
        ramme.addEventListener("pointercancel", slipp);

        // ---- Tastatur -----------------------------------------------------------

        ramme.addEventListener("keydown", (e) => {
            const steg = e.shiftKey ? 0.1 : 0.01; // 1 % (10 % med Shift) av bildet
            const retning = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
            if (retning) {
                u.x += retning[0] * steg * W;
                u.y += retning[1] * steg * H;
            } else if (["+", "=", "-", "−"].includes(e.key)) {
                const midtX = u.x + u.b / 2;
                const midtY = u.y + hoyde() / 2;
                u.b = klem(u.b * (e.key === "-" || e.key === "−" ? 0.95 : 1.05), minsteBredde(), maksBredde());
                u.x = midtX - u.b / 2;
                u.y = midtY - hoyde() / 2;
            } else {
                return;
            }
            e.preventDefault();
            oppdater();
        });
    }
})();
