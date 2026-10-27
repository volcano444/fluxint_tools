import json
import os
import re
from urllib.parse import urlparse

import requests


class APIClientError(Exception):
    pass


def _safe_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise APIClientError("URL endpoint harus berupa URL HTTP/HTTPS yang valid.")
    if parsed.username or parsed.password:
        raise APIClientError("Jangan menaruh username/password di URL endpoint.")
    return url



def _replace_templates(value, variables):
    if isinstance(value, str):
        for key, replacement in variables.items():
            value = value.replace(
                "{" + key + "}",
                str(replacement)
            )
        return value

    if isinstance(value, list):
        return [
            _replace_templates(item, variables)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: _replace_templates(item, variables)
            for key, item in value.items()
        }

    return value

def request_api(endpoint, query, settings, extra_variables=None):
    if not endpoint.get("enabled", False):
        raise APIClientError(
            "Menu ini belum aktif / dalam pemeliharan."
        )

    url = _safe_url(str(endpoint.get("url", "")).strip())
    method = str(endpoint.get("method", "GET")).upper()

    if method not in {"GET", "POST"}:
        raise APIClientError("Method yang didukung hanya GET dan POST.")

    variables = {"query": query}
    if extra_variables:
        variables.update(extra_variables)

    if "|" in query:
        player_id, zone_id = query.split("|", 1)
        variables["id"] = player_id.strip()
        variables["zone"] = zone_id.strip()

    params = _replace_templates(
        endpoint.get("params", {}),
        variables
    )

    body = _replace_templates(
        endpoint.get("json", {}),
        variables
    )

    headers = {
        "Accept": "application/json",
        "User-Agent": "FluxxAPI/0.1",
    }


    # Optional authentication conventions. Adjust to match your provider.
    auth_mode = endpoint.get("auth", "none")
    if auth_mode == "api_key":
        key_name = endpoint.get("api_key_setting", "api_key")
        key = settings.get(key_name, "")
        if not key:
            raise APIClientError("FLUXX_API_KEY belum diisi pada file .env.")
        headers[str(endpoint.get("auth_header", "X-API-Key"))] = key
    elif auth_mode == "bearer":
        token = settings["api_token"]
        if not token:
            raise APIClientError("FLUXX_API_TOKEN belum diisi pada file .env.")
        headers["Authorization"] = f"Bearer {token}"
    elif auth_mode == "session":
        key = settings["session_key"]
        if not key:
            raise APIClientError("FLUXX_SESSION_KEY belum diisi pada file .env.")
        headers[str(endpoint.get("auth_header", "X-Session-Key"))] = key
    elif auth_mode != "none":
        raise APIClientError("Mode auth tidak dikenal. Gunakan none, api_key, bearer, atau session.")

    try:
        with requests.Session() as session:
            response = session.request(
                method,
                url,
                params=params if method == "GET" else None,
                json=body if method == "POST" else None,
                headers=headers,
                timeout=settings["timeout"],
                allow_redirects=False,
                stream=True,
            )
            if 300 <= response.status_code < 400:
                response.close()
                raise APIClientError("Redirect ditolak untuk keamanan. Periksa URL endpoint.")
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(chunk_size=16384):
                size += len(chunk)
                if size > settings["max_response_bytes"]:
                    response.close()
                    raise APIClientError("Respons melebihi batas ukuran yang diizinkan.")
                chunks.append(chunk)
            raw = b"".join(chunks)
            content_type = response.headers.get("Content-Type", "")
            status_code = response.status_code
            response.close()
    except requests.Timeout as exc:
        raise APIClientError("Request timeout. Coba lagi atau naikkan FLUXX_TIMEOUT.") from exc
    except requests.RequestException as exc:
        raise APIClientError(f"Request API gagal: {exc}") from exc

    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {
            "ok": False,
            "message": "Respons bukan JSON valid. Periksa endpoint atau dokumentasi API.",
            "content_type": content_type,
            "body_preview": text[:1000],
        }

    return {
        "tool": endpoint.get("label", "API"),
        "http_status": status_code,
        "ok": 200 <= status_code < 300,
        "data": data,
    }
