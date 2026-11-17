import hashlib
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from PIL import Image, ImageOps


class Profil(models.Model):
    navn = models.CharField(max_length=100)
    tittel = models.CharField(max_length=100, blank=True)
    bilde = models.ImageField(upload_to="profil/", blank=True)
    om_meg = models.TextField(blank=True)
    epost = models.EmailField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    lyd = models.FileField(upload_to="lyd/", blank=True, help_text="Lages med «python manage.py lag_lyd».")
    lyd_manus = models.TextField(blank=True, help_text="Teksten som er lest opp i lydfilen.")
    # Større, skarp utgave til forstørrelsen på forsiden. Lages av save().
    bilde_stor = models.ImageField(upload_to="profil/", blank=True, editable=False)

    STOR_BREDDE = 1200

    class Meta:
        verbose_name_plural = "profil"

    def __str__(self):
        return self.navn

    @property
    def stort_bilde_url(self):
        """Den store utgaven, eller originalen hvis den ikke er laget ennå."""
        return self.bilde_stor.url if self.bilde_stor else self.bilde.url

    def save(self, *args, **kwargs):
        nytt_bilde = bool(self.bilde) and not self.bilde._committed
        super().save(*args, **kwargs)
        gammel = self.bilde_stor.name if self.bilde_stor else ""
        if self.bilde and (nytt_bilde or not self.bilde_stor):
            self.bilde_stor.save(f"{Path(self.bilde.name).stem}-stor.webp", self._lag_stort_bilde(), save=False)
        elif not self.bilde and self.bilde_stor:
            self.bilde_stor = ""
        else:
            return
        super().save(update_fields=["bilde_stor"])
        _slett(self.bilde.storage, [gammel], behold=[self.bilde_stor.name])

    def _lag_stort_bilde(self):
        with self.bilde.open("rb") as fil, Image.open(fil) as original:
            # Mobilbilder lagres ofte liggende med en «roter»-merknad; snu dem riktig først
            bilde = ImageOps.exif_transpose(original).convert("RGB")
        if bilde.width > self.STOR_BREDDE:
            hoyde = round(bilde.height * self.STOR_BREDDE / bilde.width)
            bilde = bilde.resize((self.STOR_BREDDE, hoyde), Image.Resampling.LANCZOS)
        return _som_webp(bilde, kvalitet=85)


class Erfaring(models.Model):
    stilling = models.CharField(max_length=100)
    arbeidsgiver = models.CharField(max_length=100)
    fra_dato = models.DateField()
    til_dato = models.DateField(null=True, blank=True, help_text="La stå tom hvis du jobber der nå.")
    beskrivelse = models.TextField(blank=True)
    detaljer = models.TextField(blank=True, help_text="Vises når man trykker «Vis mer».")

    class Meta:
        verbose_name_plural = "erfaringer"
        ordering = ["-fra_dato"]

    @property
    def har_detaljer(self):
        return bool(self.beskrivelse or self.detaljer) or bool(self.egenskaper.all())

    def __str__(self):
        return f"{self.stilling}, {self.arbeidsgiver}"


class Utdanning(models.Model):
    studie = models.CharField(max_length=100)
    skole = models.CharField(max_length=100)
    fra_dato = models.DateField()
    til_dato = models.DateField(null=True, blank=True, help_text="La stå tom hvis du studerer nå.")
    beskrivelse = models.TextField(blank=True)
    detaljer = models.TextField(blank=True, help_text="Vises når man trykker «Vis mer».")

    class Meta:
        verbose_name_plural = "utdanninger"
        ordering = ["-fra_dato"]

    @property
    def har_detaljer(self):
        return bool(self.beskrivelse or self.detaljer) or bool(self.fag.all()) or bool(self.egenskaper.all())

    def __str__(self):
        return f"{self.studie}, {self.skole}"


class Ferdighet(models.Model):
    class Niva(models.IntegerChoices):
        GRUNNLEGGENDE = 1, "Grunnleggende"
        GOD = 2, "God"
        SVAERT_GOD = 3, "Svært god"

    navn = models.CharField(max_length=50)
    niva = models.IntegerField("nivå", choices=Niva, default=Niva.GOD)

    class Meta:
        verbose_name_plural = "ferdigheter"
        ordering = ["-niva", "navn"]

    def __str__(self):
        return self.navn


