from django.shortcuts import render


def forside(request):
    return render(request, "profil/forside.html")
