from django.contrib import admin

from .models import (
    Egenskap,
    Erfaring,
    ErfaringEgenskap,
    Fag,
    Ferdighet,
    Profil,
    Prosjekt,
    Utdanning,
    UtdanningEgenskap,
    Verv,
    VervEgenskap,
)


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ["navn", "tittel", "epost"]


@admin.register(Egenskap)
class EgenskapAdmin(admin.ModelAdmin):
    search_fields = ["navn"]


class ErfaringEgenskapInline(admin.StackedInline):
    model = ErfaringEgenskap
    autocomplete_fields = ["egenskap"]
    extra = 0


class VervEgenskapInline(admin.StackedInline):
    model = VervEgenskap
    autocomplete_fields = ["egenskap"]
    extra = 0


class UtdanningEgenskapInline(admin.StackedInline):
    model = UtdanningEgenskap
    autocomplete_fields = ["egenskap"]
    extra = 0


class FagInline(admin.StackedInline):
    model = Fag
    extra = 0


@admin.register(Erfaring)
class ErfaringAdmin(admin.ModelAdmin):
    list_display = ["stilling", "arbeidsgiver", "fra_dato", "til_dato"]
    inlines = [ErfaringEgenskapInline]


@admin.register(Verv)
class VervAdmin(admin.ModelAdmin):
    list_display = ["rolle", "organisasjon", "fra_dato", "til_dato"]
    inlines = [VervEgenskapInline]


@admin.register(Utdanning)
class UtdanningAdmin(admin.ModelAdmin):
    list_display = ["studie", "skole", "fra_dato", "til_dato"]
    inlines = [FagInline, UtdanningEgenskapInline]


@admin.register(Ferdighet)
class FerdighetAdmin(admin.ModelAdmin):
    list_display = ["navn", "niva"]
    list_editable = ["niva"]


@admin.register(Prosjekt)
class ProsjektAdmin(admin.ModelAdmin):
    list_display = ["tittel", "dato", "lenke"]