class Prosjekt(models.Model):
    tittel = models.CharField(max_length=100)
    beskrivelse = models.TextField()
    lenke = models.URLField(blank=True)
    dato = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "prosjekter"
        ordering = ["-dato"]

    @property
    def har_detaljer(self):
        return bool(self.beskrivelse or self.lenke)

    def __str__(self):
        return self.tittel


class Verv(models.Model):
    rolle = models.CharField(max_length=100)
    organisasjon = models.CharField(max_length=100)
    fra_dato = models.DateField()
    til_dato = models.DateField(null=True, blank=True, help_text="La stå tom hvis vervet pågår.")
    beskrivelse = models.TextField(blank=True)
    detaljer = models.TextField(blank=True, help_text="Vises når man trykker «Vis mer».")

    class Meta:
        verbose_name_plural = "verv"
        ordering = ["-fra_dato"]

    @property
    def har_detaljer(self):
        return bool(self.beskrivelse or self.detaljer) or bool(self.egenskaper.all())

    def __str__(self):
        return f"{self.rolle}, {self.organisasjon}"


class Fag(models.Model):
    utdanning = models.ForeignKey(Utdanning, on_delete=models.CASCADE, related_name="fag")
    emnekode = models.CharField(max_length=20, blank=True)
    navn = models.CharField(max_length=100)
    beskrivelse = models.TextField(blank=True, help_text="Hva faget handlet om, og hvorfor det er relevant.")

    class Meta:
        verbose_name_plural = "fag"
        ordering = ["emnekode", "navn"]

    def __str__(self):
        return f"{self.emnekode} {self.navn}".strip()


class Idrettslag(models.Model):
    idrett = models.CharField(max_length=50)
    lag = models.CharField("lag eller klubb", max_length=100)
    rolle = models.CharField("rolle eller nivå", max_length=100, blank=True)
    fra_dato = models.DateField()
    til_dato = models.DateField(null=True, blank=True)
    beskrivelse = models.TextField(blank=True)
    detaljer = models.TextField(blank=True, help_text="Vises når man trykker «Vis mer».")

    class Meta:
        verbose_name = "lag eller klubb"
        verbose_name_plural = "lag og klubber"
        ordering = ["-fra_dato"]

    @property
    def har_detaljer(self):
        return bool(self.rolle or self.beskrivelse or self.detaljer) or bool(self.egenskaper.all())

    def __str__(self):
        return f"{self.idrett}, {self.lag}"


class Idrettshendelse(models.Model):
    navn = models.CharField(max_length=100, help_text="F.eks. Oslo Maraton 2026.")
    dato = models.DateField()
    resultat = models.CharField(max_length=100, blank=True, help_text="F.eks. 3:45:12 eller 2. plass.")
    beskrivelse = models.TextField(blank=True)

    class Meta:
        verbose_name = "konkurranse eller løp"
        verbose_name_plural = "konkurranser og løp"
        ordering = ["-dato"]

    @property
    def har_detaljer(self):
        return bool(self.beskrivelse) or bool(self.egenskaper.all())

    def __str__(self):
        return f"{self.navn} – {self.resultat}" if self.resultat else self.navn


class Egenskap(models.Model):
    navn = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "egenskaper"
        ordering = ["navn"]

    def __str__(self):
        return self.navn


class EgenskapKobling(models.Model):
    """Kobler en egenskap til én oppføring, med forklaring på hvordan oppføringen ga egenskapen."""

    egenskap = models.ForeignKey(Egenskap, on_delete=models.CASCADE)
    forklaring = models.TextField(blank=True, help_text="Hvordan akkurat denne oppføringen ga egenskapen.")

    class Meta:
        abstract = True
        ordering = ["egenskap__navn"]
        verbose_name = "egenskap"
        verbose_name_plural = "egenskaper"

    def __str__(self):
        return str(self.egenskap)


class UtdanningEgenskap(EgenskapKobling):
    utdanning = models.ForeignKey(Utdanning, on_delete=models.CASCADE, related_name="egenskaper")

    class Meta(EgenskapKobling.Meta):
        constraints = [models.UniqueConstraint(fields=["utdanning", "egenskap"], name="unik_utdanning_egenskap")]


class ErfaringEgenskap(EgenskapKobling):
    erfaring = models.ForeignKey(Erfaring, on_delete=models.CASCADE, related_name="egenskaper")

    class Meta(EgenskapKobling.Meta):
        constraints = [models.UniqueConstraint(fields=["erfaring", "egenskap"], name="unik_erfaring_egenskap")]


