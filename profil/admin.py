from django.contrib import admin

from .models import Erfaring, Ferdighet, Profil, Prosjekt, Utdanning


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ["navn", "tittel", "epost"]


@admin.register(Erfaring)
class ErfaringAdmin(admin.ModelAdmin):
    list_display = ["stilling", "arbeidsgiver", "fra_dato", "til_dato"]


@admin.register(Utdanning)
class UtdanningAdmin(admin.ModelAdmin):
    list_display = ["studie", "skole", "fra_dato", "til_dato"]


@admin.register(Ferdighet)
class FerdighetAdmin(admin.ModelAdmin):
    list_display = ["navn", "niva"]
    list_editable = ["niva"]


@admin.register(Prosjekt)
class ProsjektAdmin(admin.ModelAdmin):
    list_display = ["tittel", "dato", "lenke"]
