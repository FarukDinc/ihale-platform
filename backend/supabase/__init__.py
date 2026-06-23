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

    def upsert(self, data: dict, on_conflict: str = ""):
        self._method = "POST"
        self._body = data
        prefer = "resolution=merge-duplicates,return=representation"
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


class Client:
    def __init__(self, url: str, key: str):
        self._url = url.rstrip("/")
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self.auth = AuthClient(self._url, self._headers)

    def table(self, name: str) -> QueryBuilder:
        return QueryBuilder(self._url, dict(self._headers), name)

    def rpc(self, func_name: str, params: dict = None) -> RpcBuilder:
        return RpcBuilder(self._url, dict(self._headers), func_name, params or {})


def create_client(url: str, key: str) -> Client:
    return Client(url, key)
