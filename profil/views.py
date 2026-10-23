from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import TYPER
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


er_admin = user_passes_test(lambda bruker: bruker.is_staff)


@er_admin
def rediger(request, innhold, pk=None):
    if innhold not in TYPER:
        raise Http404
    type_ = TYPER[innhold]
    objekt = get_object_or_404(type_.modell, pk=pk) if pk else type_.modell()

    data = request.POST if request.method == "POST" else None
    filer = request.FILES if request.method == "POST" else None
    form = type_.skjema()(data, filer, instance=objekt)
    form_ok = data is not None and form.is_valid()
    formsets = [
        (tittel, formset(data, filer, instance=form.instance, prefix=prefix))
        for tittel, prefix, formset in type_.formsets
    ]

    if form_ok and all(fs.is_valid() for _, fs in formsets):
        objekt = form.save()
        for _, fs in formsets:
            fs.instance = objekt
            fs.save()
        if "fortsett" in request.POST:
            return redirect("profil:rediger", innhold=innhold, pk=objekt.pk)
        return redirect(reverse(type_.side) + f"#{innhold}")

    navn = type_.modell._meta.verbose_name
    return render(request, "profil/rediger.html", {
        "form": form,
        "formsets": formsets,
        "objekt": objekt,
        "innhold": innhold,
        "overskrift": f"Rediger {navn}" if objekt.pk else f"Legg til {navn}",
        "tilbake": reverse(type_.side) + f"#{innhold}",
    })


@er_admin
def slett(request, innhold, pk):
    if innhold not in TYPER or innhold == "profil":
        raise Http404
    type_ = TYPER[innhold]
    objekt = get_object_or_404(type_.modell, pk=pk)
    if request.method == "POST":
        objekt.delete()
        return redirect(reverse(type_.side) + f"#{innhold}")
    return render(request, "profil/slett.html", {"objekt": objekt, "innhold": innhold})
