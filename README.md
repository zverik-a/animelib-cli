# CLii

A small terminal client for searching anime, browsing episode sources, and opening a selected video in [mpv](https://mpv.io/).

## Requirements

- Python 3.10 or newer
- `mpv` installed and available on `PATH`
- Access to the HentaiCDN API and media hosts

## Install

```sh
git clone <repository-url>
cd CLii
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

## Configure

The client reads an optional API bearer token from `ANIMELIB_BEARER_TOKEN`. Copy `.env.example` as a reference and export the variable in your shell; this project does not load `.env` files automatically.

```sh
export ANIMELIB_BEARER_TOKEN="your-token"
```

If the API does not require authentication, leave it unset. Never commit a real token. The API endpoint can be overridden with `ANIMELIB_API_URL`.

## Run

```sh
python main.py "anime title"
```

Omit the title to be prompted interactively:

```sh
python main.py
```

Choose a title, open its episode list, select a source and quality, and the client launches `mpv`. Use `Ctrl+C` to exit.

## Notes

- This is an unofficial community client and is not affiliated with the API or media providers.
- Availability, authentication requirements, and media URLs depend on third-party services and may change.
- No license is included yet. Choose a license before publishing if you want to grant others explicit reuse rights.
