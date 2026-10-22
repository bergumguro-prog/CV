from django.shortcuts import render

from .models import Erfaring, Ferdighet, Profil, Utdanning


def forside(request):
    return render(request, "profil/forside.html", {
        "profil": Profil.objects.first(),
        "erfaringer": Erfaring.objects.all(),
        "utdanninger": Utdanning.objects.all(),
        "ferdigheter": Ferdighet.objects.all(),
    })
