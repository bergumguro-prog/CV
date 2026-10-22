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
