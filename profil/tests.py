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

    def test_manus_tar_med_det_som_pagar(self):
        from .lyd import lag_manus

        manus = lag_manus(self.profil)
        self.assertIn("Jeg heter Ola Nordmann.", manus)
        self.assertIn("Jeg liker å kode.", manus)
        self.assertIn("studerer jeg Datateknologi ved NTNU", manus)
        self.assertIn("jobber jeg som assistent i Firma", manus)
        self.assertNotIn("Gammel jobb", manus)

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
        self.assertContains(response, "Logg inn")
        self.assertNotContains(response, "+ Legg til")
        self.assertNotContains(response, ">Rediger<")

    def test_knapper_for_innlogget(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, "+ Legg til", count=4)
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

    def test_ukjent_type_gir_404(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/rediger/hemmelig/ny/").status_code, 404)
