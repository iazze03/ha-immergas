"""Client HTTP per il cloud Immergas Smartech Plus."""
from __future__ import annotations

import requests

BASE_URL = "https://smartechplus.immergas.com"

BOILER_MODES = {
    "0": "Spento",
    "2": "Estate",
    "3": "Inverno",
    "4": "Raffrescamento",
}
BOILER_MODES_REVERSE = {v: k for k, v in BOILER_MODES.items()}


class ImmergasAuthError(Exception):
    """Errore di autenticazione."""


class ImmergasConnectionError(Exception):
    """Errore di connessione."""


class ImmergasClient:
    """Client per le API cloud Immergas Smartech Plus."""

    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Safari/605.1.15"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": BASE_URL + "/dashboard/index",
        })
        self._token_a: str | None = None
        self._token_b: str | None = None
        self._phpsessid: str | None = None

    # ─────────────────────────────────────────
    #  AUTH
    # ─────────────────────────────────────────

    def login(self) -> None:
        """Esegue il login e salva i cookie di sessione."""
        # Reset sessione e cookie precedenti
        self._session.cookies.clear()
        self._token_a   = None
        self._token_b   = None
        self._phpsessid = None

        try:
            # Step 1: GET della pagina login per ottenere eventuali cookie iniziali
            self._session.get(BASE_URL + "/", timeout=15)

            # Step 2: POST delle credenziali
            resp = self._session.post(
                BASE_URL + "/",
                data={"email": self.email, "password": self.password},
                allow_redirects=True,
                timeout=15,
            )
        except requests.RequestException as err:
            raise ImmergasConnectionError(str(err)) from err

        # Verifica presenza cookie tokenA e tokenB — sono la prova del login riuscito
        cookies = self._session.cookies.get_dict()
        self._token_a   = cookies.get("tokenA")
        self._token_b   = cookies.get("tokenB")
        self._phpsessid = cookies.get("PHPSESSID")

        if not self._token_a or not self._token_b:
            # Fallback: controlla anche il testo HTML
            if "logout" not in resp.text and "Dashboard" not in resp.text:
                raise ImmergasAuthError("Login fallito: credenziali non valide")

    def is_authenticated(self) -> bool:
        """Verifica se i token sono presenti."""
        return bool(self._token_a and self._token_b)

    def _ensure_auth(self) -> None:
        """Esegue il login se non autenticato."""
        if not self.is_authenticated():
            self.login()

    # ─────────────────────────────────────────
    #  LETTURA
    # ─────────────────────────────────────────

    def get_devices(self) -> list[dict]:
        """Restituisce la lista dei gateway/dispositivi."""
        self._ensure_auth()
        try:
            resp = self._session.get(
                BASE_URL + "/api/getDevices", timeout=15
            )
            data = resp.json()
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err

        gateways = data.get("gateways", [])
        if not gateways:
            return []

        devices = []
        for gw in gateways:
            thing_id = gw.get("thingId", "")
            for info in gw.get("info", []):
                devices.append({
                    "thing_id":    thing_id,
                    "device_name": info.get("name", ""),
                    "temp_off":    info.get("tempOff", 16),
                })
        return devices

    def get_status(self, device_name: str, thing_id: str) -> dict:
        """
        Legge lo stato corrente del termostato.

        Restituisce un dict con:
          current_temp, setpoint, ext_temp,
          mode (0=manuale, 1=auto), fire_icon (bool)
        """
        self._ensure_auth()
        try:
            resp = self._session.get(
                BASE_URL + "/api/getTemp",
                params={
                    "device":    device_name,
                    "id":        thing_id,
                    "scheduler": 1,
                },
                timeout=15,
            )
            data = resp.json()
        except Exception as err:
            # Prova re-login e riprova
            self._token_a = None
            self._token_b = None
            raise ImmergasConnectionError(str(err)) from err

        if data.get("code") != 200:
            raise ImmergasConnectionError(f"Risposta inattesa: {data}")

        status = data.get("status", {})
        return {
            "current_temp": float(data.get("currentTemp", 0)),
            "setpoint":     float(data.get("settedTemp", 0)),
            "ext_temp":     float(data.get("extTemp", 0)),
            "mode":         int(status.get("mode", 0)),
            "fire_icon":    bool(status.get("fireIcon", False)),
            "rubinetto":    bool(status.get("rubinettoIcon", False)),
        }

    # ─────────────────────────────────────────
    #  COMANDI
    # ─────────────────────────────────────────

    def set_temperature(
        self, device_name: str, thing_id: str, temp: float
    ) -> bool:
        """Imposta il setpoint di temperatura."""
        self._ensure_auth()
        try:
            resp = self._session.get(
                BASE_URL + "/api/setTemp",
                params={
                    "temp":   temp,
                    "device": device_name,
                    "id":     thing_id,
                },
                timeout=15,
            )
            data = resp.json()
            return data.get("code") == 200
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err

    def set_mode(
        self, device_name: str, thing_id: str, mode: int
    ) -> bool:
        """Imposta la modalità (0=manuale, 1=automatico)."""
        self._ensure_auth()
        try:
            resp = self._session.get(
                BASE_URL + "/api/setMode",
                params={
                    "mode":   mode,
                    "device": device_name,
                    "id":     thing_id,
                },
                timeout=15,
            )
            data = resp.json()
            return data.get("code") == 200
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err

    def set_boiler_mode(
        self, thing_id: str, boiler_mode: str, sanitary_temp: int = 45
    ) -> bool:
        """
        Imposta la modalità caldaia.
        boiler_mode: "0"=spento, "2"=estate, "3"=inverno, "4"=raffrescamento
        """
        self._ensure_auth()
        try:
            resp = self._session.get(
                BASE_URL + "/api/setParamWebApp",
                params={
                    "boilerMode":   boiler_mode,
                    "setSanitario": sanitary_temp,
                    "id":           thing_id,
                },
                timeout=15,
            )
            data = resp.json()
            return data.get("code") == 200
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err
