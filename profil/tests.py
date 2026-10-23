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
