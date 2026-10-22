from django.shortcuts import render

from .models import Erfaring, Ferdighet, Profil, Prosjekt, Utdanning


def forside(request):
    return render(request, "profil/forside.html", {
        "profil": Profil.objects.first(),
        "erfaringer": Erfaring.objects.all(),
        "utdanninger": Utdanning.objects.all(),
        "ferdigheter": Ferdighet.objects.all(),
    })


def om_meg(request):
    return render(request, "profil/om_meg.html", {"profil": Profil.objects.first()})


def prosjekter(request):
    return render(request, "profil/prosjekter.html", {"prosjekter": Prosjekt.objects.all()})


def kontakt(request):
    return render(request, "profil/kontakt.html", {"profil": Profil.objects.first()})
