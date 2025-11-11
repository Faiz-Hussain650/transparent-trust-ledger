import hashlib, json

def canonicalize(data: dict) -> str:
    def sort(obj):
        if isinstance(obj, dict):
            return {k: sort(obj[k]) for k in sorted(obj)}
        if isinstance(obj, list):
            return [sort(i) for i in obj]
        return obj
    return json.dumps(sort(data), separators=(",", ":"))

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
