import os
import json
import time
import threading
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Dict, Optional, Tuple

# Límites en modo prueba (menos llamadas a la API de Spotify)
MP_BIBLIO_MAX = 120
MP_ARTIST_ALBUMS_MAX = 24
MP_ARTIST_TRACKS_MAX = 40
MP_BUSQUEDA_ARTISTAS = 3


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
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        modo_prueba: bool = False,
    ):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.redirect_uri  = redirect_uri
        self.modo_prueba   = modo_prueba
        self.sp            = None
        self.headers       = None
        self.usuario       = None
        self._req_lock     = threading.Lock()

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

        limite = MP_BIBLIO_MAX if self.modo_prueba else None

        resultado = self.sp.current_user_saved_tracks(limit=50, market=pais)
        total     = resultado["total"]
        if limite is not None:
            total = min(total, limite)
        canciones.extend(resultado["items"])

        while resultado["next"] and (limite is None or len(canciones) < limite):
            resultado = self.sp.next(resultado)
            chunk = resultado["items"]
            if limite is not None:
                rest = limite - len(canciones)
                chunk = chunk[:rest]
            canciones.extend(chunk)
            if callback:
                prog = len(canciones) / max(total, 1)
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
        lim = MP_BUSQUEDA_ARTISTAS if self.modo_prueba else 8
        try:
            resultado = self.sp.search(q=nombre, type="artist", limit=lim)
            return resultado["artists"]["items"]
        except Exception as e:
            print(f"SPOTIFY: Error búsqueda artista: {e}")
            return []

    def _album_tracks_rest(self, album_id: str) -> List[dict]:
        """Tracks de un álbum vía REST (uso concurrente con lock en headers)."""
        items: List[dict] = []
        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?limit=50"
        while url:
            with self._req_lock:
                self._renovar_headers()
                resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                break
            datos = resp.json()
            items.extend(datos.get("items", []))
            url = datos.get("next")
        return items

    @staticmethod
    def _track_uri(track: dict) -> Optional[str]:
        u = track.get("uri")
        if u:
            return u
        tid = track.get("id")
        return f"spotify:track:{tid}" if tid else None

    def obtener_canciones_artista_spotify(
        self, artist_id: str, cantidad: int = 50, callback: Callable = None
    ) -> List[str]:
        """
        URIs de canciones del artista (álbumes + singles, sin duplicados por título).
        Fuera de modo prueba usa varias peticiones en paralelo para acelerar.
        """
        self._renovar_headers()
        if self.modo_prueba:
            cantidad = min(cantidad, MP_ARTIST_TRACKS_MAX)

        uris_unicos: List[str] = []
        nombres_vistos = set()
        state = threading.Lock()

        try:
            albumes_max = MP_ARTIST_ALBUMS_MAX if self.modo_prueba else 200
            albumes: List[dict] = []
            resp = self.sp.artist_albums(
                artist_id, album_type="album,single", limit=50
            )
            albumes.extend(resp["items"])
            while resp["next"] and len(albumes) < albumes_max:
                resp = self.sp.next(resp)
                albumes.extend(resp["items"])
            albumes = albumes[:albumes_max]
            total_albumes = len(albumes)
            if total_albumes == 0:
                return []

            def incorporar(tracks: List[dict]) -> bool:
                """True si ya se alcanzó cantidad."""
                with state:
                    for track in tracks:
                        if len(uris_unicos) >= cantidad:
                            return True
                        nombre_norm = track["name"].lower().strip()
                        if nombre_norm in nombres_vistos:
                            continue
                        uri = self._track_uri(track)
                        if not uri:
                            continue
                        nombres_vistos.add(nombre_norm)
                        uris_unicos.append(uri)
                    return len(uris_unicos) >= cantidad

            def uno(album: dict) -> None:
                tracks = self._album_tracks_rest(album["id"])
                incorporar(tracks)

            workers = 1 if self.modo_prueba else min(4, total_albumes)
            if workers <= 1:
                for idx, album in enumerate(albumes):
                    if incorporar(self._album_tracks_rest(album["id"])):
                        break
                    if callback:
                        callback(
                            (idx + 1) / total_albumes,
                            f"Explorando discografía: {idx+1}/{total_albumes} álbumes",
                        )
            else:
                hecho = [0]

                def worker(album: dict):
                    uno(album)
                    with state:
                        hecho[0] += 1
                        h = hecho[0]
                    if callback:
                        callback(
                            h / total_albumes,
                            f"Explorando discografía: {h}/{total_albumes} álbumes",
                        )

                with ThreadPoolExecutor(max_workers=workers) as ex:
                    list(ex.map(worker, albumes))

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
                    "description": descripcion or "Creada con SyncNode (Klyro)"
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
