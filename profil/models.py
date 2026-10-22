from django.db import models


class Profil(models.Model):
    navn = models.CharField(max_length=100)
    tittel = models.CharField(max_length=100, blank=True)
    om_meg = models.TextField(blank=True)
    epost = models.EmailField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)

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

    class Meta:
        verbose_name_plural = "erfaringer"
        ordering = ["-fra_dato"]

    def __str__(self):
        return f"{self.stilling}, {self.arbeidsgiver}"


class Utdanning(models.Model):
    studie = models.CharField(max_length=100)
    skole = models.CharField(max_length=100)
    fra_dato = models.DateField()
    til_dato = models.DateField(null=True, blank=True, help_text="La stå tom hvis du studerer nå.")
    beskrivelse = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "utdanninger"
        ordering = ["-fra_dato"]

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

    def __str__(self):
        return self.tittel


class Verv(models.Model):
    rolle = models.CharField(max_length=100)
    organisasjon = models.CharField(max_length=100)
    fra_dato = models.DateField()
    til_dato = models.DateField(null=True, blank=True, help_text="La stå tom hvis vervet pågår.")
    beskrivelse = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "verv"
        ordering = ["-fra_dato"]

    def __str__(self):
        return f"{self.rolle}, {self.organisasjon}"
