        import json
        import hashlib
        from typing import Any


        def hash_json(obj: Any) -> str:
            """Deterministic SHA-256 hash of a JSON-serialisable object."""
            s = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
            return hashlib.sha256(s).hexdigest()
        