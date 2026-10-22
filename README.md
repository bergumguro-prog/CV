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
3. Lag `.env` med en ny nøkkel, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=brukernavn.pythonanywhere.com` og `DJANGO_CSRF_TRUSTED_ORIGINS=https://brukernavn.pythonanywhere.com`.
4. Klargjør databasen og statiske filer:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python manage.py createsuperuser
   ```
5. Under **Web**: lag en ny web-app med *Manual configuration*, sett *Virtualenv* til `~/CV/venv`, og la WSGI-filen peke på `cv.settings` i `~/CV`.
6. Under **Static files**: koble `/static/` til `~/CV/staticfiles` og `/media/` til `~/CV/media`.
7. Skru på **Force HTTPS** og trykk **Reload**.

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
| `/admin/` | Redigering av innhold |
