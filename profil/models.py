from django.db import models


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

    class Meta:
        verbose_name_plural = "profil"

    def __str__(self):
        return self.navn


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
