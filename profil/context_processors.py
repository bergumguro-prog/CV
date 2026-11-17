from django.conf import settings

from .models import UTSNITT_FORHOLD, Profil


def nettsted(request):
    """Gjør navnet og søkbarheten tilgjengelig i alle maler (sidetittel og meta-tagger)."""
    return {
        "nettsted_profil": Profil.objects.first(),
        "sokbar": settings.SOKBAR,
        # Formatet på forsidebildene, til CSS-en (f.eks. «16 / 9»)
        "utsnitt_forhold": f"{UTSNITT_FORHOLD[0]} / {UTSNITT_FORHOLD[1]}",
    }
