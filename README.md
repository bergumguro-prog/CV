# CV

En liten nettside som presenterer meg: erfaring, utdanning, ferdigheter og prosjekter. Laget med Django.

Alt innhold legges inn i Django admin, så ingen personlig informasjon ligger i koden.

## Teknologi

- Python 3.14
- Django 6.1
- SQLite

## Kjør lokalt

```zsh
git clone https://github.com/bergumguro-prog/CV.git
cd CV

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # fyll inn en egen DJANGO_SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Siden kjører på http://127.0.0.1:8000, og innhold legges inn på http://127.0.0.1:8000/admin.

En ny `DJANGO_SECRET_KEY` lages med:

```zsh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Redigere innhold

Gå til `/logg-inn/` og logg inn med superbrukeren. Da dukker «Rediger» og «+ Legg til» opp direkte på CV-en.

Etter 5 mislykkede innloggingsforsøk sperres IP-adressen i 1 time. Sperrer du deg selv ute, opphever du det med:

```zsh
python manage.py axes_reset
```

## Forsidebilder

Øverst på forsiden kan det ligge en stor bildekarusell med navnet og tittelen din. Når man scroller, krymper den til et smalt banner med navnet og menyen. Uten bilder ser forsiden ut som vanlig.

1. Logg inn og trykk **+ Legg til forsidebilde** (under navnet ditt på forsiden, eller oppe i karusellen når den finnes).
2. Velg et bilde. Det dukker opp med en ramme i 16:9 som viser hva som kommer med: dra rammen for å flytte den og hjørnene for å endre størrelsen (piltastene og + / − virker også). Under ser du hvordan den smale stripen øverst blir når man har scrollet, så du kan sjekke at f.eks. ansikter er med.
3. Skriv en **alternativ tekst** – en kort beskrivelse for dem som bruker skjermleser. Bildeteksten er valgfri og vises oppe til høyre på bildet.
4. **Rekkefølge** bestemmer hvilket bilde som vises først (lavest tall først). Fjern krysset for **Aktiv** for å skjule et bilde uten å slette det.

Bildet må være minst 1200 × 675 piksler. Originalen lagres uendret, så du kan velge et nytt utsnitt senere med «Rediger bilde» uten å laste opp på nytt. Utsnittet lagres i 2400 og 1200 px bredde (WebP), og lages bare på nytt når bildet eller utsnittet endres. Formatet (16:9) står ett sted, `UTSNITT_FORHOLD` i `profil/models.py`. Bildene bytter av seg selv hvert 6. sekund, og besøkende kan pause, sveipe eller bruke piltastene. Skjulte bilder finner du igjen under **Forsidebilder** i admin.

## Publisering på PythonAnywhere

1. Lag en gratis konto på [pythonanywhere.com](https://www.pythonanywhere.com) og åpne en **Bash console**.
2. Klon repoet og sett opp miljøet:
   ```bash
   git clone https://github.com/bergumguro-prog/CV.git
   cd CV
   python3.14 -m venv venv   # bruk nyeste Python-versjon PythonAnywhere tilbyr
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Lag `.env` med en ny nøkkel, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=brukernavn.pythonanywhere.com` og `DJANGO_CSRF_TRUSTED_ORIGINS=https://brukernavn.pythonanywhere.com`. Siden er skjult for søkemotorer til du setter `DJANGO_SOKBAR=True`.
4. Klargjør databasen og statiske filer:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python manage.py createsuperuser
   ```
5. Under **Web**: lag en ny web-app med *Manual configuration*, sett *Virtualenv* til `~/CV/venv`, og la WSGI-filen peke på `cv.settings` i `~/CV`.
6. Under **Static files**: koble `/static/` til `~/CV/staticfiles` og `/media/` til `~/CV/media`.
7. Skru på **Force HTTPS** og trykk **Reload**.

### Oppdatere siden senere

Etter å ha hentet nye endringer (f.eks. forsidebildene) kjører du dette i Bash-konsollen, og trykker **Reload** under **Web**:

```bash
cd ~/CV && source venv/bin/activate
git pull
python manage.py migrate          # nødvendig etter oppdateringer med nye modeller, som Forsidebilde
python manage.py lag_forsidebilder   # lager utsnitt for forsidebilder som mangler det
python manage.py collectstatic --noinput
```

`collectstatic` må kjøres etter hver oppdatering. Den gir CSS- og JavaScript-filene innholdet sitt i filnavnet (f.eks. `style.3f9a2c1b.css`), så besøkende alltid får den nye utgaven i stedet for en gammel kopi fra nettleseren.

Bildene du laster opp havner i `~/CV/media/`. Sjekk at `/media/` er koblet til `~/CV/media` under **Static files** (punkt 6), ellers vises ikke forsidebildene og profilbildet når `DJANGO_DEBUG=False`.

Innhold fra en lokal database kan flyttes med `python manage.py dumpdata profil --indent 2 > cv-data.json` lokalt og `python manage.py loaddata cv-data.json` på serveren. Profilbildet lastes opp på nytt i admin.

## Tester

```zsh
python manage.py test
```

## Sider

| URL | Innhold |
|---|---|
| `/` | Erfaring, utdanning og ferdigheter |
| `/om-meg/` | Om meg-tekst |
| `/prosjekter/` | Prosjekter |
| `/kontakt/` | E-post, GitHub og LinkedIn |
| `/logg-inn/` | Innlogging for å redigere |
| `/admin/` | Djangos admin (avansert) |
