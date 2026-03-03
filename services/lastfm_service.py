import pylast
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Dict, Callable


class LastFMService:
    def __init__(self, api_key: str, max_workers: int = 10):
        self.api_key     = api_key
        self.max_workers = max_workers
        self._red        = pylast.LastFMNetwork(api_key=api_key)
        self._cache: Dict[str, Tuple[List[str], str]] = {}

    def consultar_artista(self, nombre: str) -> Tuple[List[str], str]:
        """Retorna (tags, idioma) para un artista."""
        if nombre in self._cache:
            return self._cache[nombre]

        try:
            artista = self._red.get_artist(nombre)
            tags    = artista.get_top_tags(limit=10)
            tags_lower = [t.item.get_name().lower() for t in tags]

            idioma = self._deducir_idioma(tags_lower)
            resultado = (tags_lower, idioma)
            self._cache[nombre] = resultado
            return resultado
        except Exception:
            pass

        resultado = ([], "en")
        self._cache[nombre] = resultado
        return resultado

    def consultar_lote(
        self, nombres: List[str], callback: Callable = None
    ) -> Dict[str, Tuple[List[str], str]]:
        """Consulta múltiples artistas en paralelo."""
        resultados = {}
        total      = len(nombres)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.consultar_artista, nombre): nombre
                for nombre in nombres
            }
            completados = 0
            for future in as_completed(futures):
                nombre          = futures[future]
                resultados[nombre] = future.result()
                completados    += 1
                if callback:
                    callback(completados / total, f"LastFM: {completados}/{total} artistas")

        return resultados

    def _deducir_idioma(self, tags: List[str]) -> str:
        indicadores_es = {
            "spanish", "en español", "en espanol", "latino", "latina",
            "hispanico", "habla hispana", "mexican", "colombian",
            "argentinian", "chilean", "peruvian", "venezuelan",
            "ecuadorian", "dominican", "puerto rican", "cuban",
            "spanish rap", "spanish hip hop", "trap en español",
            "rap en español", "musica urbana", "urbano", "trap latino",
            "rock en español", "pop en español", "indie en español"
        }
        indicadores_en = {
            "english", "british", "american", "usa", "uk", "canadian",
            "australian", "american rapper", "british rapper",
            "english rap", "american hip hop", "american rock",
            "american pop", "us rap", "uk rap"
        }
        for tag in tags:
            if tag in indicadores_es:
                return "es"
            if tag in indicadores_en:
                return "en"
        return "en"

    def limpiar_cache(self):
        self._cache.clear()
