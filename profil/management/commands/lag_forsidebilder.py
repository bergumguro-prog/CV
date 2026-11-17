from django.core.management.base import BaseCommand

from profil.models import Forsidebilde, Profil


class Command(BaseCommand):
    help = ("Lager de beskårne forsidebildene på nytt der originalen eller utsnittet er endret, "
            "og den store utgaven av profilbildet hvis den mangler.")

    def handle(self, *args, **options):
        laget = 0
        for bilde in Forsidebilde.objects.all():
            for_ = bilde.generert_fra
            bilde.save()
            if bilde.generert_fra != for_:
                laget += 1
                self.stdout.write(f"Laget utsnitt for «{bilde}»")
        for profil in Profil.objects.exclude(bilde="").filter(bilde_stor=""):
            profil.save()
            self.stdout.write(f"Laget stor utgave av profilbildet til {profil}")
        self.stdout.write(self.style.SUCCESS(f"Ferdig: {laget} av {Forsidebilde.objects.count()} bilder ble laget på nytt."))
