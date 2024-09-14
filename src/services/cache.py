from flask_caching import Cache


cache = Cache(
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache",
        "CACHE_THRESHOLD": 500,
        "CACHE_DEFAULT_TIMEOUT": 60 * 60,  # In seconds, default is 300, meaning 5 min
        "CACHE_DIR": "./cache",
    },
)

timeout = 86400
