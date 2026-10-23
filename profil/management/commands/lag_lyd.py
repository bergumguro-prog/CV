from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from profil.lyd import lag_manus, les_opp
from profil.models import Profil


class Command(BaseCommand):
    help = "Lager «Lytt til CV-en»-lyden med ElevenLabs. Hopper over hvis manuset ikke har endret seg."

    def add_arguments(self, parser):
        parser.add_argument("--tving", action="store_true", help="Lag lyden på nytt selv om manuset er likt.")
        parser.add_argument("--vis", action="store_true", help="Vis bare manuset, uten å lage lyd.")

    def handle(self, *args, tving=False, vis=False, **options):
        profil = Profil.objects.first()
        if profil is None:
            raise CommandError("Legg inn en profil i admin først.")

        manus = lag_manus(profil)
        if vis:
            self.stdout.write(manus)
            return
        if "[FYLL INN" in manus:
            raise CommandError("Manuset inneholder fortsatt «[FYLL INN». Fyll ut teksten i admin først.")
        if profil.lyd and profil.lyd_manus == manus and not tving:
            self.stdout.write("Manuset er uendret, så lyden er allerede oppdatert.")
            return
        if not settings.ELEVENLABS_API_KEY or not settings.ELEVENLABS_VOICE_ID:
            raise CommandError("Sett ELEVENLABS_API_KEY og ELEVENLABS_VOICE_ID i .env.")

        self.stdout.write("Lager lyd med ElevenLabs …")
        lyd = les_opp(manus)
        if profil.lyd:
            profil.lyd.delete(save=False)
        profil.lyd.save("cv.mp3", ContentFile(lyd), save=False)
        profil.lyd_manus = manus
        profil.save()
        self.stdout.write(self.style.SUCCESS(f"Ferdig: {profil.lyd.url} ({len(lyd) // 1024} kB)"))
