from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Erfaring, Ferdighet, Profil, Prosjekt, Utdanning


class ModellTester(TestCase):
    def test_str(self):
        self.assertEqual(str(Profil(navn="Ola Nordmann")), "Ola Nordmann")
        self.assertEqual(str(Erfaring(stilling="Utvikler", arbeidsgiver="Firma")), "Utvikler, Firma")
        self.assertEqual(str(Utdanning(studie="Informatikk", skole="UiO")), "Informatikk, UiO")
        self.assertEqual(str(Ferdighet(navn="Python")), "Python")
        self.assertEqual(str(Prosjekt(tittel="CV-side")), "CV-side")

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
        response = self.client.get(reverse("profil:forside"))
        self.assertContains(response, "Ola Nordmann")
        self.assertContains(response, "Utvikler, Firma")
        self.assertContains(response, "Django")

    def test_prosjektsiden_viser_prosjekter(self):
        Prosjekt.objects.create(tittel="CV-side", beskrivelse="Laget med Django", lenke="https://github.com")
        response = self.client.get(reverse("profil:prosjekter"))
        self.assertContains(response, "CV-side")
        self.assertContains(response, 'href="https://github.com"')
