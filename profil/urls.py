from django.urls import path

from . import views

app_name = "profil"

urlpatterns = [
    path("", views.forside, name="forside"),
    path("om-meg/", views.om_meg, name="om_meg"),
    path("prosjekter/", views.prosjekter, name="prosjekter"),
    path("kontakt/", views.kontakt, name="kontakt"),
]
