"""
supabase/__init__.py
--------------------
'supabase' paketini httpx ile tamamen taklit eder.
api.py, worker.py, payment.py'da hiçbir değişiklik gerekmez.
"""

import httpx
from typing import Any, Optional


class AuthResponse:
    def __init__(self, user_data: dict):
        self.user = UserObj(user_data)


class UserObj:
    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.email = data.get("email", "")


class ExecuteResult:
    def __init__(self, data):
        self.data = data


class QueryBuilder:
    """
    supabase.table("x").select(...).eq(...).execute() zincirini taklit eder.
    """

    def __init__(self, url: str, headers: dict, table: str):
        self._url = url
        self._headers = headers
        self._table = table
        self._method = "GET"
        self._body: Optional[dict] = None
        self._params: dict = {}
        self._single = False
        self._rpc_name: Optional[str] = None

    # ── SELECT ──────────────────────────────────────────
    def select(self, columns: str = "*"):
        self._params["select"] = columns
        self._method = "GET"
        return self

    # ── FILTERS ─────────────────────────────────────────
    def eq(self, column: str, value: Any):
        self._params[column] = f"eq.{value}"
        return self

    def ilike(self, column: str, pattern: str):
        self._params[column] = f"ilike.{pattern}"
        return self

    def in_(self, column: str, values: list):
        joined = ",".join(str(v) for v in values)
        self._params[column] = f"in.({joined})"
        return self

    def is_(self, column: str, value: str):
        self._params[column] = f"is.{value}"
        return self

    def not_(self, column: str, operator: str, value: Any):
        # PostgREST negasyon: örn. not_("ekap_id", "in", "(a,b)") → ekap_id=not.in.(a,b)
        self._params[column] = f"not.{operator}.{value}"
        return self

    def order(self, column: str, desc: bool = False):
        self._params["order"] = f"{column}.{'desc' if desc else 'asc'}"
        return self

    def limit(self, n: int):
        self._params["limit"] = n
        return self

    def range(self, start: int, end: int):
        self._headers = {**self._headers, "Range": f"{start}-{end}"}
        return self

    def single(self):
        self._single = True
        self._headers = {**self._headers, "Accept": "application/vnd.pgrst.object+json"}
        return self

    # ── INSERT / UPDATE / UPSERT / DELETE ───────────────
    def insert(self, data: dict):
        self._method = "POST"
        self._body = data
        self._headers = {**self._headers, "Prefer": "return=representation"}
        return self

    def update(self, data: dict):
        self._method = "PATCH"
        self._body = data
        self._headers = {**self._headers, "Prefer": "return=representation"}
        return self

    def upsert(self, data: dict, on_conflict: str = "", ignore_duplicates: bool = False):
        self._method = "POST"
        self._body = data
        # ignore_duplicates=True → çakışan satırları güncelleme, atla (INSERT ... ON CONFLICT DO NOTHING)
        # False (varsayılan) → çakışanları güncelle (merge)
        resolution = "ignore-duplicates" if ignore_duplicates else "merge-duplicates"
        prefer = f"resolution={resolution},return=representation"
        self._headers = {**self._headers, "Prefer": prefer}
        if on_conflict:
            self._params["on_conflict"] = on_conflict
        return self

    def delete(self):
        self._method = "DELETE"
        self._headers = {**self._headers, "Prefer": "return=representation"}
        return self

    # ── EXECUTE ─────────────────────────────────────────
    def execute(self) -> ExecuteResult:
        endpoint = f"{self._url}/rest/v1/{self._table}"

        # Params: PostgREST için column=eq.value formatı
        params = {}
        for k, v in self._params.items():
            params[k] = v

        with httpx.Client(timeout=30) as client:
            resp = client.request(
                method=self._method,
                url=endpoint,
                headers=self._headers,
                params=params,
                json=self._body,
            )

        if resp.status_code >= 400:
            raise Exception(f"Supabase hata {resp.status_code}: {resp.text}")

        try:
            data = resp.json()
        except Exception:
            data = None

        return ExecuteResult(data)


class RpcBuilder:
    def __init__(self, url: str, headers: dict, func_name: str, params: dict):
        self._url = url
        self._headers = headers
        self._func_name = func_name
        self._params = params

    def execute(self) -> ExecuteResult:
        endpoint = f"{self._url}/rest/v1/rpc/{self._func_name}"
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                endpoint,
                headers=self._headers,
                json=self._params,
            )
        if resp.status_code >= 400:
            raise Exception(f"RPC hata {resp.status_code}: {resp.text}")
        try:
            data = resp.json()
        except Exception:
            data = None
        return ExecuteResult(data)


