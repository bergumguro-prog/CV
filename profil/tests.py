import shutil
import tempfile
from datetime import date
from io import BytesIO, StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Egenskap,
    Erfaring,
    ErfaringEgenskap,
    Fag,
    Ferdighet,
    Forsidebilde,
    Idrettshendelse,
    Idrettslag,
    Profil,
    Prosjekt,
    Utdanning,
    Verv,
    VervEgenskap,
)


class ModellTester(TestCase):
    def test_str(self):
        self.assertEqual(str(Profil(navn="Ola Nordmann")), "Ola Nordmann")
        self.assertEqual(str(Erfaring(stilling="Utvikler", arbeidsgiver="Firma")), "Utvikler, Firma")
        self.assertEqual(str(Utdanning(studie="Informatikk", skole="UiO")), "Informatikk, UiO")
        self.assertEqual(str(Ferdighet(navn="Python")), "Python")
        self.assertEqual(str(Prosjekt(tittel="CV-side")), "CV-side")
        self.assertEqual(str(Verv(rolle="Leder", organisasjon="Abakus")), "Leder, Abakus")
        self.assertEqual(str(Fag(emnekode="TDT4100", navn="OOP")), "TDT4100 OOP")
        self.assertEqual(str(Fag(navn="OOP")), "OOP")
        self.assertEqual(str(Idrettslag(idrett="Håndball", lag="NTNUI")), "Håndball, NTNUI")
        self.assertEqual(str(Idrettshendelse(navn="Oslo Maraton", resultat="3:45:12")), "Oslo Maraton – 3:45:12")
        self.assertEqual(str(Idrettshendelse(navn="Oslo Maraton")), "Oslo Maraton")

    def test_erfaring_nyeste_forst(self):
        Erfaring.objects.create(stilling="Gammel", arbeidsgiver="A", fra_dato=date(2020, 1, 1))
        Erfaring.objects.create(stilling="Ny", arbeidsgiver="B", fra_dato=date(2024, 1, 1))
        self.assertEqual([e.stilling for e in Erfaring.objects.all()], ["Ny", "Gammel"])