class VervEgenskap(EgenskapKobling):
    verv = models.ForeignKey(Verv, on_delete=models.CASCADE, related_name="egenskaper")

    class Meta(EgenskapKobling.Meta):
        constraints = [models.UniqueConstraint(fields=["verv", "egenskap"], name="unik_verv_egenskap")]


class IdrettslagEgenskap(EgenskapKobling):
    idrettslag = models.ForeignKey(Idrettslag, on_delete=models.CASCADE, related_name="egenskaper")

    class Meta(EgenskapKobling.Meta):
        constraints = [models.UniqueConstraint(fields=["idrettslag", "egenskap"], name="unik_idrettslag_egenskap")]


class IdrettshendelseEgenskap(EgenskapKobling):
    idrettshendelse = models.ForeignKey(Idrettshendelse, on_delete=models.CASCADE, related_name="egenskaper")

    class Meta(EgenskapKobling.Meta):
        constraints = [
            models.UniqueConstraint(fields=["idrettshendelse", "egenskap"], name="unik_idrettshendelse_egenskap")
        ]


# Formatet på utsnittet til forsidebildene (bredde, høyde). Brukes av Python, skjemaet,
# beskjæringsverktøyet og CSS-en (via context processoren), så det står bare her.
UTSNITT_FORHOLD = (16, 9)

# Minste utsnitt i piksler, så bildet blir skarpt også på store skjermer
MIN_BREDDE = 1200
MIN_HOYDE = round(MIN_BREDDE * UTSNITT_FORHOLD[1] / UTSNITT_FORHOLD[0])  # 675

# Hvor mye utsnittet kan avvike fra 16:9 før det avvises (avrunding i nettleseren)
FORHOLD_TOLERANSE = 0.02

_prosent = [MinValueValidator(0), MaxValueValidator(100)]


