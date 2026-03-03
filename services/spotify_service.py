import os
import json
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Dict, Optional, Tuple


PERMISOS = (
    "user-library-read "
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-read-private "
    "user-read-email"
)


class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.redirect_uri  = redirect_uri
        self.sp            = None
        self.headers       = None
        self.usuario       = None

    # ------------------------------------------------------------------
    # AUTENTICACIÓN
    # ------------------------------------------------------------------

    def autenticar(self) -> dict:
        """Autentica con Spotify y retorna info del usuario."""
        # Limpiar cache viejo para forzar re-autenticación limpia
        for archivo in os.listdir("."):
            if archivo.startswith(".cache"):
                try:
                    os.remove(archivo)
                except Exception:
                    pass

        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=PERMISOS,
            open_browser=True,
            cache_path=".spotify_token"
        )

        self.sp      = spotipy.Spotify(auth_manager=auth_manager)
        self.usuario = self.sp.current_user()

        token = auth_manager.get_cached_token()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        return self.usuario

    def _renovar_headers(self):
        """Renueva el token si está por vencer."""
        try:
            token = self.sp.auth_manager.get_access_token(as_dict=False)
            self.headers["Authorization"] = f"Bearer {token}"
        except Exception:
            pass

    # ------------------------------------------------------------------
    # BIBLIOTECA
    # ------------------------------------------------------------------

    def obtener_biblioteca(self, callback: Callable = None) -> List[dict]:
        """Obtiene todas las canciones guardadas del usuario."""
        self._renovar_headers()
        canciones = []
        pais      = self.usuario.get("country", "US")

        resultado = self.sp.current_user_saved_tracks(limit=50, market=pais)
        total     = resultado["total"]
        canciones.extend(resultado["items"])

        while resultado["next"]:
            resultado = self.sp.next(resultado)
            canciones.extend(resultado["items"])
            if callback:
                prog = len(canciones) / total
                callback(prog * 0.4, f"Descargando biblioteca: {len(canciones)}/{total}")

        return canciones

    def obtener_generos_artistas_lote(self, artist_ids: List[str]) -> Dict[str, List[str]]:
        """Obtiene géneros de artistas usando la REST API directamente."""
        self._renovar_headers()
        resultado = {}

        for i in range(0, len(artist_ids), 50):
            lote = artist_ids[i:i + 50]
            try:
                resp = requests.get(
                    f"https://api.spotify.com/v1/artists?ids={','.join(lote)}",
                    headers=self.headers,
                    timeout=10
                )
                if resp.status_code == 200:
                    for artista in resp.json().get("artists", []):
                        if artista:
                            resultado[artista["id"]] = artista.get("genres", [])
                elif resp.status_code == 403:
                    # En modo desarrollo este endpoint puede estar bloqueado
                    print(f"SPOTIFY: /artists bloqueado (403) - se usará LastFM como respaldo")
                    break
            except Exception as e:
                print(f"SPOTIFY: Error en lote artistas: {e}")
            time.sleep(0.1)

        return resultado

    def obtener_audio_features_lote(self, track_ids: List[str]) -> Dict[str, dict]:
        """Obtiene audio features de canciones en lote."""
        self._renovar_headers()
        resultado = {}

        for i in range(0, len(track_ids), 100):
            lote = track_ids[i:i + 100]
            try:
                resp = requests.get(
                    f"https://api.spotify.com/v1/audio-features?ids={','.join(lote)}",
                    headers=self.headers,
                    timeout=10
                )
                if resp.status_code == 200:
                    for feat in resp.json().get("audio_features", []):
                        if feat:
                            resultado[feat["id"]] = feat
            except Exception as e:
                print(f"SPOTIFY: Error audio features: {e}")

        return resultado

    # ------------------------------------------------------------------
    # BÚSQUEDA
    # ------------------------------------------------------------------

    def buscar_artista(self, nombre: str) -> List[dict]:
        """Busca artistas por nombre en Spotify."""
        self._renovar_headers()
        try:
            resultado = self.sp.search(q=nombre, type="artist", limit=5)
            return resultado["artists"]["items"]
        except Exception as e:
            print(f"SPOTIFY: Error búsqueda artista: {e}")
            return []

    def obtener_canciones_artista_spotify(
        self, artist_id: str, cantidad: int = 50, callback: Callable = None
    ) -> List[str]:
        """
        Obtiene URIs de canciones de un artista desde toda la discografía en Spotify.
        Recorre álbumes → canciones, eliminando duplicados.
        """
        self._renovar_headers()
        uris_unicos = []
        nombres_vistos = set()

        try:
            # Obtenemos álbumes del artista
            albumes = []
            resp = self.sp.artist_albums(
                artist_id, album_type="album,single", limit=50
            )
            albumes.extend(resp["items"])
            while resp["next"] and len(albumes) < 200:
                resp = self.sp.next(resp)
                albumes.extend(resp["items"])

            total_albumes = len(albumes)
            for idx, album in enumerate(albumes):
                if len(uris_unicos) >= cantidad:
                    break

                tracks_resp = self.sp.album_tracks(album["id"], limit=50)
                for track in tracks_resp["items"]:
                    nombre_norm = track["name"].lower().strip()
                    if nombre_norm not in nombres_vistos:
                        nombres_vistos.add(nombre_norm)
                        uris_unicos.append(track["uri"])

                if callback:
                    prog = (idx + 1) / total_albumes
                    callback(prog, f"Explorando discografía: {idx+1}/{total_albumes} álbumes")

                time.sleep(0.05)

        except Exception as e:
            print(f"SPOTIFY: Error obteniendo canciones del artista: {e}")

        return uris_unicos[:cantidad]

    def filtrar_biblioteca_por_artista(
        self, canciones_biblioteca: List[dict], nombre_artista: str
    ) -> List[str]:
        """Filtra la biblioteca guardada por nombre de artista."""
        nombre_lower = nombre_artista.lower()
        uris = []
        for item in canciones_biblioteca:
            track = item.get("track")
            if not track or not track.get("uri", "").startswith("spotify:track:"):
                continue
            for artista in track.get("artists", []):
                if nombre_lower in artista["name"].lower():
                    uris.append(track["uri"])
                    break
        return uris

    # ------------------------------------------------------------------
    # PLAYLISTS
    # ------------------------------------------------------------------

    def obtener_playlists_usuario(self) -> Dict[str, str]:
        """Retorna {nombre: id} de playlists del usuario."""
        self._renovar_headers()
        playlists = {}
        url = "https://api.spotify.com/v1/me/playlists?limit=50"

        while url:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                break
            datos = resp.json()
            for pl in datos.get("items", []):
                if pl and pl.get("owner", {}).get("id") == self.usuario["id"]:
                    playlists[pl["name"]] = pl["id"]
            url = datos.get("next")

        return playlists

    def crear_playlist(self, nombre: str, descripcion: str = "") -> Optional[str]:
        """Crea una playlist nueva usando /me/playlists (funciona en modo dev)."""
        self._renovar_headers()
        try:
            resp = requests.post(
                "https://api.spotify.com/v1/me/playlists",
                headers=self.headers,
                json={
                    "name": nombre,
                    "public": False,
                    "description": descripcion or f"Creada por SyncNode 2.0"
                },
                timeout=10
            )
            if resp.status_code in (200, 201):
                return resp.json()["id"]
            print(f"SPOTIFY: Error creando playlist {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"SPOTIFY: Error crear playlist: {e}")
        return None

    def vaciar_playlist(self, playlist_id: str):
        """Elimina todas las canciones de una playlist."""
        self._renovar_headers()
        uris = []
        url  = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"

        while url:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                break
            datos = resp.json()
            for item in datos.get("items", []):
                if item.get("track") and item["track"].get("uri"):
                    uris.append({"uri": item["track"]["uri"]})
            url = datos.get("next")

        for i in range(0, len(uris), 100):
            requests.delete(
                f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
                headers=self.headers,
                json={"tracks": uris[i:i + 100]},
                timeout=10
            )

    def agregar_canciones(
        self, playlist_id: str, uris: List[str], callback: Callable = None
    ):
        """Agrega canciones a una playlist en lotes de 100."""
        self._renovar_headers()
        total = len(uris)

        for i in range(0, total, 100):
            lote = uris[i:i + 100]
            resp = requests.post(
                f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
                headers=self.headers,
                json={"uris": lote},
                timeout=10
            )
            if callback:
                callback(
                    min((i + len(lote)) / total, 1.0),
                    f"Subiendo canciones: {min(i + 100, total)}/{total}"
                )
            time.sleep(0.1)

    def crear_o_actualizar_playlist(
        self,
        nombre: str,
        uris: List[str],
        playlists_existentes: Dict[str, str],
        forzar_nueva: bool = False,
        callback: Callable = None
    ) -> Optional[str]:
        """Crea o actualiza una playlist con las URIs dadas."""
        nombre_completo = f"SyncNode | {nombre}"

        if nombre_completo in playlists_existentes and not forzar_nueva:
            pl_id = playlists_existentes[nombre_completo]
            self.vaciar_playlist(pl_id)
            self.agregar_canciones(pl_id, uris, callback)
            return pl_id

        pl_id = self.crear_playlist(nombre_completo)
        if pl_id:
            self.agregar_canciones(pl_id, uris, callback)
        return pl_id
