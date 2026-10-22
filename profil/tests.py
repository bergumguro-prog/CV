import shutil
import tempfile
from datetime import date
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Erfaring, Ferdighet, Profil, Prosjekt, Utdanning, Verv


class ModellTester(TestCase):
    def test_str(self):
        self.assertEqual(str(Profil(navn="Ola Nordmann")), "Ola Nordmann")
        self.assertEqual(str(Erfaring(stilling="Utvikler", arbeidsgiver="Firma")), "Utvikler, Firma")
        self.assertEqual(str(Utdanning(studie="Informatikk", skole="UiO")), "Informatikk, UiO")
        self.assertEqual(str(Ferdighet(navn="Python")), "Python")
        self.assertEqual(str(Prosjekt(tittel="CV-side")), "CV-side")
        self.assertEqual(str(Verv(rolle="Leder", organisasjon="Abakus")), "Leder, Abakus")

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
