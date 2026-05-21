"""Client HTTP per il cloud Immergas Smartech Plus."""
from __future__ import annotations
import requests

BASE_URL = "https://smartechplus.immergas.com"

BOILER_MODES = {"0": "Spento", "2": "Estate", "3": "Inverno", "4": "Raffrescamento"}
BOILER_MODES_REVERSE = {v: k for k, v in BOILER_MODES.items()}

class ImmergasAuthError(Exception):
    pass

class ImmergasConnectionError(Exception):
    pass

class ImmergasClient:
    def __init__(self, token_a, token_b, phpsessid, email="", password=""):
        self._token_a = token_a
        self._token_b = token_b
        self._phpsessid = phpsessid
        self.email = email
        self.password = password
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15", "X-Requested-With": "XMLHttpRequest", "Referer": BASE_URL + "/dashboard/index"})
        self._session.cookies.update({"tokenA": token_a, "tokenB": token_b, "PHPSESSID": phpsessid, "lang": "it"})

    def _parse_result(self, resp):
        try:
            result = resp.json()
            if isinstance(result, dict):
                return result.get("code") == 200
            return int(result) > 0
        except Exception:
            return False

    def get_devices(self):
        try:
            resp = self._session.get(BASE_URL + "/api/getDevices", timeout=15)
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
                devices.append({"thing_id": thing_id, "device_name": info.get("name", ""), "temp_off": info.get("tempOff", 16)})
        return devices

    def get_status(self, device_name, thing_id):
        try:
            resp = self._session.get(BASE_URL + "/api/getTemp", params={"device": device_name, "id": thing_id, "scheduler": 1}, timeout=15)
            data = resp.json()
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err
        if data.get("code") != 200:
            raise ImmergasConnectionError(f"Risposta inattesa: {data}")
        status = data.get("status", {})
        return {"current_temp": float(data.get("currentTemp", 0)), "setpoint": float(data.get("settedTemp", 0)), "ext_temp": float(data.get("extTemp", 0)), "mode": int(status.get("mode", 0)), "fire_icon": bool(status.get("fireIcon", False)), "rubinetto": bool(status.get("rubinettoIcon", False))}

    def set_temperature(self, device_name, thing_id, temp):
        try:
            resp = self._session.get(BASE_URL + "/api/setTemp", params={"temp": temp, "device": device_name, "id": thing_id}, timeout=15)
            return self._parse_result(resp)
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err

    def set_mode(self, device_name, thing_id, mode):
        try:
            resp = self._session.get(BASE_URL + "/api/setMode", params={"mode": mode, "device": device_name, "id": thing_id}, timeout=15)
            return self._parse_result(resp)
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err

    def set_boiler_mode(self, device_name, thing_id, boiler_mode, sanitary_temp=45):
        try:
            resp = self._session.get(BASE_URL + "/api/setParamWebApp", params={"boilerMode": boiler_mode, "setSanitario": sanitary_temp, "id": thing_id}, timeout=15)
            return self._parse_result(resp)
        except Exception as err:
            raise ImmergasConnectionError(str(err)) from err