class SideTester(TestCase):
    sider = ["forside", "om_meg", "prosjekter", "kontakt"]

    def test_sidene_svarer_uten_innhold(self):
        for side in self.sider:
            with self.subTest(side=side):
                response = self.client.get(reverse(f"profil:{side}"))
                self.assertEqual(response.status_code, 200)

    def test_forsiden_viser_innhold(self):
        Profil.objects.create(navn="Ola Nordmann", tittel="Utvikler")
        Erfaring.objects.create(stilling="Utvikler", arbeidsgiver="Firma", fra_dato=date(2024, 1, 1))
        Ferdighet.objects.create(navn="Django")
        Verv.objects.create(rolle="Leder", organisasjon="Abakus", fra_dato=date(2026, 1, 1))
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, "Ola Nordmann")
        self.assertContains(response, "Utvikler, Firma")
        self.assertContains(response, "Django")
        self.assertContains(response, "Leder, Abakus")

    def test_vis_mer_bare_med_detaljer(self):
        Erfaring.objects.create(stilling="Uten", arbeidsgiver="A", fra_dato=date(2023, 1, 1))
        response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, 'class="mer"')

        Erfaring.objects.create(
            stilling="Med", arbeidsgiver="B", fra_dato=date(2024, 1, 1), detaljer="Ledet et team på seks."
        )
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, 'class="mer"', count=1)
        self.assertContains(response, "Ledet et team på seks.")

    def test_fag_under_utdanning(self):
        utdanning = Utdanning.objects.create(studie="Datateknologi", skole="NTNU", fra_dato=date(2025, 1, 1))
        Fag.objects.create(utdanning=utdanning, emnekode="TDT4100", navn="Objektorientert programmering",
                           beskrivelse="Java og testing.")
        Fag.objects.create(utdanning=utdanning, navn="Uten beskrivelse")
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, 'class="mer"', count=1)
        self.assertContains(response, '<summary><span>TDT4100 Objektorientert programmering</span><span class="vis-mer"></span></summary>', html=True)
        self.assertContains(response, "Java og testing.")
        self.assertContains(response, "Uten beskrivelse")

    def test_egenskaper_med_forklaring(self):
        ledelse = Egenskap.objects.create(navn="Ledelse")
        teamarbeid = Egenskap.objects.create(navn="Teamarbeid")
        jobb = Erfaring.objects.create(stilling="Medic", arbeidsgiver="Forsvaret", fra_dato=date(2024, 1, 1))
        verv = Verv.objects.create(rolle="Leder", organisasjon="Abakus", fra_dato=date(2026, 1, 1))
        ErfaringEgenskap.objects.create(erfaring=jobb, egenskap=teamarbeid)
        VervEgenskap.objects.create(verv=verv, egenskap=ledelse, forklaring="Ledet jubileumsstyret.")
        VervEgenskap.objects.create(verv=verv, egenskap=teamarbeid)

        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, 'class="mer"', count=2)
        self.assertContains(response, '<summary><span>Ledelse</span><span class="vis-mer"></span></summary>', html=True)
        self.assertContains(response, "Ledet jubileumsstyret.")
        self.assertNotContains(response, '<summary><span>Teamarbeid</span><span class="vis-mer"></span></summary>', html=True)

    def test_bare_overskrift_og_ar_utenfor_vis_mer(self):
        Erfaring.objects.create(stilling="Sommerjobb", arbeidsgiver="Firma", fra_dato=date(2023, 1, 1),
                                til_dato=date(2023, 1, 1), beskrivelse="Skjult tekst.")
        Erfaring.objects.create(stilling="Uten mer", arbeidsgiver="A", fra_dato=date(2020, 1, 1))
        response = self.client.get(reverse("profil:forside"))
        tekst = response.content.decode()
        self.assertContains(response, 'class="mer"', count=1)
        self.assertLess(tekst.index("Sommerjobb, Firma"), tekst.index('class="vis-mer"'))
        self.assertLess(tekst.index('class="vis-mer"'), tekst.index("Skjult tekst."))
        self.assertNotIn("2023 – 2023", tekst)
        self.assertInHTML('<span class="ar">2020 – nå</span>', tekst)

    def test_idrett_vises(self):
        response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, 'id="idrett"')

        Idrettslag.objects.create(idrett="Håndball", lag="NTNUI D2", rolle="Spiller", fra_dato=date(2025, 1, 1))
        Idrettshendelse.objects.create(navn="Oslo Maraton", dato=date(2026, 9, 20), resultat="3:45:12")
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, "Håndball, NTNUI D2")
        self.assertContains(response, "Spiller")
        self.assertContains(response, "Oslo Maraton – 3:45:12")
        self.assertInHTML('<span class="ar">2025 – nå</span>', response.content.decode())
        self.assertInHTML('<span class="ar">2026</span>', response.content.decode())

    def test_prosjektsiden_viser_prosjekter(self):
        Prosjekt.objects.create(tittel="CV-side", beskrivelse="Laget med Django", lenke="https://github.com")
        response = self.client.get(reverse("profil:prosjekter"))
        self.assertContains(response, "CV-side")
        self.assertContains(response, 'href="https://github.com"')


class ProfilbildeTester(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)

    def test_forsiden_viser_profilbilde(self):
        from PIL import Image

        fil = BytesIO()
        Image.new("RGB", (10, 10)).save(fil, "PNG")
        with override_settings(MEDIA_ROOT=self.media):
            Profil.objects.create(
                navn="Ola Nordmann",
                bilde=SimpleUploadedFile("ola.png", fil.getvalue(), content_type="image/png"),
            )
            response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, '<img src="/media/profil/ola')


class LydTester(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        self.profil = Profil.objects.create(navn="Ola Nordmann", tittel="Student", om_meg="Jeg liker å kode.")
        Utdanning.objects.create(studie="Datateknologi", skole="NTNU", fra_dato=date(2025, 1, 1))
        Erfaring.objects.create(stilling="Assistent", arbeidsgiver="Firma", fra_dato=date(2025, 1, 1))
        Erfaring.objects.create(stilling="Gammel jobb", arbeidsgiver="Før", fra_dato=date(2020, 1, 1),
                                til_dato=date(2021, 1, 1))

    def test_manus_er_hilsen_og_om_meg(self):
        from .lyd import lag_manus

        manus = lag_manus(self.profil)
        self.assertTrue(manus.startswith("Hei! Jeg heter Ola Nordmann.\n\nJeg liker å kode."))
        self.assertNotIn("Assistent", manus)

    def test_kommandoen_lager_lyd_bare_nar_manus_endres(self):
        from unittest.mock import patch

        from django.core.management import call_command

        with override_settings(MEDIA_ROOT=self.media, ELEVENLABS_API_KEY="nokkel", ELEVENLABS_VOICE_ID="stemme"), \
                patch("profil.management.commands.lag_lyd.les_opp", return_value=b"mp3") as les_opp:
            call_command("lag_lyd", stdout=StringIO())
            call_command("lag_lyd", stdout=StringIO())
            self.assertEqual(les_opp.call_count, 1)

            self.profil.refresh_from_db()
            self.assertIn("Ola Nordmann", self.profil.lyd_manus)
            response = self.client.get(reverse("profil:forside"))
            self.assertContains(response, "<audio")

            self.profil.om_meg = "Ny tekst."
            self.profil.save()
            call_command("lag_lyd", stdout=StringIO())
            self.assertEqual(les_opp.call_count, 2)

    def test_kommandoen_stopper_ved_fyll_inn(self):
        from django.core.management import CommandError, call_command

        self.profil.om_meg = "[FYLL INN: noe om meg]"
        self.profil.save()
        with self.assertRaises(CommandError):
            call_command("lag_lyd", stdout=StringIO())

    def test_lesbar_feilmelding_fra_elevenlabs(self):
        import urllib.error
        from unittest.mock import patch

        from django.core.management import CommandError, call_command

        svar = BytesIO(b'{"detail": {"message": "Free users cannot use library voices via the API."}}')
        feil = urllib.error.HTTPError("url", 402, "Payment Required", {}, svar)
        with override_settings(ELEVENLABS_API_KEY="nokkel", ELEVENLABS_VOICE_ID="stemme"), \
                patch("profil.management.commands.lag_lyd.les_opp", side_effect=feil):
            with self.assertRaisesMessage(CommandError, "ElevenLabs svarte 402: Free users cannot use library voices"):
                call_command("lag_lyd", stdout=StringIO())

    def test_ingen_avspiller_uten_lyd(self):
        response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, "<audio")


