// Bildekarusellen øverst på forsiden.
// - Bytter bilde av seg selv hvert 6. sekund, med pause-knapp (WCAG 2.2.2)
// - Sveip, piltaster og prikker for å bytte manuelt
// - Pauser når karusellen er krympet til banner, eller fanen er skjult
// - Langsom zoom («Ken Burns») på bildet som vises, bare når karusellen er i full størrelse
// - Reserveløsning for scroll-effekten i nettlesere uten CSS scroll-drevne animasjoner
// - Forstørret profilbilde i en dialog (nederst i filen)
(() => {
    "use strict";

    const hero = document.querySelector(".hero");
    if (!hero) return;

    const INTERVALL = 6000;
    const OVERGANG = 1200; // overtoningen mellom bildene, samme som i style.css
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
    let vedToppen = true; // karusellen er i full størrelse (ikke begynt å krympe)
    let dialogApen = false; // profilbildet er forstørret; brukerens egen pause endres ikke

    // Zoomen varer like lenge som et bilde vises, pluss overtoningen ut
    hero.style.setProperty("--zoom-tid", `${INTERVALL + OVERGANG}ms`);

    // ---- Bytte bilde -----------------------------------------------------------

    function vis(indeks) {
        const forrige = aktiv;
        aktiv = (indeks + lysbilder.length) % lysbilder.length;
        if (aktiv !== forrige) startZoom(lysbilder[aktiv]);
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

    // ---- Langsom zoom -------------------------------------------------------------
    // Det nye bildet starter zoomen fra 1,0. Det forrige beholder sin zoom mens det
    // tones ut, så ingenting hopper. Selve animasjonen ligger i style.css.

    function startZoom(lysbilde) {
        const zoom = lysbilde.querySelector(".hero-zoom");
        if (!zoom) return;
        zoom.classList.remove("zoomer");
        void zoom.offsetWidth; // start animasjonen på nytt
        zoom.classList.add("zoomer");
    }

    function zoomSkalGa() {
        const karusellGar = lysbilder.length < 2 || (onskerAvspilling && !fokusInne && !pekerOver);
        return vedToppen && !document.hidden && !dialogApen && karusellGar;
    }

    function oppdaterZoom() {
        // Pause fryser zoomen der den er, uten å hoppe tilbake
        hero.classList.toggle("zoom-pause", !zoomSkalGa());
    }

    // ---- Automatisk avspilling --------------------------------------------------

    function skalSpille() {
        return onskerAvspilling && !samlet && !document.hidden && !fokusInne && !pekerOver && !dialogApen;
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
        oppdaterZoom();
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
            vedToppen = inngang.intersectionRatio >= 0.99; // har ikke begynt å scrolle
            hero.classList.toggle("samlet", samlet);
            hero.classList.toggle("halvveis", inngang.intersectionRatio < 0.5);
            oppdaterAvspilling();
        }, { threshold: [0, 0.5, 0.99, 1] }).observe(vakt);
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

    document.addEventListener("visibilitychange", oppdaterZoom);
    document.addEventListener("profilbilde:apnet", () => { dialogApen = true; oppdaterAvspilling(); });
    document.addEventListener("profilbilde:lukket", () => { dialogApen = false; oppdaterAvspilling(); });
    if (lysbilder.length) startZoom(lysbilder[aktiv]);
    oppdaterAvspilling();
})();

// Forstørret profilbilde.
// - Knappen rundt profilbildet åpner en <dialog> med en større, skarpere utgave
// - Bildet glir fra sin plass til midten med View Transitions der det støttes,
//   ellers tones det inn og skaleres litt. Bare toning ved «Reduser bevegelse»
// - Lukkes med Esc, klikk utenfor bildet eller ×. Fokus går tilbake til knappen
// - Karusellen og zoomen pauses mens bildet er åpent
(() => {
    "use strict";

    const dialog = document.querySelector(".profilbilde-dialog");
    if (!dialog) return;

    const stort = dialog.querySelector(".profilbilde-stor");
    const lukkKnapp = dialog.querySelector(".profilbilde-lukk");
    const roligBevegelse = window.matchMedia("(prefers-reduced-motion: reduce)");
    const NAVN = "profilbilde"; // view-transition-name

    let knapp = null; // knappen som åpnet dialogen
    let lukker = false;

    const kanGli = () => "startViewTransition" in document && !roligBevegelse.matches;
    const lillebilde = () => knapp && knapp.querySelector("img");

    // Hent det store bildet første gang, og vent til det er klart så overgangen ikke viser et tomt bilde
    async function lastStortBilde() {
        if (!stort.getAttribute("src")) stort.src = stort.dataset.src;
        try {
            await stort.decode();
        } catch {
            // Vis dialogen uansett; bildet kommer når det er lastet
        }
    }

    async function apne(fra) {
        if (dialog.open) return;
        knapp = fra;
        document.dispatchEvent(new CustomEvent("profilbilde:apnet"));
        await lastStortBilde();

        if (kanGli()) {
            dialog.dataset.overgang = "gli";
            lillebilde().style.viewTransitionName = NAVN;
            await document.startViewTransition(() => {
                lillebilde().style.viewTransitionName = "";
                stort.style.viewTransitionName = NAVN;
                dialog.showModal();
            }).finished;
            stort.style.viewTransitionName = "";
        } else {
            dialog.dataset.overgang = "ton";
            dialog.showModal();
        }
    }

    async function lukk() {
        if (!dialog.open || lukker) return;
        lukker = true;
        if (kanGli() && lillebilde()) {
            stort.style.viewTransitionName = NAVN;
            await document.startViewTransition(() => {
                stort.style.viewTransitionName = "";
                lillebilde().style.viewTransitionName = NAVN;
                dialog.close();
            }).finished;
            lillebilde().style.viewTransitionName = "";
        } else {
            // Spill ut-animasjonen i CSS, og lukk når den er ferdig
            dialog.classList.add("lukkes");
            await Promise.race([
                new Promise((ferdig) => dialog.addEventListener("animationend", ferdig, { once: true })),
                new Promise((ferdig) => setTimeout(ferdig, 400)),
            ]);
            dialog.classList.remove("lukkes");
            dialog.close();
        }
        lukker = false;
    }

    document.querySelectorAll(".profilbilde-knapp").forEach((k) => {
        k.addEventListener("click", () => apne(k));
        // Begynn å hente det store bildet allerede når musen er over eller knappen får fokus,
        // så overgangen kan starte med en gang ved klikk
        const forhandslast = () => { if (!stort.getAttribute("src")) stort.src = stort.dataset.src; };
        k.addEventListener("pointerenter", forhandslast, { once: true });
        k.addEventListener("focus", forhandslast, { once: true });
    });
    lukkKnapp.addEventListener("click", lukk);

    // Esc: vis lukke-animasjonen i stedet for å lukke brått
    dialog.addEventListener("cancel", (e) => {
        e.preventDefault();
        lukk();
    });

    // Klikk på det mørke området utenfor bildet (det treffer selve <dialog>-elementet)
    dialog.addEventListener("click", (e) => {
        if (e.target === dialog) lukk();
    });

    // Rydd opp uansett hvordan dialogen ble lukket. Fokus går automatisk tilbake til knappen.
    dialog.addEventListener("close", () => {
        lukker = false;
        dialog.classList.remove("lukkes");
        document.dispatchEvent(new CustomEvent("profilbilde:lukket"));
    });
})();
