url_map = {
    "web": {
        "host": "http://127.0.0.1:8000",
    },
    "telegram": {
        "host": "https://api.telegram.org",
        "webhook": "https://5de0-94-158-50-207.ngrok-free.app",
        "webapp": {
            "update_time_script": "/bot/update_time_script",
            "create_script_time": "/bot/create_script_time"
        }
    }
}