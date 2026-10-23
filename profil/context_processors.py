from django.conf import settings

from .models import Profil


def nettsted(request):
    """Gjør navnet og søkbarheten tilgjengelig i alle maler (sidetittel og meta-tagger)."""
    return {
        "nettsted_profil": Profil.objects.first(),
        "sokbar": settings.SOKBAR,
    }
