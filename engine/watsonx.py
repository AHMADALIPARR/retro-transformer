# SPDX-License-Identifier: AGPL-3.0-or-later
#
# retro-transformer
# Copyright (C) 2026 SnapKitty Collective
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

"""watsonx.ai REST client (stdlib only).

Implements the two calls the transformation engine needs:

1. IAM token exchange -- POST https://iam.cloud.ibm.com/identity/token
   with grant_type=urn:ibm:params:oauth:grant-type:apikey
2. Text generation -- POST https://{region}.ml.cloud.ibm.com/ml/v1/text/generation

Configuration comes from the environment:

    WATSONX_API_KEY      IBM Cloud API key (required for real calls)
    WATSONX_PROJECT_ID   watsonx.ai project id (required for real calls)
    WATSONX_REGION       region, e.g. us-south (default: us-south)
    WATSONX_MODEL_ID     model id (default: ibm/granite-3-8b-instruct)

Transient failures (HTTP 429 / 5xx) are retried with exponential backoff.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
IAM_GRANT_TYPE = "urn:ibm:params:oauth:grant-type:apikey"
GENERATION_API_VERSION = "2023-05-29"

DEFAULT_REGION = "us-south"
DEFAULT_MODEL_ID = "ibm/granite-3-8b-instruct"

MAX_RETRIES = 4
BASE_BACKOFF_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 120
# Refresh the IAM token this far before it actually expires.
TOKEN_EXPIRY_BUFFER_SECONDS = 120


class WatsonxError(Exception):
    """Base error for watsonx.ai client failures."""


class MissingCredentialsError(WatsonxError):
    """Raised when WATSONX_API_KEY / WATSONX_PROJECT_ID are not set."""


class AuthenticationError(WatsonxError):
    """Raised when the IAM token exchange or a call is rejected (401/403)."""


class RateLimitError(WatsonxError):
    """Raised when retries are exhausted on throttling / server errors."""


@dataclass
class WatsonxConfig:
    """Connection settings, resolved from the environment."""

    api_key: str = ""
    project_id: str = ""
    region: str = DEFAULT_REGION
    model_id: str = DEFAULT_MODEL_ID

    @classmethod
    def from_env(cls) -> "WatsonxConfig":
        return cls(
            api_key=os.environ.get("WATSONX_API_KEY", "").strip(),
            project_id=os.environ.get("WATSONX_PROJECT_ID", "").strip(),
            region=os.environ.get("WATSONX_REGION", DEFAULT_REGION).strip()
            or DEFAULT_REGION,
            model_id=os.environ.get("WATSONX_MODEL_ID", DEFAULT_MODEL_ID).strip()
            or DEFAULT_MODEL_ID,
        )

    @property
    def generation_url(self) -> str:
        return (
            f"https://{self.region}.ml.cloud.ibm.com"
            f"/ml/v1/text/generation?version={GENERATION_API_VERSION}"
        )

    def require_credentials(self) -> None:
        missing = [
            name
            for name, value in (
                ("WATSONX_API_KEY", self.api_key),
                ("WATSONX_PROJECT_ID", self.project_id),
            )
            if not value
        ]
        if missing:
            raise MissingCredentialsError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + ". Set them, or run with MOCK=1 for credential-free testing."
            )


class WatsonxClient:
    """Thin watsonx.ai client: IAM auth + text generation with retries."""

    def __init__(self, config: WatsonxConfig | None = None) -> None:
        self.config = config or WatsonxConfig.from_env()
        self.config.require_credentials()
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 2000,
        temperature: float = 0.0,
        stop_sequences: list[str] | None = None,
        decoding_method: str = "greedy",
    ) -> str:
        """Generate text for *prompt* and return the generated text.

        Raises WatsonxError subclasses on auth / transport / API failures.
        """
        body = {
            "model_id": self.config.model_id,
            "input": prompt,
            "parameters": {
                "decoding_method": decoding_method,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "repetition_penalty": 1.0,
            },
            "project_id": self.config.project_id,
        }
        if stop_sequences:
            body["parameters"]["stop_sequences"] = stop_sequences

        payload = self._request_json(
            "POST",
            self.config.generation_url,
            body,
            headers={"Authorization": f"Bearer {self._token()}"},
        )
        try:
            return payload["results"][0]["generated_text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise WatsonxError(
                f"Unexpected generation response shape: {payload!r}"
            ) from exc

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _token(self) -> str:
        """Return a cached IAM access token, refreshing it when stale."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        form = urllib.parse.urlencode(
            {"grant_type": IAM_GRANT_TYPE, "apikey": self.config.api_key}
        ).encode("ascii")
        try:
            payload = self._request_json(
                "POST",
                IAM_TOKEN_URL,
                None,
                raw_body=form,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except WatsonxError as exc:
            raise AuthenticationError(
                f"IAM token exchange failed: {exc}"
            ) from exc
        try:
            token = payload["access_token"]
            expires_in = int(payload.get("expires_in", 3600))
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError(
                f"IAM token response missing access_token: {payload!r}"
            ) from exc
        self._access_token = token
        self._token_expires_at = (
            time.time() + expires_in - TOKEN_EXPIRY_BUFFER_SECONDS
        )
        return token

    def _request_json(
        self,
        method: str,
        url: str,
        body: dict | None,
        *,
        raw_body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        """HTTP request with retry/backoff on 429 and 5xx; returns parsed JSON."""
        data = raw_body if raw_body is not None else (
            json.dumps(body).encode("utf-8") if body is not None else None
        )
        request_headers = {"Accept": "application/json"}
        if data is not None and raw_body is None:
            request_headers["Content-Type"] = "application/json"
        request_headers.update(headers or {})

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    url, data=data, headers=request_headers, method=method
                )
                with urllib.request.urlopen(
                    req, timeout=REQUEST_TIMEOUT_SECONDS
                ) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = _read_error_body(exc)
                if exc.code in (401, 403):
                    raise AuthenticationError(
                        f"watsonx.ai rejected the request (HTTP {exc.code}): {detail}"
                    ) from exc
                if exc.code == 429 or 500 <= exc.code < 600:
                    last_error = RateLimitError(
                        f"watsonx.ai HTTP {exc.code}: {detail}"
                    )
                else:
                    raise WatsonxError(
                        f"watsonx.ai HTTP {exc.code}: {detail}"
                    ) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = WatsonxError(f"watsonx.ai transport error: {exc}")

            if attempt < MAX_RETRIES:
                delay = BASE_BACKOFF_SECONDS * (2 ** attempt)
                delay += random.uniform(0, 0.5)  # jitter
                time.sleep(delay)

        raise last_error or WatsonxError("watsonx.ai request failed")


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", "replace")[:500]
    except Exception:
        return "<unreadable error body>"
