class URLMap:
    def __init__(self):
        self._map = {
            "WEBHOOK": "https://api.telegram.org/bot/update_time_script",
            "CREATE_SCRIPT": "https://api.telegram.org/bot/create_script_time",
            "UPDATE_SCRIPT": "https://api.telegram.org/bot/update_time_script",
            "WEB": "http://127.0.0.1:8000",
        }

    def get(self, key: str, *, params: dict = None) -> str:
        url = self._map.get(key.upper())
        if not url:
            raise ValueError(f"URL key '{key}' not found in URLMap")

        if params:
            from urllib.parse import urlencode
            url += '?' + urlencode(params)

        return url
