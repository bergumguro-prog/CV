from dataclasses import dataclass, field

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import BaseInlineFormSet, inlineformset_factory, modelform_factory

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


class EgenskapForm(forms.ModelForm):
    """Egenskapen skrives inn som tekst, og lages automatisk hvis den ikke finnes fra før."""

    navn = forms.CharField(label="Egenskap", max_length=50)
    field_order = ["navn", "forklaring"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["navn"].initial = self.instance.egenskap.navn

    def save(self, commit=True):
        navn = self.cleaned_data["navn"].strip()
        egenskap = Egenskap.objects.filter(navn__iexact=navn).first()
        self.instance.egenskap = egenskap or Egenskap.objects.create(navn=navn)
        return super().save(commit)


class EgenskapFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        brukt = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or self._should_delete_form(form):
                continue
            navn = form.cleaned_data.get("navn", "").strip().lower()
            if not navn:
                continue
            if navn in brukt:
                raise ValidationError("Samme egenskap er lagt inn to ganger.")
            brukt.add(navn)


def _egenskaper(forelder, kobling):
    return inlineformset_factory(
        forelder, kobling, form=EgenskapForm, formset=EgenskapFormSet,
        fields=["forklaring"], extra=1, can_delete=True,
    )


FagFormSet = inlineformset_factory(
    Utdanning, Fag, fields=["emnekode", "navn", "beskrivelse"], extra=1, can_delete=True,
)


@dataclass
class Type:
    """Hva som kan redigeres for én type innhold, og hvor man sendes tilbake etterpå."""

    navn: str
    modell: type[models.Model]
    felt: list[str]
    side: str = "profil:forside"
    formsets: list[tuple[str, str, type]] = field(default_factory=list)

    def skjema(self):
        datoer = [f for f in self.felt if isinstance(self.modell._meta.get_field(f), models.DateField)]
        widgets = {f: forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d") for f in datoer}
        return modelform_factory(self.modell, fields=self.felt, widgets=widgets)


TYPER = {
    "profil": Type("profil", Profil, ["navn", "tittel", "bilde", "om_meg", "epost", "github", "linkedin"]),
    "erfaring": Type(
        "erfaring", Erfaring,
        ["stilling", "arbeidsgiver", "fra_dato", "til_dato", "beskrivelse", "detaljer"],
        formsets=[("Egenskaper", "egenskaper", _egenskaper(Erfaring, ErfaringEgenskap))],
    ),
    "verv": Type(
        "verv", Verv,
        ["rolle", "organisasjon", "fra_dato", "til_dato", "beskrivelse", "detaljer"],
        formsets=[("Egenskaper", "egenskaper", _egenskaper(Verv, VervEgenskap))],
    ),
    "utdanning": Type(
        "utdanning", Utdanning,
        ["studie", "skole", "fra_dato", "til_dato", "beskrivelse", "detaljer"],
        formsets=[
            ("Relevante fag", "fag", FagFormSet),
            ("Egenskaper", "egenskaper", _egenskaper(Utdanning, UtdanningEgenskap)),
        ],
    ),
    "ferdighet": Type("ferdighet", Ferdighet, ["navn", "niva"]),
    "prosjekt": Type("prosjekt", Prosjekt, ["tittel", "dato", "beskrivelse", "lenke"], side="profil:prosjekter"),
}
