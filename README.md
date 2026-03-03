# ◈ SyncNode 2.0

> Organiza tu biblioteca de Spotify inteligentemente por géneros y artistas.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-gold?style=flat-square)
![Spotify](https://img.shields.io/badge/API-Spotify-1DB954?style=flat-square)

---

## ¿Qué hace?

SyncNode analiza tu biblioteca de Spotify y crea playlists organizadas automáticamente usando tres estrategias de clasificación:

1. **Géneros de Spotify** — datos directos de la API
2. **LastFM** — tags de la comunidad como respaldo
3. **Audio Features** — energía, tempo y danceability como último recurso

También puedes buscar cualquier artista y crear una playlist con toda su discografía en segundos.

---

## Características

- 🎵 Organización por género con subdivisión por idioma (🇪🇸 / 🇺🇸)
- 🎤 Búsqueda de artistas en todo Spotify o en tu biblioteca personal
- 📊 Estadísticas visuales con barras animadas y top artistas
- ✨ Pantalla de carga animada con partículas
- 💾 Caché en disco para no repetir llamadas a la API
- 🎨 Interfaz premium oscura con acento dorado

---

## Instalación

### 1. Clona el repositorio

```bash
git clone https://github.com/tu-usuario/syncnode.git
cd syncnode
```

### 2. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 3. Configura tus credenciales

Al ejecutar por primera vez se genera un `config.json` automáticamente. Complétalo con tus credenciales:

```json
{
  "client_id":      "TU_CLIENT_ID",
  "client_secret":  "TU_CLIENT_SECRET",
  "redirect_uri":   "http://127.0.0.1:8888/callback",
  "lastfm_api_key": "TU_KEY_OPCIONAL"
}
```

#### ¿Dónde consigo las credenciales?

| Credencial | Dónde obtenerla |
|---|---|
| `client_id` y `client_secret` | [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) → Crear app |
| `lastfm_api_key` | [last.fm/api/account/create](https://www.last.fm/api/account/create) — gratis e instantáneo |

> ⚠️ En el Spotify Dashboard asegúrate de agregar `http://127.0.0.1:8888/callback` como Redirect URI en Settings.

### 4. Ejecuta

```bash
python main.py
```

---

## Estructura del proyecto

```
syncnode2/
├── main.py                  # Punto de entrada
├── config.json              # Credenciales (no subir a GitHub)
├── config/
│   └── genres.json          # Mapa de géneros y reglas
├── services/
│   ├── spotify_service.py   # Comunicación con la API de Spotify
│   └── lastfm_service.py    # Comunicación con la API de LastFM
├── logic/
│   ├── classifier.py        # Motor de clasificación de géneros
│   └── organizer.py         # Lógica de organización y creación de playlists
└── ui/
    └── main_window.py       # Interfaz gráfica completa
```

---

## Requisitos

- Python 3.10 o superior
- Cuenta de Spotify (Free o Premium)
- App registrada en Spotify Developer Dashboard

---

## .gitignore recomendado

```
config.json
.spotify_token
artist_cache.json
.cache*
__pycache__/
*.pyc
```

---

## Licencia

MIT — úsalo, modifícalo y compártelo libremente.
