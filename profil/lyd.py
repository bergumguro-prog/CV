import json
import urllib.request
from datetime import date

from django.conf import settings
from django.db.models import Q

from .models import Erfaring, Utdanning, Verv


def _liste(deler):
    """['a', 'b', 'c'] -> 'a, b og c'"""
    if len(deler) <= 1:
        return "".join(deler)
    return ", ".join(deler[:-1]) + " og " + deler[-1]


def _liten_forbokstav(tekst):
    """'Leder' -> 'leder', men 'PR-ansvarlig' beholdes."""
    if len(tekst) > 1 and tekst[1].islower():
        return tekst[0].lower() + tekst[1:]
    return tekst


def _pagaende(modell):
    return modell.objects.filter(Q(til_dato__isnull=True) | Q(til_dato__gte=date.today()))


def lag_manus(profil):
    """Lager en kort, muntlig presentasjon ut fra innholdet i databasen."""
    avsnitt = [f"Hei! Jeg heter {profil.navn}."]
    if profil.om_meg:
        avsnitt.append(profil.om_meg)

    studier = [f"{u.studie} ved {u.skole}" for u in _pagaende(Utdanning)]
    if studier:
        avsnitt.append(f"Akkurat nå studerer jeg {_liste(studier)}.")

    jobber = [f"{_liten_forbokstav(e.stilling)} i {e.arbeidsgiver}" for e in _pagaende(Erfaring)]
    if jobber:
        avsnitt.append(f"Ved siden av jobber jeg som {_liste(jobber)}.")

    verv = [f"{_liten_forbokstav(v.rolle)} i {v.organisasjon}" for v in _pagaende(Verv)]
    if verv:
        avsnitt.append(f"Jeg har også disse vervene: {_liste(verv)}.")

    avsnitt.append("Trykk på «Vis mer» for å lese mer om hva jeg har gjort. Ta gjerne kontakt!")
    return "\n\n".join(avsnitt)


def les_opp(tekst):
    """Sender teksten til ElevenLabs og returnerer lyden som MP3-bytes."""
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
        "?output_format=mp3_44100_128"
    )
    foresporsel = urllib.request.Request(
        url,
        data=json.dumps({"text": tekst, "model_id": settings.ELEVENLABS_MODEL}).encode(),
        headers={"xi-api-key": settings.ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(foresporsel, timeout=120) as svar:
        return svar.read()
