import hashlib
import json
from pathlib import Path

class ResponseCache:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_key(self, model, prompt):
        """Generate cache key from model + prompt"""
        data = f"{model}:{prompt}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, model, prompt):
        """Retrieve cached response"""
        key = self._get_key(model, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return None
    
    def set(self, model, prompt, response):
        """Cache a response"""
        key = self._get_key(model, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump(response, f)