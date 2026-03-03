import json
import os
from collections import defaultdict
from typing import Dict, List, Callable, Optional, Tuple

from logic.classifier import Clasificador
from services.spotify_service import SpotifyService
from services.lastfm_service import LastFMService


CACHE_FILE = "artist_cache.json"


class MotorOrganizacion:
    def __init__(
        self,
        spotify: SpotifyService,
        lastfm: Optional[LastFMService],
        clasificador: Clasificador
    ):
        self.spotify      = spotify
        self.lastfm       = lastfm
        self.clasificador = clasificador
        self.biblioteca   = []          # Items crudos de Spotify
        self.cache_disco  = self._cargar_cache()
        self.grupos       = {}          # {genero: [(uri, tid, artista)]}

    # ------------------------------------------------------------------
    # CACHE EN DISCO
    # ------------------------------------------------------------------

    def _cargar_cache(self) -> dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                print(f"CACHE: {len(datos)} artistas cargados desde disco")
                return datos
            except Exception:
                pass
        return {}

    def _guardar_cache(self):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache_disco, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"CACHE: Error guardando: {e}")

    # ------------------------------------------------------------------
    # CARGA DE BIBLIOTECA
    # ------------------------------------------------------------------

    def cargar_biblioteca(self, callback: Callable = None) -> int:
        """Carga la biblioteca del usuario desde Spotify."""
        if callback:
            callback(0.0, "Conectando con Spotify...")
        self.biblioteca = self.spotify.obtener_biblioteca(callback)
        return len(self.biblioteca)

    # ------------------------------------------------------------------
    # CLASIFICACIÓN
    # ------------------------------------------------------------------

    def clasificar(self, callback: Callable = None) -> Dict[str, list]:
        """
        Clasifica toda la biblioteca en géneros.
        Estrategia: Spotify genres → LastFM tags → Audio Features
        """
        # Recopilar artistas únicos
        datos_artistas = {}
        for item in self.biblioteca:
            track = item.get("track")
            if not track:
                continue
            for a in track.get("artists", []):
                if a["name"] not in datos_artistas:
                    datos_artistas[a["name"]] = a["id"]

        total_artistas = len(datos_artistas)
        if callback:
            callback(0.4, f"Analizando {total_artistas} artistas únicos...")

        # PASO 1: Géneros de Spotify
        ids_sin_cache = [
            aid for nombre, aid in datos_artistas.items()
            if nombre not in self.cache_disco
        ]
        nombre_por_id = {v: k for k, v in datos_artistas.items()}

        generos_spotify = {}
        if ids_sin_cache:
            generos_spotify = self.spotify.obtener_generos_artistas_lote(ids_sin_cache)

        sin_genero = []
        for nombre, aid in datos_artistas.items():
            if nombre in self.cache_disco:
                continue
            tags_spotify = generos_spotify.get(aid, [])
            if tags_spotify:
                genero, idioma = self.clasificador.clasificar_artista(tags_spotify, [])
                self.cache_disco[nombre] = {"genre": genero, "lang": idioma}
            else:
                sin_genero.append(nombre)

        if callback:
            callback(0.55, f"Spotify clasificó {total_artistas - len(sin_genero)} artistas")

        # PASO 2: LastFM para los que no tienen género
        if sin_genero and self.lastfm:
            completados = [0]
            def cb_lastfm(prog, msg):
                completados[0] = int(prog * len(sin_genero))
                if callback:
                    callback(0.55 + prog * 0.25, msg)

            resultados_lastfm = self.lastfm.consultar_lote(sin_genero, cb_lastfm)
            aun_sin_genero = []

            for nombre, (tags_lf, idioma_lf) in resultados_lastfm.items():
                tags_spotify = generos_spotify.get(datos_artistas.get(nombre, ""), [])
                genero, idioma = self.clasificador.clasificar_artista(tags_spotify, tags_lf)
                self.cache_disco[nombre] = {
                    "genre": genero,
                    "lang":  idioma_lf if not idioma else idioma
                }
                if not genero:
                    aun_sin_genero.append(nombre)

            sin_genero = aun_sin_genero

        self._guardar_cache()

        if callback:
            callback(0.80, "Agrupando canciones...")

        # PASO 3: Agrupar canciones
        grupos_raw     = defaultdict(list)
        necesitan_audio = []

        for item in self.biblioteca:
            track = item.get("track")
            if not track or not track.get("uri", "").startswith("spotify:track:"):
                continue

            uri    = track["uri"]
            tid    = track["id"]
            nombre = track.get("name", "")
            artistas = track.get("artists", [])

            votos_genero = defaultdict(float)
            votos_idioma = defaultdict(int)

            for a in artistas:
                datos = self.cache_disco.get(a["name"], {})
                g = datos.get("genre") if isinstance(datos, dict) else datos
                l = datos.get("lang", "en") if isinstance(datos, dict) else "en"
                if g:
                    votos_genero[g] += 1
                if l:
                    votos_idioma[l] += 1

            nombre_artista = artistas[0]["name"] if artistas else ""

            if votos_genero:
                mejor_g = max(votos_genero, key=votos_genero.get)
                mejor_l = max(votos_idioma, key=votos_idioma.get) if votos_idioma else "en"
                genero_final = self.clasificador.genero_con_idioma(mejor_g, mejor_l)
                grupos_raw[genero_final].append((uri, tid, nombre_artista))
            else:
                necesitan_audio.append((uri, tid, nombre, nombre_artista))

        # PASO 4: Audio features para los sin género
        if necesitan_audio:
            if callback:
                callback(0.85, f"Audio features para {len(necesitan_audio)} canciones...")

            ids_audio    = [tid for _, tid, _, _ in necesitan_audio]
            feats        = self.spotify.obtener_audio_features_lote(ids_audio)

            for uri, tid, nombre_cancion, nombre_artista in necesitan_audio:
                cat    = self.clasificador.clasificar_por_audio(feats.get(tid))
                grupos_raw[cat].append((uri, tid, nombre_artista))

        # Fusionar grupos pequeños
        self.grupos = self.clasificador.fusionar_grupos_pequenos(dict(grupos_raw))

        if callback:
            callback(1.0, f"¡Clasificación completa! {len(self.grupos)} géneros encontrados")

        return self.grupos

    # ------------------------------------------------------------------
    # ESTADÍSTICAS
    # ------------------------------------------------------------------

    def calcular_estadisticas(self) -> dict:
        """Calcula estadísticas de la biblioteca clasificada."""
        total     = sum(len(v) for v in self.grupos.values())
        if total == 0:
            return {}

        # Top géneros
        generos_ordenados = sorted(
            self.grupos.items(), key=lambda x: len(x[1]), reverse=True
        )

        # Top artistas
        conteo_artistas = defaultdict(int)
        for items in self.grupos.values():
            for _, _, artista in items:
                if artista:
                    conteo_artistas[artista] += 1

        top_artistas = sorted(
            conteo_artistas.items(), key=lambda x: -x[1]
        )[:10]

        # Distribución idioma
        es = sum(len(v) for k, v in self.grupos.items() if "🇪🇸" in k)
        en = sum(len(v) for k, v in self.grupos.items() if "🇺🇸" in k)
        otros_idioma = total - es - en

        return {
            "total":           total,
            "total_generos":   len(self.grupos),
            "generos":         [(g, len(v)) for g, v in generos_ordenados],
            "top_artistas":    top_artistas,
            "idioma_es":       es,
            "idioma_en":       en,
            "idioma_otros":    otros_idioma,
        }

    # ------------------------------------------------------------------
    # BÚSQUEDA POR ARTISTA EN BIBLIOTECA
    # ------------------------------------------------------------------

    def buscar_en_biblioteca(self, nombre: str) -> List[str]:
        return self.spotify.filtrar_biblioteca_por_artista(self.biblioteca, nombre)

    # ------------------------------------------------------------------
    # CREACIÓN DE PLAYLISTS
    # ------------------------------------------------------------------

    def crear_playlists_generos(
        self,
        generos_seleccionados: List[str],
        callback: Callable = None
    ):
        playlists = self.spotify.obtener_playlists_usuario()
        total     = len(generos_seleccionados)

        for idx, genero in enumerate(generos_seleccionados):
            if genero not in self.grupos:
                continue

            uris = [uri for uri, _, _ in self.grupos[genero]]
            if not uris:
                continue

            def cb(prog, msg, i=idx):
                if callback:
                    global_prog = (i + prog) / total
                    callback(global_prog, f"[{i+1}/{total}] {msg}")

            self.spotify.crear_o_actualizar_playlist(genero, uris, playlists, callback=cb)

        if callback:
            callback(1.0, f"¡{total} playlists creadas en Spotify!")

    def crear_playlists_artistas(
        self,
        artistas_seleccionados: List[str],
        callback: Callable = None
    ):
        """Crea playlists filtrando por artista desde la biblioteca."""
        playlists = self.spotify.obtener_playlists_usuario()
        total     = len(artistas_seleccionados)

        # Agrupar canciones por artista desde biblioteca
        grupos_artista = defaultdict(list)
        for item in self.biblioteca:
            track = item.get("track")
            if not track or not track.get("uri", "").startswith("spotify:track:"):
                continue
            for a in track.get("artists", []):
                if a["name"] in artistas_seleccionados:
                    grupos_artista[a["name"]].append(track["uri"])

        for idx, artista in enumerate(artistas_seleccionados):
            uris = list(set(grupos_artista.get(artista, [])))
            if not uris:
                continue

            def cb(prog, msg, i=idx):
                if callback:
                    callback((i + prog) / total, f"[{i+1}/{total}] {msg}")

            self.spotify.crear_o_actualizar_playlist(
                artista, uris, playlists, callback=cb
            )

        if callback:
            callback(1.0, "¡Playlists de artistas creadas!")