class RedigeringTester(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.admin = User.objects.create_superuser("guro", "guro@example.com", "passord")
        self.utdanning = Utdanning.objects.create(studie="Datateknologi", skole="NTNU", fra_dato=date(2025, 1, 1))

    def formset(self, prefix, *rader):
        data = {f"{prefix}-TOTAL_FORMS": str(len(rader)), f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-MIN_NUM_FORMS": "0", f"{prefix}-MAX_NUM_FORMS": "1000"}
        for i, rad in enumerate(rader):
            data.update({f"{prefix}-{i}-{felt}": verdi for felt, verdi in rad.items()})
        return data

    def test_bare_innloggede_kan_redigere(self):
        response = self.client.get(reverse("profil:ny", args=["erfaring"]))
        self.assertRedirects(response, reverse("profil:logg_inn") + "?next=/rediger/erfaring/ny/")

        response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, "Logg inn")
        self.assertNotContains(response, "+ Legg til")
        self.assertNotContains(response, ">Rediger<")

    def test_knapper_for_innlogget(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, "+ Legg til", count=6)
        self.assertContains(response, reverse("profil:rediger", args=["utdanning", self.utdanning.pk]))
        self.assertContains(response, "Logg ut")

    def test_legg_til_erfaring_med_ny_egenskap(self):
        self.client.force_login(self.admin)
        data = {"stilling": "Utvikler", "arbeidsgiver": "TellMe", "fra_dato": "2026-11-01", "til_dato": "",
                "beskrivelse": "", "detaljer": ""}
        data |= self.formset("egenskaper", {"navn": "Ledelse", "forklaring": "Ledet arbeidet."})
        response = self.client.post(reverse("profil:ny", args=["erfaring"]), data)
        self.assertRedirects(response, reverse("profil:forside") + "#erfaring")

        erfaring = Erfaring.objects.get(arbeidsgiver="TellMe")
        kobling = erfaring.egenskaper.get()
        self.assertEqual((kobling.egenskap.navn, kobling.forklaring), ("Ledelse", "Ledet arbeidet."))

    def test_gjenbruker_egenskap_uansett_store_bokstaver(self):
        Egenskap.objects.create(navn="Teamarbeid")
        self.client.force_login(self.admin)
        data = {"studie": "Datateknologi", "skole": "NTNU", "fra_dato": "2025-01-01", "til_dato": "",
                "beskrivelse": "", "detaljer": ""}
        data |= self.formset("fag", {"emnekode": "TDT4100", "navn": "OOP", "beskrivelse": "Java."})
        data |= self.formset("egenskaper", {"navn": "teamarbeid", "forklaring": ""})
        self.client.post(reverse("profil:rediger", args=["utdanning", self.utdanning.pk]), data)

        self.assertEqual(Egenskap.objects.count(), 1)
        self.assertEqual(self.utdanning.fag.get().emnekode, "TDT4100")

    def test_samme_egenskap_to_ganger_gir_feilmelding(self):
        self.client.force_login(self.admin)
        data = {"rolle": "Leder", "organisasjon": "Abakus", "fra_dato": "2026-01-01", "til_dato": "",
                "beskrivelse": "", "detaljer": ""}
        data |= self.formset("egenskaper", {"navn": "Ledelse", "forklaring": ""}, {"navn": "ledelse", "forklaring": ""})
        response = self.client.post(reverse("profil:ny", args=["verv"]), data)
        self.assertContains(response, "Samme egenskap er lagt inn to ganger.")
        self.assertFalse(Verv.objects.exists())

    def test_slett_etter_bekreftelse(self):
        self.client.force_login(self.admin)
        url = reverse("profil:slett", args=["utdanning", self.utdanning.pk])
        self.assertContains(self.client.get(url), "Ja, slett")
        self.client.post(url)
        self.assertFalse(Utdanning.objects.exists())

    def test_pagar_na_fjerner_sluttdato(self):
        verv = Verv.objects.create(rolle="Leder", organisasjon="Abakus", fra_dato=date(2026, 1, 1),
                                   til_dato=date(2027, 1, 1))
        self.client.force_login(self.admin)
        data = {"rolle": "Leder", "organisasjon": "Abakus", "fra_dato": "2026-01-01", "til_dato": "2027-01-01",
                "pagar": "on", "beskrivelse": "", "detaljer": ""}
        data |= self.formset("egenskaper")
        self.client.post(reverse("profil:rediger", args=["verv", verv.pk]), data)
        verv.refresh_from_db()
        self.assertIsNone(verv.til_dato)

        response = self.client.get(reverse("profil:rediger", args=["verv", verv.pk]))
        self.assertContains(response, 'name="pagar" id="id_pagar" checked')

    def test_pagar_na_med_ugyldig_dato(self):
        self.client.force_login(self.admin)
        data = {"rolle": "Leder", "organisasjon": "Abakus", "fra_dato": "2026-01-01", "til_dato": "ugyldig",
                "pagar": "on", "beskrivelse": "", "detaljer": ""}
        data |= self.formset("egenskaper")
        self.client.post(reverse("profil:ny", args=["verv"]), data)
        self.assertIsNone(Verv.objects.get().til_dato)

    def test_legg_til_maraton_med_egenskap(self):
        self.client.force_login(self.admin)
        data = {"navn": "Oslo Maraton", "dato": "2026-09-20", "resultat": "3:45:12", "beskrivelse": ""}
        data |= self.formset("egenskaper", {"navn": "Utholdenhet", "forklaring": "Trente i fire måneder."})
        response = self.client.post(reverse("profil:ny", args=["idrettshendelse"]), data)
        self.assertRedirects(response, reverse("profil:forside") + "#idrettshendelse")
        hendelse = Idrettshendelse.objects.get()
        self.assertEqual(hendelse.egenskaper.get().forklaring, "Trente i fire måneder.")

    def test_ukjent_type_gir_404(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/rediger/hemmelig/ny/").status_code, 404)


class InnloggingTester(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("guro", "guro@example.com", "riktig-passord")
        self.url = reverse("profil:logg_inn")

    def logg_inn(self, passord, ip="10.0.0.1"):
        return self.client.post(self.url, {"username": "guro", "password": passord}, HTTP_X_REAL_IP=ip)

    def test_innlogging_virker(self):
        response = self.logg_inn("riktig-passord")
        self.assertRedirects(response, reverse("profil:forside"))

    def test_sperret_etter_fem_feilforsok(self):
        for _ in range(5):
            self.logg_inn("feil")
        response = self.logg_inn("riktig-passord")
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Midlertidig sperret", status_code=429)

    def test_sperren_gjelder_bare_samme_ip(self):
        for _ in range(5):
            self.logg_inn("feil", ip="10.0.0.1")
        response = self.logg_inn("riktig-passord", ip="10.0.0.2")
        self.assertRedirects(response, reverse("profil:forside"))


class TittelOgSokbarhetTester(TestCase):
    def test_navnet_i_tittelen(self):
        response = self.client.get(reverse("profil:om_meg"))
        self.assertContains(response, "<title>Om meg</title>", html=True)

        Profil.objects.create(navn="Ola Nordmann", om_meg="Jeg liker å kode.")
        response = self.client.get(reverse("profil:om_meg"))
        self.assertContains(response, "<title>Om meg – Ola Nordmann</title>", html=True)
        self.assertContains(response, '<meta name="description" content="Jeg liker å kode.">', html=True)

    def test_skjult_for_sokemotorer_som_standard(self):
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">', html=True)

        with override_settings(SOKBAR=True):
            response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, 'name="robots"')


def lag_bilde(bredde, hoyde, navn="bilde.png", format="PNG", **lagre):
    from PIL import Image

    fil = BytesIO()
    Image.new("RGB", (bredde, hoyde), (200, 120, 60)).save(fil, format, **lagre)
    return SimpleUploadedFile(navn, fil.getvalue(), content_type=f"image/{format.lower()}")


class ForsidebildeOppsett(TestCase):
    """Felles oppsett: opplastede filer havner i en midlertidig mappe."""

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        innstillinger = override_settings(MEDIA_ROOT=self.media)
        innstillinger.enable()
        self.addCleanup(innstillinger.disable)

    def nytt_bilde(self, **felt):
        felt.setdefault("bilde", lag_bilde(3000, 1500))
        felt.setdefault("alt_tekst", "Utsikt over fjellet")
        return Forsidebilde.objects.create(**felt)


def lag_todelt_bilde(bredde, hoyde):
    """Rød venstre halvdel og blå høyre halvdel, for å sjekke hvilket utsnitt som ble brukt."""
    from PIL import Image

    bilde = Image.new("RGB", (bredde, hoyde), (255, 0, 0))
    bilde.paste((0, 0, 255), (bredde // 2, 0, bredde, hoyde))
    fil = BytesIO()
    bilde.save(fil, "PNG")
    return SimpleUploadedFile("todelt.png", fil.getvalue(), content_type="image/png")


class ForsidebildeModellTester(ForsidebildeOppsett):
    def storrelse(self, fil):
        from PIL import Image

        with Image.open(fil.path) as bilde:
            return bilde.format, bilde.size

    def test_str_og_rekkefolge(self):
        andre = self.nytt_bilde(alt_tekst="Andre", rekkefolge=2)
        forste = self.nytt_bilde(alt_tekst="Første", rekkefolge=1)
        self.assertEqual(str(forste), "Første")
        self.assertEqual(list(Forsidebilde.objects.all()), [forste, andre])

    def test_originalen_lagres_uendret(self):
        opplastet = lag_bilde(3000, 1500)
        innhold = opplastet.read()
        opplastet.seek(0)
        bilde = self.nytt_bilde(bilde=opplastet)
        with open(bilde.bilde.path, "rb") as fil:
            self.assertEqual(fil.read(), innhold)
        self.assertEqual((bilde.original_bredde, bilde.original_hoyde), (3000, 1500))

    def test_liggende_bilde_far_midtstilt_utsnitt_i_to_storrelser(self):
        bilde = self.nytt_bilde(bilde=lag_bilde(3000, 1500))
        # Største 16:9-utsnitt: 2667 × 1500 piksler midt i bildet
        self.assertAlmostEqual(bilde.utsnitt_bredde, 2666.667 / 3000 * 100, places=2)
        self.assertAlmostEqual(bilde.utsnitt_x, (3000 - 2666.667) / 2 / 3000 * 100, places=2)
        self.assertEqual((bilde.utsnitt_y, bilde.utsnitt_hoyde), (0, 100))
        self.assertEqual(self.storrelse(bilde.bilde_stor), ("WEBP", (2400, 1350)))
        self.assertEqual(self.storrelse(bilde.bilde_liten), ("WEBP", (1200, 675)))
        self.assertEqual((bilde.bredde, bilde.hoyde), (2400, 1350))
        self.assertEqual(bilde.srcset, f"{bilde.bilde_liten.url} 1200w, {bilde.bilde_stor.url} 2400w")
        self.assertEqual(bilde.vis_url, bilde.bilde_stor.url)

    def test_staende_bilde(self):
        bilde = self.nytt_bilde(bilde=lag_bilde(2000, 3000))
        self.assertEqual(self.storrelse(bilde.bilde_stor), ("WEBP", (2000, 1125)))  # aldri forstørret
        self.assertEqual(self.storrelse(bilde.bilde_liten), ("WEBP", (1200, 675)))
        self.assertAlmostEqual(bilde.utsnitt_y, (3000 - 1125) / 2 / 3000 * 100, places=3)

    def test_mobilbilde_snus_riktig_vei_for_beskjaering(self):
        from PIL import Image

        exif = Image.Exif()
        exif[0x0112] = 6  # «roter 90°», slik mange mobilkameraer lagrer bilder
        bilde = self.nytt_bilde(bilde=lag_bilde(3000, 2000, "mobil.jpg", "JPEG", exif=exif))
        self.assertEqual((bilde.original_bredde, bilde.original_hoyde), (2000, 3000))
        self.assertEqual(self.storrelse(bilde.bilde_stor), ("WEBP", (2000, 1125)))

    def test_det_valgte_utsnittet_brukes(self):
        from PIL import Image

        # Høyre halvdel (blå) av et 3200 × 1800-bilde er nøyaktig 16:9
        bilde = self.nytt_bilde(bilde=lag_todelt_bilde(3200, 1800),
                                utsnitt_x=50, utsnitt_y=25, utsnitt_bredde=50, utsnitt_hoyde=50)
        with Image.open(bilde.bilde_stor.path) as utsnitt:
            self.assertEqual(utsnitt.size, (1600, 900))
            for punkt in [(5, 5), (800, 450), (1590, 890)]:
                rod, _, bla = utsnitt.convert("RGB").getpixel(punkt)
                self.assertGreater(bla, 200)
                self.assertLess(rod, 60)

    def test_lages_bare_pa_nytt_nar_noe_endres(self):
        import os

        bilde = self.nytt_bilde()
        forste = (bilde.bilde_stor.name, bilde.bilde_liten.name, bilde.generert_fra)

        bilde.alt_tekst = "Ny tekst"
        bilde.save()
        Forsidebilde.objects.get().save()
        bilde.refresh_from_db()
        self.assertEqual((bilde.bilde_stor.name, bilde.bilde_liten.name, bilde.generert_fra), forste)

        bilde.utsnitt_x = 0
        bilde.save()
        self.assertNotEqual(bilde.bilde_stor.name, forste[0])
        self.assertTrue(os.path.exists(bilde.bilde_stor.path))
        for gammel in forste[:2]:
            self.assertFalse(os.path.exists(os.path.join(self.media, gammel)))

    def test_gamle_filer_fjernes_nar_bildet_byttes(self):
        import os

        bilde = self.nytt_bilde()
        gamle = [bilde.bilde.path, bilde.bilde_stor.path, bilde.bilde_liten.path]
        bilde.bilde = lag_bilde(1600, 900, "nytt.png")
        bilde.utsnitt_x = bilde.utsnitt_y = bilde.utsnitt_bredde = bilde.utsnitt_hoyde = None
        bilde.save()
        self.assertFalse(any(os.path.exists(f) for f in gamle))
        self.assertTrue(all(os.path.exists(f.path) for f in (bilde.bilde, bilde.bilde_stor, bilde.bilde_liten)))
        self.assertEqual((bilde.bredde, bilde.hoyde), (1600, 900))

    def test_alle_filene_slettes_med_bildet(self):
        import os

        bilde = self.nytt_bilde()
        filer = [bilde.bilde.path, bilde.bilde_stor.path, bilde.bilde_liten.path]
        bilde.delete()
        self.assertFalse(any(os.path.exists(f) for f in filer))

    def test_kommandoen_lager_manglende_utsnitt(self):
        bilde = self.nytt_bilde()
        Forsidebilde.objects.update(bilde_stor="", bilde_liten="", generert_fra="")
        bilde.refresh_from_db()
        self.assertEqual(bilde.vis_url, bilde.bilde.url)  # originalen brukes i mellomtiden

        from django.core.management import call_command

        call_command("lag_forsidebilder", stdout=StringIO())
        bilde.refresh_from_db()
        self.assertTrue(bilde.bilde_stor)
        self.assertEqual(bilde.vis_url, bilde.bilde_stor.url)


class UtsnittValideringTester(ForsidebildeOppsett):
    def skjema(self, fil=None, instance=None, **utsnitt):
        from .forms import ForsidebildeSkjema

        data = {"alt_tekst": "Fjellet", "bildetekst": "", "rekkefolge": "0", "aktiv": "on"}
        data |= {f"utsnitt_{navn}": str(verdi) for navn, verdi in utsnitt.items()}
        filer = {"bilde": fil} if fil else {}
        return ForsidebildeSkjema(data, filer, instance=instance)

    def feil(self, skjema):
        self.assertFalse(skjema.is_valid())
        return " ".join(str(f) for f in skjema.errors.values())

    def test_uten_utsnitt_brukes_midten(self):
        skjema = self.skjema(lag_bilde(3000, 1500))
        self.assertTrue(skjema.is_valid(), skjema.errors)
        bilde = skjema.save()
        self.assertEqual((bilde.utsnitt_y, bilde.utsnitt_hoyde), (0, 100))

    def test_gyldig_utsnitt(self):
        skjema = self.skjema(lag_bilde(3200, 1800), x=10, y=10, bredde=50, hoyde=50)
        self.assertTrue(skjema.is_valid(), skjema.errors)

    def test_for_lite_bilde(self):
        self.assertIn("Bildet er for lite (800 × 450 piksler). Det må være minst 1200 × 675 piksler",
                      self.feil(self.skjema(lag_bilde(800, 450))))

    def test_ikke_et_bilde(self):
        fil = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 ikke et bilde", content_type="application/pdf")
        self.assertIn("bilde", self.feil(self.skjema(fil)).lower())

    def test_verdier_utenfor_0_til_100(self):
        self.feil(self.skjema(lag_bilde(3200, 1800), x=-5, y=0, bredde=50, hoyde=50))
        self.feil(self.skjema(lag_bilde(3200, 1800), x=0, y=0, bredde=150, hoyde=50))

    def test_utsnitt_utenfor_bildet(self):
        self.assertIn("utenfor bildet", self.feil(self.skjema(lag_bilde(3200, 1800), x=60, y=0, bredde=50, hoyde=50)))

    def test_feil_format(self):
        # 50 % × 80 % av et 16:9-bilde er ikke 16:9
        self.assertIn("16:9", self.feil(self.skjema(lag_bilde(3200, 1800), x=0, y=0, bredde=50, hoyde=80)))

    def test_litt_avrunding_er_greit(self):
        skjema = self.skjema(lag_bilde(3200, 1800), x=10, y=10, bredde=50.3, hoyde=50)
        self.assertTrue(skjema.is_valid(), skjema.errors)

    def test_for_lite_utsnitt(self):
        # 20 % av 3200 piksler = 640 piksler bredt
        self.assertIn("Utsnittet er for lite", self.feil(self.skjema(lag_bilde(3200, 1800), x=0, y=0, bredde=20, hoyde=20)))

    def test_nytt_bilde_uten_nytt_utsnitt_midtstilles(self):
        bilde = self.nytt_bilde(bilde=lag_bilde(3200, 1800), utsnitt_x=0, utsnitt_y=0, utsnitt_bredde=50, utsnitt_hoyde=50)
        # Samme utsnittsverdier sendes med (som uten JavaScript), men bildet er nytt og stående
        skjema = self.skjema(lag_bilde(2000, 3000), instance=bilde, x=0, y=0, bredde=50, hoyde=50)
        self.assertTrue(skjema.is_valid(), skjema.errors)
        bilde = skjema.save()
        self.assertEqual((bilde.utsnitt_x, bilde.utsnitt_bredde), (0, 100))

    def test_utsnitt_endres_uten_nytt_bilde(self):
        bilde = self.nytt_bilde(bilde=lag_bilde(3200, 1800))
        skjema = self.skjema(instance=bilde, x=50, y=50, bredde=50, hoyde=50)
        self.assertTrue(skjema.is_valid(), skjema.errors)
        self.assertEqual(skjema.save().utsnitt_x, 50)


class ForsidebildeVisningTester(ForsidebildeOppsett):
    def setUp(self):
        super().setUp()
        Profil.objects.create(navn="Ola Nordmann", tittel="Utvikler")

    def test_uten_bilder_er_forsiden_som_for(self):
        response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, 'class="hero"')
        self.assertNotContains(response, "forside.js")
        self.assertContains(response, '<div class="intro">')
        self.assertContains(response, "<h1>Ola Nordmann</h1>", html=True)

    def test_med_bilder_vises_karusellen(self):
        self.nytt_bilde(alt_tekst="Første bilde", bildetekst="Jotunheimen", rekkefolge=1)
        self.nytt_bilde(alt_tekst="Andre bilde", rekkefolge=2)
        self.nytt_bilde(alt_tekst="Skjult bilde", aktiv=False)
        response = self.client.get(reverse("profil:forside"))
        tekst = response.content.decode()

        self.assertContains(response, 'class="hero"')
        self.assertContains(response, 'src="/static/profil/forside.js" defer')
        self.assertContains(response, "<h1>Ola Nordmann</h1>", count=1, html=True)
        self.assertNotContains(response, '<div class="intro">')
        self.assertContains(response, "Jotunheimen")
        self.assertNotContains(response, "Skjult bilde")
        self.assertContains(response, 'sizes="100vw"', count=2)
        # Første bilde lastes med en gang, resten senere
        self.assertLess(tekst.index("Første bilde"), tekst.index("Andre bilde"))
        self.assertIn('alt="Første bilde" decoding="async" fetchpriority="high"', tekst)
        self.assertIn('alt="Andre bilde" decoding="async" loading="lazy"', tekst)
        # Prikker og pause-knapp når det er mer enn ett bilde
        self.assertContains(response, 'class="hero-prikk"', count=2)
        self.assertContains(response, 'class="hero-pause"')

    def test_ett_bilde_har_ingen_prikker(self):
        self.nytt_bilde()
        response = self.client.get(reverse("profil:forside"))
        self.assertNotContains(response, "hero-kontroller")

    def test_antall_sporringer_avhenger_ikke_av_antall_bilder(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self.nytt_bilde()
        with CaptureQueriesContext(connection) as ett_bilde:
            self.client.get(reverse("profil:forside"))
        self.nytt_bilde()
        self.nytt_bilde()
        with CaptureQueriesContext(connection) as tre_bilder:
            self.client.get(reverse("profil:forside"))
        self.assertEqual(len(ett_bilde), len(tre_bilder))


class ForsidebildeRedigeringTester(ForsidebildeOppsett):
    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import User

        self.admin = User.objects.create_superuser("guro", "guro@example.com", "passord")
        self.vanlig = User.objects.create_user("besokende", "b@example.com", "passord")
        self.profil = Profil.objects.create(navn="Ola Nordmann")

    def data(self, **felt):
        return {"bilde": lag_bilde(1600, 900), "alt_tekst": "Fjellet", "bildetekst": "", "rekkefolge": "0",
                "aktiv": "on"} | felt

    def test_bare_ansatte_kan_legge_til_og_redigere(self):
        bilde = self.nytt_bilde()
        sider = [reverse("profil:ny", args=["forsidebilde"]),
                 reverse("profil:rediger", args=["forsidebilde", bilde.pk]),
                 reverse("profil:slett", args=["forsidebilde", bilde.pk])]
        for bruker in (None, self.vanlig):
            if bruker:
                self.client.force_login(bruker)
            for url in sider:
                with self.subTest(bruker=bruker, url=url):
                    response = self.client.get(url)
                    self.assertRedirects(response, reverse("profil:logg_inn") + f"?next={url}")
            self.client.post(sider[0], self.data(alt_tekst="Inntrenger"))
            self.client.post(sider[2])
        self.assertEqual(list(Forsidebilde.objects.values_list("alt_tekst", flat=True)), ["Utsikt over fjellet"])

    def test_ansatt_legger_til_bilde(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("profil:ny", args=["forsidebilde"]), self.data())
        self.assertRedirects(response, reverse("profil:forside") + "#forsidebilde")
        bilde = Forsidebilde.objects.get()
        self.assertEqual((bilde.alt_tekst, bilde.bredde, bilde.aktiv), ("Fjellet", 1600, True))

    def test_alt_tekst_er_pakrevd(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("profil:ny", args=["forsidebilde"]), self.data(alt_tekst=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Forsidebilde.objects.exists())

    def test_ansatt_sletter_bilde(self):
        bilde = self.nytt_bilde()
        self.client.force_login(self.admin)
        self.client.post(reverse("profil:slett", args=["forsidebilde", bilde.pk]))
        self.assertFalse(Forsidebilde.objects.exists())

    def test_redigeringsknapper_bare_for_ansatte(self):
        bilde = self.nytt_bilde()
        rediger = reverse("profil:rediger", args=["forsidebilde", bilde.pk])
        ny = reverse("profil:ny", args=["forsidebilde"])

        for bruker in (None, self.vanlig):
            if bruker:
                self.client.force_login(bruker)
            response = self.client.get(reverse("profil:forside"))
            self.assertNotContains(response, rediger)
            self.assertNotContains(response, ny)
            self.assertNotContains(response, "hero-redigering")

        self.client.force_login(self.admin)
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, rediger)
        self.assertContains(response, ny)

    def test_redigeringssiden_har_beskjaeringsverktoy(self):
        bilde = self.nytt_bilde()
        self.client.force_login(self.admin)
        for url in (reverse("profil:rediger", args=["forsidebilde", bilde.pk]),
                    reverse("admin:profil_forsidebilde_change", args=[bilde.pk])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'class="utsnitt"')
                self.assertContains(response, f'data-original="{bilde.bilde.url}"')
                self.assertContains(response, 'data-forhold="16/9"')
                self.assertContains(response, "profil/utsnitt.js")
                self.assertContains(response, 'type="hidden" name="utsnitt_x"')
                self.assertNotContains(response, "bilde-clear")  # bildet er påkrevd, kan ikke fjernes

    def test_ansatt_endrer_utsnitt(self):
        bilde = self.nytt_bilde(bilde=lag_bilde(3200, 1800))
        self.client.force_login(self.admin)
        data = {"alt_tekst": "Fjellet", "bildetekst": "", "rekkefolge": "0", "aktiv": "on",
                "utsnitt_x": "50", "utsnitt_y": "25", "utsnitt_bredde": "50", "utsnitt_hoyde": "50"}
        response = self.client.post(reverse("profil:rediger", args=["forsidebilde", bilde.pk]), data)
        self.assertRedirects(response, reverse("profil:forside") + "#forsidebilde")
        bilde.refresh_from_db()
        self.assertEqual((bilde.utsnitt_x, bilde.bredde, bilde.hoyde), (50, 1600, 900))

    def test_legg_til_forsidebilde_uten_karusell(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, reverse("profil:ny", args=["forsidebilde"]))
