import json
import urllib.request

from django.conf import settings


def lag_manus(profil):
    """Lager en kort, muntlig presentasjon: hilsen, «Om meg» og en avslutning.

    Lister over jobber og verv blir tunge å høre på, så det som skal med i lyden
    skrives inn i «Om meg».
    """
    avsnitt = [f"Hei! Jeg heter {profil.navn}."]
    if profil.om_meg:
        avsnitt.append(profil.om_meg)
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
