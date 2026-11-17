// Bildekarusellen øverst på forsiden.
// - Bytter bilde av seg selv hvert 6. sekund, med pause-knapp (WCAG 2.2.2)
// - Sveip, piltaster og prikker for å bytte manuelt
// - Pauser når karusellen er krympet til banner, eller fanen er skjult
// - Reserveløsning for scroll-effekten i nettlesere uten CSS scroll-drevne animasjoner
(() => {
    "use strict";

    const hero = document.querySelector(".hero");
    if (!hero) return;

    const INTERVALL = 6000;
    const SVEIP_TERSKEL = 40; // piksler før et sveip teller

    const lysbilder = [...hero.querySelectorAll(".hero-bilde")];
    const prikker = [...hero.querySelectorAll(".hero-prikk")];
    const redigerLenker = [...hero.querySelectorAll(".hero-redigering [data-lysbilde]")];
    const kontroller = hero.querySelector(".hero-kontroller");
    const pauseKnapp = hero.querySelector(".hero-pause");
    const bilder = hero.querySelector(".hero-bilder");
    const vakt = document.querySelector(".hero-vakt");
    const roligBevegelse = window.matchMedia("(prefers-reduced-motion: reduce)");

    let aktiv = 0;
    let onskerAvspilling = lysbilder.length > 1 && !roligBevegelse.matches;
    let samlet = false;   // krympet til banner
    let fokusInne = false;
    let pekerOver = false;
    let tidtaker = null;

    // ---- Bytte bilde -----------------------------------------------------------

    function vis(indeks) {
        aktiv = (indeks + lysbilder.length) % lysbilder.length;
        lysbilder.forEach((bilde, i) => {
            const erAktiv = i === aktiv;
            bilde.hidden = false;
            bilde.classList.toggle("aktiv", erAktiv);
            bilde.inert = !erAktiv;
        });
        prikker.forEach((prikk, i) => {
            if (i === aktiv) prikk.setAttribute("aria-current", "true");
            else prikk.removeAttribute("aria-current");
        });
        redigerLenker.forEach((lenke, i) => { lenke.hidden = i !== aktiv; });
    }

    // ---- Automatisk avspilling --------------------------------------------------

    function skalSpille() {
        return onskerAvspilling && !samlet && !document.hidden && !fokusInne && !pekerOver;
    }

    function oppdaterAvspilling() {
        clearTimeout(tidtaker);
        tidtaker = null;
        if (skalSpille()) {
            tidtaker = setTimeout(() => { vis(aktiv + 1); oppdaterAvspilling(); }, INTERVALL);
        }
        if (pauseKnapp) {
            pauseKnapp.dataset.spiller = String(onskerAvspilling);
            pauseKnapp.setAttribute("aria-label", onskerAvspilling ? "Sett på pause" : "Spill av");
        }
        // Skjermlesere får beskjed om nytt bilde bare når det er brukeren som bytter
        bilder.setAttribute("aria-live", onskerAvspilling ? "off" : "polite");
    }

    function byttManuelt(indeks) {
        vis(indeks);
        oppdaterAvspilling(); // start 6-sekunders-telleren på nytt
    }

    if (lysbilder.length > 1) {
        kontroller.hidden = false;
        bilder.tabIndex = 0;

        prikker.forEach((prikk) => {
            prikk.addEventListener("click", () => byttManuelt(Number(prikk.dataset.lysbilde)));
        });

        pauseKnapp.addEventListener("click", () => {
            onskerAvspilling = !onskerAvspilling;
            oppdaterAvspilling();
        });

        // Piltaster når fokus er på bildene eller kontrollene
        hero.addEventListener("keydown", (e) => {
            if (!e.target.closest(".hero-bilder, .hero-kontroller")) return;
            if (e.key === "ArrowRight") { byttManuelt(aktiv + 1); e.preventDefault(); }
            if (e.key === "ArrowLeft") { byttManuelt(aktiv - 1); e.preventDefault(); }
        });

        // Sveip: vannrett bevegelse bytter bilde, loddrett scroller siden som vanlig
        let start = null;
        hero.addEventListener("pointerdown", (e) => {
            if (e.pointerType === "mouse" || e.target.closest("a, button")) return;
            start = { x: e.clientX, y: e.clientY };
        });
        hero.addEventListener("pointerup", (e) => {
            if (!start) return;
            const dx = e.clientX - start.x;
            const dy = e.clientY - start.y;
            start = null;
            if (Math.abs(dx) > SVEIP_TERSKEL && Math.abs(dx) > Math.abs(dy)) {
                byttManuelt(aktiv + (dx < 0 ? 1 : -1));
            }
        });
        hero.addEventListener("pointercancel", () => { start = null; });

        // Pause mens brukeren leser eller bruker tastaturet i karusellen
        hero.addEventListener("focusin", (e) => {
            fokusInne = !!e.target.closest(".hero-bilder, .hero-kontroller");
            oppdaterAvspilling();
        });
        hero.addEventListener("focusout", () => { fokusInne = false; oppdaterAvspilling(); });
        bilder.addEventListener("pointerenter", (e) => {
            if (e.pointerType === "mouse") { pekerOver = true; oppdaterAvspilling(); }
        });
        bilder.addEventListener("pointerleave", () => { pekerOver = false; oppdaterAvspilling(); });

        document.addEventListener("visibilitychange", oppdaterAvspilling);
        roligBevegelse.addEventListener("change", () => {
            if (roligBevegelse.matches) onskerAvspilling = false;
            oppdaterAvspilling();
        });

        // De andre bildene lastes først når siden ellers er ferdig
        const lastResten = () => vis(aktiv);
        if (document.readyState === "complete") lastResten();
        else window.addEventListener("load", lastResten, { once: true });
    }

    // ---- Krympet til banner? ----------------------------------------------------
    // «Vakten» er like høy som strekningen karusellen krymper over. Når den er ute av
    // syne, er karusellen et banner. Halvveis skjules teksten, så den ikke kan klikkes.

    if (vakt && "IntersectionObserver" in window) {
        new IntersectionObserver(([inngang]) => {
            samlet = !inngang.isIntersecting;
            hero.classList.toggle("samlet", samlet);
            hero.classList.toggle("halvveis", inngang.intersectionRatio < 0.5);
            oppdaterAvspilling();
        }, { threshold: [0, 0.5, 1] }).observe(vakt);
    }

    // ---- Reserveløsning for scroll-effekten -------------------------------------
    // Nettlesere med animation-timeline gjør alt i CSS. Andre (f.eks. Firefox) får
    // fremdriften fra 0 til 1 som en CSS-variabel, oppdatert én gang per bilde.

    if (!CSS.supports("animation-timeline: scroll()") && !roligBevegelse.matches) {
        hero.classList.add("js-fremdrift");
        let strekning = 1;
        let venter = false;

        const mal = () => { strekning = Math.max(1, hero.offsetHeight - hero.querySelector("nav").offsetHeight); };
        const tegn = () => {
            venter = false;
            const fremdrift = Math.min(1, Math.max(0, window.scrollY / strekning));
            hero.style.setProperty("--fremdrift", fremdrift.toFixed(4));
        };
        const planlegg = () => {
            if (!venter) { venter = true; requestAnimationFrame(tegn); }
        };

        mal();
        tegn();
        window.addEventListener("scroll", planlegg, { passive: true });
        window.addEventListener("resize", () => { mal(); planlegg(); }, { passive: true });
    }

    oppdaterAvspilling();
})();