class AuthClient:
    def __init__(self, url: str, headers: dict):
        self._url = url
        self._headers = headers

    def get_user(self, token: str) -> AuthResponse:
        endpoint = f"{self._url}/auth/v1/user"
        hdrs = {**self._headers, "Authorization": f"Bearer {token}"}
        with httpx.Client(timeout=15) as client:
            resp = client.get(endpoint, headers=hdrs)
        if resp.status_code != 200:
            raise Exception(f"Auth hata {resp.status_code}: {resp.text}")
        return AuthResponse(resp.json())


class BucketObj:
    """list_buckets() sonuçları için .name erişimi sağlar."""
    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.public = data.get("public", False)


class StorageBucket:
    """sb.storage.from_(bucket) — upload / get_public_url."""
    def __init__(self, url: str, key: str, bucket: str):
        self._url = url
        self._key = key
        self._bucket = bucket

    def upload(self, path: str, content: bytes, file_options: dict = None) -> ExecuteResult:
        opts = file_options or {}
        ct = opts.get("content-type") or opts.get("contentType") or "application/octet-stream"
        upsert = str(opts.get("upsert", "false")).lower() == "true"
        endpoint = f"{self._url}/storage/v1/object/{self._bucket}/{path.lstrip('/')}"
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": ct,
        }
        if upsert:
            headers["x-upsert"] = "true"
        method = "PUT" if upsert else "POST"
        with httpx.Client(timeout=180) as client:
            resp = client.request(method, endpoint, headers=headers, content=content)
        if resp.status_code >= 400:
            raise Exception(f"Storage upload hata {resp.status_code}: {resp.text}")
        try:
            data = resp.json()
        except Exception:
            data = None
        return ExecuteResult(data)

    def get_public_url(self, path: str) -> str:
        return f"{self._url}/storage/v1/object/public/{self._bucket}/{path.lstrip('/')}"


class StorageClient:
    """sb.storage — from_ / list_buckets / create_bucket."""
    def __init__(self, url: str, key: str):
        self._url = url
        self._key = key

    def _auth_headers(self, json_ct: bool = True) -> dict:
        h = {"apikey": self._key, "Authorization": f"Bearer {self._key}"}
        if json_ct:
            h["Content-Type"] = "application/json"
        return h

    def from_(self, bucket: str) -> StorageBucket:
        return StorageBucket(self._url, self._key, bucket)

    def list_buckets(self) -> list:
        endpoint = f"{self._url}/storage/v1/bucket"
        with httpx.Client(timeout=30) as client:
            resp = client.get(endpoint, headers=self._auth_headers(json_ct=False))
        if resp.status_code >= 400:
            raise Exception(f"Storage list_buckets hata {resp.status_code}: {resp.text}")
        return [BucketObj(b) for b in (resp.json() or [])]

    def create_bucket(self, bucket_id: str, options: dict = None) -> ExecuteResult:
        opts = options or {}
        body = {"id": bucket_id, "name": bucket_id, "public": opts.get("public", False)}
        if "file_size_limit" in opts:
            body["file_size_limit"] = opts["file_size_limit"]
        endpoint = f"{self._url}/storage/v1/bucket"
        with httpx.Client(timeout=30) as client:
            resp = client.post(endpoint, headers=self._auth_headers(), json=body)
        if resp.status_code >= 400:
            raise Exception(f"Storage create_bucket hata {resp.status_code}: {resp.text}")
        try:
            data = resp.json()
        except Exception:
            data = None
        return ExecuteResult(data)


class Client:
    def __init__(self, url: str, key: str):
        self._url = url.rstrip("/")
        self._key = key
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self.auth = AuthClient(self._url, self._headers)
        self.storage = StorageClient(self._url, key)

    def table(self, name: str) -> QueryBuilder:
        return QueryBuilder(self._url, dict(self._headers), name)

    def rpc(self, func_name: str, params: dict = None) -> RpcBuilder:
        return RpcBuilder(self._url, dict(self._headers), func_name, params or {})


def create_client(url: str, key: str) -> Client:
    return Client(url, key)
