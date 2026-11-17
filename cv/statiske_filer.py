from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class StatiskeFiler(ManifestStaticFilesStorage):
    """CSS og JavaScript får innholdet sitt i filnavnet, f.eks. style.3f9a2c1b.css.

    Når en fil endres, får den et nytt navn, så nettlesere henter den nye utgaven
    i stedet for å bruke en gammel kopi. Navnene lages av «collectstatic».

    Er collectstatic ikke kjørt ennå (f.eks. i tester), brukes det vanlige
    filnavnet i stedet for at siden krasjer.
    """

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            return name
