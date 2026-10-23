from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "profil"

urlpatterns = [
    path("", views.forside, name="forside"),
    path("om-meg/", views.om_meg, name="om_meg"),
    path("prosjekter/", views.prosjekter, name="prosjekter"),
    path("kontakt/", views.kontakt, name="kontakt"),
    path("logg-inn/", auth_views.LoginView.as_view(template_name="profil/logg_inn.html"), name="logg_inn"),
    path("logg-ut/", auth_views.LogoutView.as_view(), name="logg_ut"),
    path("rediger/<str:innhold>/ny/", views.rediger, name="ny"),
    path("rediger/<str:innhold>/<int:pk>/", views.rediger, name="rediger"),
    path("rediger/<str:innhold>/<int:pk>/slett/", views.slett, name="slett"),
]