class Forsidebilde(models.Model):
    """Et stort bilde i karusellen øverst på forsiden.

    Originalen lagres uendret. Ut fra den lages et beskåret utsnitt i 16:9 i to
    størrelser, bare når bildet eller utsnittet endres.
    """

    STOR_BREDDE = 2400
    LITEN_BREDDE = 1200

    bilde = models.ImageField(
        upload_to="forside/original/",
        help_text=f"Liggende bilder passer best. Minst {MIN_BREDDE} × {MIN_HOYDE} piksler. "
                  "Velg utsnittet i forhåndsvisningen under.",
    )
    original_bredde = models.PositiveIntegerField(default=0, editable=False)
    original_hoyde = models.PositiveIntegerField(default=0, editable=False)

    # Utsnittet, i prosent av originalen (så det virker uansett bildets størrelse)
    utsnitt_x = models.FloatField(null=True, blank=True, validators=_prosent)
    utsnitt_y = models.FloatField(null=True, blank=True, validators=_prosent)
    utsnitt_bredde = models.FloatField(null=True, blank=True, validators=_prosent)
    utsnitt_hoyde = models.FloatField(null=True, blank=True, validators=_prosent)

    # Ferdig beskårne bilder, laget av save()
    bilde_stor = models.ImageField(upload_to="forside/", blank=True, editable=False)
    bilde_liten = models.ImageField(upload_to="forside/", blank=True, editable=False)
    bredde = models.PositiveIntegerField(default=0, editable=False)
    hoyde = models.PositiveIntegerField(default=0, editable=False)
    generert_fra = models.CharField(max_length=64, blank=True, editable=False)

    alt_tekst = models.CharField(
        "alternativ tekst", max_length=200,
        help_text="Beskriv bildet for dem som ikke kan se det, f.eks. «Utsikt over Trondheim fra Gråkallen».",
    )
    bildetekst = models.CharField(max_length=120, blank=True, help_text="Valgfri kort tekst som vises på bildet.")
    rekkefolge = models.PositiveIntegerField("rekkefølge", default=0, help_text="Lavest tall vises først.")
    aktiv = models.BooleanField(default=True, help_text="Fjern krysset for å skjule bildet uten å slette det.")

    class Meta:
        verbose_name = "forsidebilde"
        verbose_name_plural = "forsidebilder"
        ordering = ["rekkefolge", "pk"]

    def __str__(self):
        return self.alt_tekst

    # ---- Til malene --------------------------------------------------------------

    @property
    def vis_url(self):
        """Det beskårne bildet, eller originalen hvis utsnittet ikke er laget ennå."""
        return self.bilde_stor.url if self.bilde_stor else self.bilde.url

    @property
    def srcset(self):
        """Begge størrelsene, så nettleseren selv velger den minste som er skarp nok."""
        if not self.bilde_stor:
            return f"{self.bilde.url} {self.original_bredde or self.bredde}w"
        if not self.bilde_liten or self.bredde <= self.LITEN_BREDDE:
            return f"{self.bilde_stor.url} {self.bredde}w"
        return f"{self.bilde_liten.url} {self.LITEN_BREDDE}w, {self.bilde_stor.url} {self.bredde}w"

    @property
    def fokus(self):
        """Midten av det valgte utsnittet, i prosent av bildet som vises: (x, y).

        Det beskårne bildet er selve utsnittet, så der er midten alltid 50 %. Før
        utsnittet er laget vises originalen, og da ligger midten der rammen står.
        """
        if self.bilde_stor or not self.har_utsnitt:
            return 50.0, 50.0
        return self.utsnitt_x + self.utsnitt_bredde / 2, self.utsnitt_y + self.utsnitt_hoyde / 2

    # ---- Utsnitt -----------------------------------------------------------------

    @property
    def har_utsnitt(self):
        return None not in (self.utsnitt_x, self.utsnitt_y, self.utsnitt_bredde, self.utsnitt_hoyde)

    def sett_midtstilt_utsnitt(self):
        """Største mulige 16:9-utsnitt midt i bildet."""
        self.utsnitt_x, self.utsnitt_y, self.utsnitt_bredde, self.utsnitt_hoyde = midtstilt_utsnitt(
            self.original_bredde, self.original_hoyde
        )

    def clean(self):
        if not self.bilde:
            return  # «Feltet er påkrevd» kommer fra skjemaet
        if self._nytt_original():
            try:
                self.original_bredde, self.original_hoyde = originalstorrelse(self.bilde)
            except OSError:
                raise ValidationError({"bilde": "Filen er ikke et bilde som kan leses."})
            if self.original_bredde < MIN_BREDDE or self.original_hoyde < MIN_HOYDE:
                raise ValidationError({"bilde": (
                    f"Bildet er for lite ({self.original_bredde} × {self.original_hoyde} piksler). "
                    f"Det må være minst {MIN_BREDDE} × {MIN_HOYDE} piksler for å bli skarpt på store skjermer."
                )})
        if not self.har_utsnitt:
            self.sett_midtstilt_utsnitt()
            return
        feil = utsnittsfeil(self.utsnitt_x, self.utsnitt_y, self.utsnitt_bredde, self.utsnitt_hoyde,
                            self.original_bredde, self.original_hoyde)
        if feil:
            raise ValidationError({"bilde": feil})

    # ---- Lagring -----------------------------------------------------------------

    def _nytt_original(self):
        return bool(self.bilde) and not self.bilde._committed

    def _signatur(self):
        """Hva de beskårne bildene er laget av. Endres den, må de lages på nytt."""
        verdier = f"{self.bilde.name}|{self.utsnitt_x:.4f}|{self.utsnitt_y:.4f}|" \
                  f"{self.utsnitt_bredde:.4f}|{self.utsnitt_hoyde:.4f}"
        return hashlib.sha256(verdier.encode()).hexdigest()[:16]

    def save(self, *args, **kwargs):
        gammel = Forsidebilde.objects.filter(pk=self.pk).first() if self.pk else None
        if self._nytt_original():
            self.original_bredde, self.original_hoyde = originalstorrelse(self.bilde)
        elif not self.original_bredde and self.bilde:
            self.original_bredde, self.original_hoyde = originalstorrelse(self.bilde)
        if not self.har_utsnitt:
            self.sett_midtstilt_utsnitt()

        super().save(*args, **kwargs)  # lagrer originalen, så den har et endelig filnavn

        if self.bilde and (self._signatur() != self.generert_fra or not self.bilde_stor):
            # Navnene må hentes nå: filfeltene får nye navn når utsnittet lagres
            gamle = [fil.name for fil in (self.bilde_stor, self.bilde_liten) if fil]
            self._lag_utsnitt()
            super().save(update_fields=["bilde_stor", "bilde_liten", "bredde", "hoyde", "generert_fra"])
            _slett(self.bilde.storage, gamle, behold=[self.bilde_stor.name, self.bilde_liten.name, self.bilde.name])

        if gammel and gammel.bilde and gammel.bilde.name != self.bilde.name:
            _slett(self.bilde.storage, [gammel.bilde.name])

    def _lag_utsnitt(self):
        with self.bilde.open("rb") as fil, Image.open(fil) as original:
            # Mobilbilder lagres ofte liggende med en «roter»-merknad; snu dem riktig først
            bilde = ImageOps.exif_transpose(original).convert("RGB")
        b, h = bilde.size
        boks = (
            round(self.utsnitt_x / 100 * b),
            round(self.utsnitt_y / 100 * h),
            round((self.utsnitt_x + self.utsnitt_bredde) / 100 * b),
            round((self.utsnitt_y + self.utsnitt_hoyde) / 100 * h),
        )
        utsnitt = bilde.crop(boks)
        stor = _i_format(utsnitt, min(self.STOR_BREDDE, utsnitt.width))
        liten = _i_format(utsnitt, min(self.LITEN_BREDDE, stor.width))

        signatur = self._signatur()
        navn = f"{Path(self.bilde.name).stem}-{signatur[:8]}"
        self.bilde_stor.save(f"{navn}-{stor.width}.webp", _som_webp(stor), save=False)
        self.bilde_liten.save(f"{navn}-{liten.width}.webp", _som_webp(liten), save=False)
        self.bredde, self.hoyde = stor.size
        self.generert_fra = signatur


