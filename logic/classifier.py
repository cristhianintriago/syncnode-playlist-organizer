import json
import os
from collections import defaultdict
from typing import List, Dict, Optional, Tuple


class Clasificador:
    def __init__(self, ruta_json: str = None):
        if ruta_json is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_json = os.path.join(base, "config", "genres.json")

        with open(ruta_json, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.tags_ignorar  = set(cfg["tags_ignorar"])
        self.genre_map     = cfg["genre_map"]
        self.audio_rules   = cfg["audio_features_rules"]
        lang_cfg           = cfg["language"]
        self.subdividir    = set(lang_cfg["subdivide_genres"])
        self.min_tracks    = lang_cfg["min_tracks"]
        self.spanish_tags  = set(lang_cfg["spanish_tags"])
        self.english_tags  = set(lang_cfg["english_tags"])

    # ------------------------------------------------------------------
    # CLASIFICACIÓN DE GÉNERO
    # ------------------------------------------------------------------

    def normalizar_genero(self, genero: str) -> Optional[str]:
        """Convierte un tag a una categoría del genre_map."""
        if not genero or genero.lower() in self.tags_ignorar:
            return None
        g = genero.lower()
        for categoria, palabras in self.genre_map.items():
            for palabra in palabras:
                if palabra in g:
                    return categoria
        return None

    def clasificar_artista(
        self,
        tags_spotify: List[str],
        tags_lastfm: List[str]
    ) -> Tuple[Optional[str], str]:
        """
        Clasifica un artista usando votos ponderados.
        Spotify tiene peso 2, LastFM peso 1.
        Retorna (genero, idioma).
        """
        votos_genero = defaultdict(float)
        votos_idioma = defaultdict(int)

        # Tags de Spotify (peso 2)
        idioma_spotify = self._idioma_por_spotify(tags_spotify)
        if idioma_spotify:
            votos_idioma[idioma_spotify] += 2

        for tag in tags_spotify:
            cat = self.normalizar_genero(tag)
            if cat:
                votos_genero[cat] += 2

        # Tags de LastFM (peso 1)
        for tag in tags_lastfm:
            cat = self.normalizar_genero(tag)
            if cat:
                votos_genero[cat] += 1
            tag_l = tag.lower()
            if tag_l in self.spanish_tags:
                votos_idioma["es"] += 1
            elif tag_l in self.english_tags:
                votos_idioma["en"] += 1

        genero = max(votos_genero, key=votos_genero.get) if votos_genero else None
        idioma = max(votos_idioma, key=votos_idioma.get) if votos_idioma else "en"

        return genero, idioma

    def clasificar_por_audio(self, features: dict) -> str:
        """Clasifica una canción por audio features como último recurso."""
        if not features:
            return "Otros"

        d   = features.get("danceability", 0)
        e   = features.get("energy", 0)
        v   = features.get("valence", 0)
        t   = features.get("tempo", 0)

        puntos = defaultdict(float)

        rules = self.audio_rules
        if e >= rules["Electrónica / Dance"].get("energy_min", 0) and \
           d >= rules["Electrónica / Dance"].get("danceability_min", 0):
            puntos["Electrónica / Dance"] += 2

        if d >= rules["Reggaeton / Latin"].get("danceability_min", 0) and \
           rules["Reggaeton / Latin"].get("tempo_min", 0) <= t <= rules["Reggaeton / Latin"].get("tempo_max", 999):
            puntos["Reggaeton / Latin"] += 2

        if e >= rules["Rock"].get("energy_min", 0) and \
           t >= rules["Rock"].get("tempo_min", 0):
            puntos["Rock"] += 2

        if v <= rules["R&B / Soul"].get("valence_max", 1) and \
           e <= rules["R&B / Soul"].get("energy_max", 1):
            puntos["R&B / Soul"] += 2

        # Reglas adicionales basadas en combinaciones
        puntos["Hip Hop / Rap"] += d * 0.8 + (1 - e) * 0.5
        if 70 <= t <= 110:
            puntos["Hip Hop / Rap"] += 0.8

        if puntos:
            mejor = max(puntos, key=puntos.get)
            if puntos[mejor] > 1.0:
                return mejor

        return "Otros"

    # ------------------------------------------------------------------
    # IDIOMA
    # ------------------------------------------------------------------

    def _idioma_por_spotify(self, generos: List[str]) -> Optional[str]:
        indicadores_es = [
            "latin", "reggaeton", "español", "mexicano", "colombian",
            "chilean", "argentinian", "trap latino", "latin trap",
            "urbano", "tropical", "bachata", "cumbia", "salsa"
        ]
        for g in generos:
            g_l = g.lower()
            for ind in indicadores_es:
                if ind in g_l:
                    return "es"
        return None

    # ------------------------------------------------------------------
    # GÉNERO FINAL CON IDIOMA
    # ------------------------------------------------------------------

    def genero_con_idioma(self, genero: Optional[str], idioma: str) -> str:
        """Agrega bandera si el género debe subdividirse por idioma."""
        if not genero:
            return "Otros"
        if genero in self.subdividir:
            if idioma == "es":
                return f"{genero} 🇪🇸"
            return f"{genero} 🇺🇸"
        return genero

    def fusionar_grupos_pequenos(
        self, grupos: Dict[str, list]
    ) -> Dict[str, list]:
        """Fusiona subdivisiones con pocos tracks al género base."""
        resultado = defaultdict(list)
        for genero, items in grupos.items():
            es_sub = genero.endswith(" 🇪🇸") or genero.endswith(" 🇺🇸")
            if es_sub and len(items) < self.min_tracks:
                base = genero.rsplit(" ", 1)[0]
                resultado[base].extend(items)
            else:
                resultado[genero].extend(items)
        return dict(resultado)
