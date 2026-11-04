import json

import requests


GITHUB_USERNAME = "volcano444"
REPO_NAME = "fluxx-keys"
BRANCH = "main"

CONFIG_FILES = {
    "endpoints": "config/endpoints.json",
    "api_keys": "config/api_keys.json",
}


def _fetch_json_file(token, file_path, timeout=15):
    url = (
        f"https://api.github.com/repos/{GITHUB_USERNAME}/"
        f"{REPO_NAME}/contents/{file_path}?ref={BRANCH}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
        )

        if response.status_code == 401:
            raise RuntimeError("GitHub token tidak valid.")

        if response.status_code == 403:
            raise RuntimeError(
                "Akses GitHub ditolak. Periksa izin token atau rate limit."
            )

        if response.status_code == 404:
            raise RuntimeError(
                f"File {file_path} tidak ditemukan atau tidak dapat diakses."
            )

        response.raise_for_status()
        if len(response.content) > 2_000_000:
            raise RuntimeError(
                f"File {file_path} melebihi batas ukuran 2 MB."
            )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"Format JSON pada {file_path} tidak valid."
            ) from None

    except requests.Timeout:
        raise RuntimeError("Koneksi GitHub timeout.") from None

    except requests.RequestException:
        raise RuntimeError(
            f"Gagal mengambil file {file_path} dari GitHub."
        ) from None


def fetch_remote_config(token, timeout=15):
    if not token:
        raise RuntimeError(
            "FLUXX_GITHUB_TOKEN belum dikonfigurasi."
        )

    endpoints = _fetch_json_file(
        token,
        CONFIG_FILES["endpoints"],
        timeout,
    )

    api_keys = _fetch_json_file(
        token,
        CONFIG_FILES["api_keys"],
        timeout,
    )

    if not isinstance(endpoints, dict):
        raise RuntimeError(
            "endpoints.json harus berisi JSON object."
        )

    if not isinstance(api_keys, dict):
        raise RuntimeError(
            "api_keys.json harus berisi JSON object."
        )

    if not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in api_keys.items()
    ):
        raise RuntimeError(
            "Format API Key harus berupa pasangan string."
        )

    allowed_api_keys = {
        "npsn_api_key",
        "locate_api_key",
        "airport_api_key",
        "spotify_api_key",
        "tempmail_api_key",
    }

    return {
        "endpoints": endpoints,
        "api_keys": {
            key: value.strip()
            for key, value in api_keys.items()
            if key in allowed_api_keys and value.strip()
        },
    }
