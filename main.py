import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.spotify_service import SpotifyService
from services.lastfm_service import LastFMService
from logic.classifier import Clasificador
from logic.organizer import MotorOrganizacion
from ui.main_window import VentanaPrincipal, lanzar_con_splash

CONFIG_FILE = "config.json"
GENRES_FILE = os.path.join("config", "genres.json")


def cargar_config() -> dict:
    defaults = {
        "client_id":      "",
        "client_secret":  "",
        "redirect_uri":   "http://127.0.0.1:8888/callback",
        "lastfm_api_key": ""
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "client_id":      "TU_CLIENT_ID_AQUI",
                "client_secret":  "TU_CLIENT_SECRET_AQUI",
                "redirect_uri":   "http://127.0.0.1:8888/callback",
                "lastfm_api_key": "TU_LASTFM_KEY_AQUI_OPCIONAL"
            }, f, indent=2)
        print(f"Se creó {CONFIG_FILE}. Completa tus credenciales y vuelve a ejecutar.")
        sys.exit(0)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    defaults.update(datos)
    return defaults


def validar_config(config: dict) -> bool:
    if not config.get("client_id") or "TU_" in config["client_id"]:
        print("ERROR: Completa el client_id en config.json")
        return False
    if not config.get("client_secret") or "TU_" in config["client_secret"]:
        print("ERROR: Completa el client_secret en config.json")
        return False
    return True


def main():
    config = cargar_config()
    if not validar_config(config):
        input("\nPresiona Enter para salir...")
        sys.exit(1)

    spotify = SpotifyService(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        redirect_uri=config["redirect_uri"]
    )

    lastfm = None
    lf_key = config.get("lastfm_api_key", "")
    if lf_key and "TU_" not in lf_key:
        try:
            lastfm = LastFMService(lf_key)
            print("LastFM activo — clasificación mejorada disponible")
        except Exception as e:
            print(f"LastFM no disponible: {e}")

    clasificador = Clasificador(GENRES_FILE)
    motor        = MotorOrganizacion(spotify, lastfm, clasificador)

    app = VentanaPrincipal()
    app.vincular_controlador(motor)

    # Mostrar splash al iniciar
    lanzar_con_splash(app)

    app.mainloop()


if __name__ == "__main__":
    main()
