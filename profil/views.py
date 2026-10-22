from django.shortcuts import render

from .models import Erfaring, Ferdighet, Profil, Prosjekt, Utdanning, Verv


def forside(request):
    return render(request, "profil/forside.html", {
        "profil": Profil.objects.first(),
        "erfaringer": Erfaring.objects.prefetch_related("egenskaper__egenskap"),
        "verv": Verv.objects.prefetch_related("egenskaper__egenskap"),
        "utdanninger": Utdanning.objects.prefetch_related("fag", "egenskaper__egenskap"),
        "ferdigheter": Ferdighet.objects.all(),
    })


def om_meg(request):
    return render(request, "profil/om_meg.html", {"profil": Profil.objects.first()})


def prosjekter(request):
    return render(request, "profil/prosjekter.html", {"prosjekter": Prosjekt.objects.all()})


def kontakt(request):
    return render(request, "profil/kontakt.html", {"profil": Profil.objects.first()})