def originalstorrelse(fil):
    """Bredde og høyde slik bildet faktisk vises, altså etter EXIF-rotasjon."""
    lagret = fil._committed
    fil.open("rb")
    fil.seek(0)
    try:
        with Image.open(fil) as bilde:
            bredde, hoyde = bilde.size
            orientering = bilde.getexif().get(0x0112, 1)
    finally:
        if lagret:
            fil.close()  # en ny opplasting holdes åpen til den er lagret
        else:
            fil.seek(0)
    return (hoyde, bredde) if orientering in (5, 6, 7, 8) else (bredde, hoyde)


def midtstilt_utsnitt(bredde, hoyde):
    """Største 16:9-utsnitt midt i et bilde, i prosent: (x, y, bredde, høyde)."""
    if not bredde or not hoyde:
        return 0.0, 0.0, 100.0, 100.0
    forhold = UTSNITT_FORHOLD[0] / UTSNITT_FORHOLD[1]
    b = min(bredde, hoyde * forhold)
    h = b / forhold
    return (
        (bredde - b) / 2 / bredde * 100,
        (hoyde - h) / 2 / hoyde * 100,
        b / bredde * 100,
        h / hoyde * 100,
    )


def utsnittsfeil(x, y, b, h, bredde, hoyde):
    """Feilmelding hvis utsnittet ikke kan brukes, ellers None. Alle mål i prosent."""
    margin = 0.01
    if b <= 0 or h <= 0 or x < -margin or y < -margin or x + b > 100 + margin or y + h > 100 + margin:
        return "Utsnittet går utenfor bildet. Flytt eller gjør rammen mindre."
    if not bredde or not hoyde:
        return None
    forhold = (b * bredde) / (h * hoyde)
    onsket = UTSNITT_FORHOLD[0] / UTSNITT_FORHOLD[1]
    if abs(forhold / onsket - 1) > FORHOLD_TOLERANSE:
        return f"Utsnittet må ha formatet {UTSNITT_FORHOLD[0]}:{UTSNITT_FORHOLD[1]}."
    if b / 100 * bredde < MIN_BREDDE - 1:
        return (f"Utsnittet er for lite ({round(b / 100 * bredde)} piksler bredt). "
                f"Det må være minst {MIN_BREDDE} piksler bredt for å bli skarpt.")
    return None


def _i_format(bilde, bredde):
    """Skaler til gitt bredde med nøyaktig 16:9, så alle utsnitt får samme form."""
    hoyde = round(bredde * UTSNITT_FORHOLD[1] / UTSNITT_FORHOLD[0])
    if bilde.size == (bredde, hoyde):
        return bilde
    return bilde.resize((bredde, hoyde), Image.Resampling.LANCZOS)


def _som_webp(bilde, kvalitet=82):
    fil = BytesIO()
    bilde.save(fil, "WEBP", quality=kvalitet, method=5)
    return ContentFile(fil.getvalue())


def _slett(lager, navn, behold=()):
    for fil in navn:
        if fil and fil not in behold:
            lager.delete(fil)


@receiver(post_delete, sender=Forsidebilde)
def slett_forsidebildefiler(sender, instance, **kwargs):
    """Fjern original og utsnitt når bildet slettes, så media-mappen ikke fylles opp."""
    filer = [instance.bilde, instance.bilde_stor, instance.bilde_liten]
    _slett(instance.bilde.storage, [fil.name for fil in filer if fil])
