from __future__ import annotations

import stat as _stat
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StorageEntry:
    name: str
    relative_path: str  # POSIX path relative to backend root
    is_dir: bool
    is_symlink: bool = False


@dataclass
class DirBrowseResult:
    current_path: str
    parent_path: str | None
    directories: list[tuple[str, str]] = field(default_factory=list)  # [(name, opaque_path)]


class StorageBackend(ABC):
    @property
    @abstractmethod
    def root_display(self) -> str:
        """Human-readable root path shown in the UI."""

    @abstractmethod
    def list_children(self, relative_path: str) -> list[StorageEntry]:
        """List direct children. relative_path='' means root."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool: ...

    @abstractmethod
    def is_file(self, relative_path: str) -> bool: ...

    @abstractmethod
    def is_dir(self, relative_path: str) -> bool: ...

    @abstractmethod
    def read_text(self, relative_path: str) -> str: ...

    @abstractmethod
    def write_text(self, relative_path: str, content: str) -> None: ...

    @abstractmethod
    def write_bytes(self, relative_path: str, content: bytes) -> None: ...

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes: ...

    @abstractmethod
    def create_file(self, relative_path: str) -> None: ...

    @abstractmethod
    def create_dir(self, relative_path: str) -> None: ...

    @abstractmethod
    def delete(self, relative_path: str) -> None: ...

    @abstractmethod
    def rename(self, src_relative: str, dst_relative: str) -> None: ...

    @abstractmethod
    def rglob_files(self, relative_path: str) -> list[str]:
        """Recursively list all file paths (not dirs) under relative_path."""

    @abstractmethod
    def get_as_local_path(self, relative_path: str) -> tuple[Path, bool]:
        """Return (local_path, is_temporary). Caller must unlink if is_temporary=True."""

    @abstractmethod
    def browse_dirs(self, path: str | None) -> DirBrowseResult:
        """Browse directories for the directory picker in settings."""


# ---------------------------------------------------------------------------
# Local filesystem backend
# ---------------------------------------------------------------------------

class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root_display(self) -> str:
        return str(self._root)

    def _abs(self, relative_path: str) -> Path:
        return self._root if not relative_path else self._root / relative_path

    def list_children(self, relative_path: str) -> list[StorageEntry]:
        path = self._abs(relative_path)
        result = []
        for child in path.iterdir():
            rel = child.relative_to(self._root).as_posix()
            is_symlink = child.is_symlink()
            is_dir = not is_symlink and child.is_dir()
            result.append(StorageEntry(
                name=child.name,
                relative_path=rel,
                is_dir=is_dir,
                is_symlink=is_symlink,
            ))
        return result

    def exists(self, relative_path: str) -> bool:
        return self._abs(relative_path).exists()

    def is_file(self, relative_path: str) -> bool:
        return self._abs(relative_path).is_file()

    def is_dir(self, relative_path: str) -> bool:
        return self._abs(relative_path).is_dir()

    def read_text(self, relative_path: str) -> str:
        return self._abs(relative_path).read_text(encoding="utf-8")

    def write_text(self, relative_path: str, content: str) -> None:
        self._abs(relative_path).write_text(content, encoding="utf-8")

    def write_bytes(self, relative_path: str, content: bytes) -> None:
        self._abs(relative_path).write_bytes(content)

    def read_bytes(self, relative_path: str) -> bytes:
        return self._abs(relative_path).read_bytes()

    def create_file(self, relative_path: str) -> None:
        self._abs(relative_path).write_text("", encoding="utf-8")

    def create_dir(self, relative_path: str) -> None:
        self._abs(relative_path).mkdir(parents=False, exist_ok=False)

    def delete(self, relative_path: str) -> None:
        import shutil
        p = self._abs(relative_path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

    def rename(self, src_relative: str, dst_relative: str) -> None:
        self._abs(src_relative).rename(self._abs(dst_relative))

    def rglob_files(self, relative_path: str) -> list[str]:
        base = self._abs(relative_path)
        return [child.relative_to(self._root).as_posix() for child in base.rglob("*") if child.is_file()]

    def get_as_local_path(self, relative_path: str) -> tuple[Path, bool]:
        return self._abs(relative_path), False

    def browse_dirs(self, path: str | None) -> DirBrowseResult:
        if path:
            current = Path(path).expanduser().resolve()
            if not current.exists() or not current.is_dir():
                current = self._root
        else:
            current = self._root

        dirs: list[tuple[str, str]] = []
        try:
            children = sorted(
                (c for c in current.iterdir() if c.is_dir()),
                key=lambda c: c.name.lower(),
            )
            for child in children:
                dirs.append((child.name, str(child.resolve())))
        except PermissionError:
            pass

        parent = str(current.parent.resolve()) if current.parent != current else None
        return DirBrowseResult(current_path=str(current), parent_path=parent, directories=dirs)


# ---------------------------------------------------------------------------
# SFTP backend
# ---------------------------------------------------------------------------

class SFTPStorageBackend(StorageBackend):
    def __init__(self, host: str, port: int, username: str, password: str, remote_path: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._remote_root = remote_path.rstrip("/") or "/"
        self._ssh = None
        self._sftp = None

    def _connect(self):
        import paramiko

        if self._sftp is not None:
            try:
                self._sftp.stat(".")
                return self._sftp
            except Exception:
                try:
                    self._sftp.close()
                except Exception:
                    pass
                self._sftp = None
                try:
                    if self._ssh:
                        self._ssh.close()
                except Exception:
                    pass
                self._ssh = None

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            timeout=10,
        )
        self._ssh = ssh
        self._sftp = ssh.open_sftp()
        return self._sftp

    def _abs(self, relative_path: str) -> str:
        if not relative_path:
            return self._remote_root
        return f"{self._remote_root}/{relative_path}"

    @property
    def root_display(self) -> str:
        return f"sftp://{self._username}@{self._host}{self._remote_root}"

    def list_children(self, relative_path: str) -> list[StorageEntry]:
        sftp = self._connect()
        abs_path = self._abs(relative_path)
        result = []
        for attr in sftp.listdir_attr(abs_path):
            name = attr.filename
            child_rel = f"{relative_path}/{name}" if relative_path else name
            mode = attr.st_mode or 0
            is_sym = _stat.S_ISLNK(mode)
            if is_sym:
                try:
                    followed = sftp.stat(f"{abs_path}/{name}")
                    is_dir = _stat.S_ISDIR(followed.st_mode or 0)
                except Exception:
                    is_dir = False
            else:
                is_dir = _stat.S_ISDIR(mode)
            result.append(StorageEntry(name=name, relative_path=child_rel, is_dir=is_dir, is_symlink=is_sym))
        return result

    def exists(self, relative_path: str) -> bool:
        sftp = self._connect()
        try:
            sftp.stat(self._abs(relative_path))
            return True
        except FileNotFoundError:
            return False

    def is_file(self, relative_path: str) -> bool:
        sftp = self._connect()
        try:
            attr = sftp.stat(self._abs(relative_path))
            return _stat.S_ISREG(attr.st_mode or 0)
        except Exception:
            return False

    def is_dir(self, relative_path: str) -> bool:
        sftp = self._connect()
        try:
            attr = sftp.stat(self._abs(relative_path))
            return _stat.S_ISDIR(attr.st_mode or 0)
        except Exception:
            return False

    def read_text(self, relative_path: str) -> str:
        return self.read_bytes(relative_path).decode("utf-8")

    def write_text(self, relative_path: str, content: str) -> None:
        self.write_bytes(relative_path, content.encode("utf-8"))

    def write_bytes(self, relative_path: str, content: bytes) -> None:
        sftp = self._connect()
        with sftp.open(self._abs(relative_path), "wb") as f:
            f.write(content)

    def read_bytes(self, relative_path: str) -> bytes:
        sftp = self._connect()
        with sftp.open(self._abs(relative_path), "rb") as f:
            return f.read()

    def create_file(self, relative_path: str) -> None:
        self.write_bytes(relative_path, b"")

    def create_dir(self, relative_path: str) -> None:
        sftp = self._connect()
        sftp.mkdir(self._abs(relative_path))

    def delete(self, relative_path: str) -> None:
        sftp = self._connect()
        self._delete_sftp_recursive(sftp, relative_path)

    def _delete_sftp_recursive(self, sftp, relative_path: str) -> None:
        abs_path = self._abs(relative_path)
        try:
            attr = sftp.stat(abs_path)
            if _stat.S_ISDIR(attr.st_mode or 0):
                for entry in self.list_children(relative_path):
                    self._delete_sftp_recursive(sftp, entry.relative_path)
                sftp.rmdir(abs_path)
            else:
                sftp.remove(abs_path)
        except FileNotFoundError:
            pass

    def rename(self, src_relative: str, dst_relative: str) -> None:
        sftp = self._connect()
        sftp.rename(self._abs(src_relative), self._abs(dst_relative))

    def rglob_files(self, relative_path: str) -> list[str]:
        result: list[str] = []
        self._rglob_recursive(relative_path, result)
        return result

    def _rglob_recursive(self, rel: str, result: list[str]) -> None:
        for entry in self.list_children(rel):
            if entry.is_dir and not entry.is_symlink:
                self._rglob_recursive(entry.relative_path, result)
            else:
                result.append(entry.relative_path)

    def get_as_local_path(self, relative_path: str) -> tuple[Path, bool]:
        content = self.read_bytes(relative_path)
        suffix = Path(relative_path).suffix
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(content)
        tmp.close()
        return Path(tmp.name), True

    def browse_dirs(self, path: str | None) -> DirBrowseResult:
        sftp = self._connect()
        current = path or self._remote_root

        try:
            attr = sftp.stat(current)
            if not _stat.S_ISDIR(attr.st_mode or 0):
                current = self._remote_root
        except Exception:
            current = self._remote_root

        dirs: list[tuple[str, str]] = []
        try:
            entries = sorted(sftp.listdir_attr(current), key=lambda a: a.filename.lower())
            for attr in entries:
                if _stat.S_ISDIR(attr.st_mode or 0):
                    child_path = f"{current.rstrip('/')}/{attr.filename}"
                    dirs.append((attr.filename, child_path))
        except Exception:
            pass

        parent = None
        stripped = current.rstrip("/")
        if "/" in stripped:
            parent = stripped.rsplit("/", 1)[0] or "/"
        elif current != "/":
            parent = "/"

        return DirBrowseResult(current_path=current, parent_path=parent, directories=dirs)


# ---------------------------------------------------------------------------
# Google Drive backend
# ---------------------------------------------------------------------------

class GoogleDriveStorageBackend(StorageBackend):
    FOLDER_MIME = "application/vnd.google-apps.folder"

    def __init__(self, folder_id: str, credentials_json: str) -> None:
        self._root_folder_id = folder_id or "root"
        self._credentials_json = credentials_json
        self._service = None
        self._id_cache: dict[str, str] = {}  # relative_path -> file_id
        self._root_name: str | None = None

    def _get_service(self):
        import json
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        if self._service is not None:
            return self._service

        data = json.loads(self._credentials_json)
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        if not creds.valid:
            creds.refresh(Request())

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    def _resolve_to_id(self, relative_path: str) -> str:
        """Navigate relative path to a Drive file/folder ID."""
        if not relative_path:
            return self._root_folder_id
        if relative_path in self._id_cache:
            return self._id_cache[relative_path]

        import json as _json
        parts = relative_path.split("/")
        current_id = self._root_folder_id
        built = ""

        for part in parts:
            built = f"{built}/{part}" if built else part
            if built in self._id_cache:
                current_id = self._id_cache[built]
                continue
            service = self._get_service()
            resp = service.files().list(
                q=f"'{current_id}' in parents and name = {_json.dumps(part)} and trashed = false",
                fields="files(id, name, mimeType)",
                pageSize=10,
            ).execute()
            files = resp.get("files", [])
            if not files:
                raise FileNotFoundError(f"Not found in Drive: {built}")
            current_id = files[0]["id"]
            self._id_cache[built] = current_id

        return current_id

    @property
    def root_display(self) -> str:
        if self._root_name is None:
            try:
                svc = self._get_service()
                if self._root_folder_id == "root":
                    self._root_name = "Google Drive"
                else:
                    meta = svc.files().get(fileId=self._root_folder_id, fields="name").execute()
                    self._root_name = f"Google Drive/{meta.get('name', self._root_folder_id)}"
            except Exception:
                self._root_name = "Google Drive"
        return self._root_name

    def list_children(self, relative_path: str) -> list[StorageEntry]:
        service = self._get_service()
        folder_id = self._resolve_to_id(relative_path)

        result = []
        page_token = None
        while True:
            params: dict = {
                "q": f"'{folder_id}' in parents and trashed = false",
                "fields": "nextPageToken, files(id, name, mimeType)",
                "pageSize": 1000,
            }
            if page_token:
                params["pageToken"] = page_token
            resp = service.files().list(**params).execute()
            for item in resp.get("files", []):
                child_rel = f"{relative_path}/{item['name']}" if relative_path else item["name"]
                is_dir = item["mimeType"] == self.FOLDER_MIME
                self._id_cache[child_rel] = item["id"]
                result.append(StorageEntry(name=item["name"], relative_path=child_rel, is_dir=is_dir))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return result

    def exists(self, relative_path: str) -> bool:
        try:
            self._resolve_to_id(relative_path)
            return True
        except FileNotFoundError:
            return False

    def is_file(self, relative_path: str) -> bool:
        try:
            file_id = self._resolve_to_id(relative_path)
            service = self._get_service()
            meta = service.files().get(fileId=file_id, fields="mimeType").execute()
            return meta.get("mimeType") != self.FOLDER_MIME
        except Exception:
            return False

    def is_dir(self, relative_path: str) -> bool:
        if not relative_path:
            return True
        try:
            file_id = self._resolve_to_id(relative_path)
            service = self._get_service()
            meta = service.files().get(fileId=file_id, fields="mimeType").execute()
            return meta.get("mimeType") == self.FOLDER_MIME
        except Exception:
            return False

    def read_text(self, relative_path: str) -> str:
        return self.read_bytes(relative_path).decode("utf-8")

    def write_text(self, relative_path: str, content: str) -> None:
        self.write_bytes(relative_path, content.encode("utf-8"))

    def read_bytes(self, relative_path: str) -> bytes:
        import io
        from googleapiclient.http import MediaIoBaseDownload
        service = self._get_service()
        file_id = self._resolve_to_id(relative_path)
        request = service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()

    def write_bytes(self, relative_path: str, content: bytes) -> None:
        from googleapiclient.http import MediaInMemoryUpload
        service = self._get_service()
        media = MediaInMemoryUpload(content, resumable=False)
        try:
            file_id = self._resolve_to_id(relative_path)
            service.files().update(fileId=file_id, media_body=media).execute()
        except FileNotFoundError:
            parent_rel = str(Path(relative_path).parent)
            if parent_rel == ".":
                parent_rel = ""
            name = Path(relative_path).name
            parent_id = self._resolve_to_id(parent_rel)
            resp = service.files().create(
                body={"name": name, "parents": [parent_id]},
                media_body=media,
                fields="id",
            ).execute()
            self._id_cache[relative_path] = resp["id"]

    def create_file(self, relative_path: str) -> None:
        self.write_bytes(relative_path, b"")

    def create_dir(self, relative_path: str) -> None:
        service = self._get_service()
        parent_rel = str(Path(relative_path).parent)
        if parent_rel == ".":
            parent_rel = ""
        name = Path(relative_path).name
        parent_id = self._resolve_to_id(parent_rel)
        resp = service.files().create(
            body={"name": name, "mimeType": self.FOLDER_MIME, "parents": [parent_id]},
            fields="id",
        ).execute()
        self._id_cache[relative_path] = resp["id"]

    def delete(self, relative_path: str) -> None:
        service = self._get_service()
        file_id = self._resolve_to_id(relative_path)
        service.files().delete(fileId=file_id).execute()
        self._id_cache.pop(relative_path, None)

    def rename(self, src_relative: str, dst_relative: str) -> None:
        service = self._get_service()
        file_id = self._resolve_to_id(src_relative)

        src_parent_rel = str(Path(src_relative).parent)
        if src_parent_rel == ".":
            src_parent_rel = ""
        dst_parent_rel = str(Path(dst_relative).parent)
        if dst_parent_rel == ".":
            dst_parent_rel = ""
        dst_name = Path(dst_relative).name

        src_parent_id = self._resolve_to_id(src_parent_rel)
        dst_parent_id = self._resolve_to_id(dst_parent_rel)

        service.files().update(
            fileId=file_id,
            body={"name": dst_name},
            addParents=dst_parent_id,
            removeParents=src_parent_id,
            fields="id",
        ).execute()

        if src_relative in self._id_cache:
            self._id_cache[dst_relative] = self._id_cache.pop(src_relative)

    def rglob_files(self, relative_path: str) -> list[str]:
        result: list[str] = []
        self._rglob_recursive(relative_path, result)
        return result

    def _rglob_recursive(self, rel: str, result: list[str]) -> None:
        for entry in self.list_children(rel):
            if entry.is_dir:
                self._rglob_recursive(entry.relative_path, result)
            else:
                result.append(entry.relative_path)

    def get_as_local_path(self, relative_path: str) -> tuple[Path, bool]:
        content = self.read_bytes(relative_path)
        suffix = Path(relative_path).suffix
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(content)
        tmp.close()
        return Path(tmp.name), True

    def browse_dirs(self, path: str | None) -> DirBrowseResult:
        service = self._get_service()
        folder_id = path or self._root_folder_id

        try:
            meta = service.files().get(fileId=folder_id, fields="id, name, parents").execute()
            current_name = meta.get("name", folder_id)
        except Exception:
            folder_id = self._root_folder_id
            meta = {}
            current_name = "Google Drive"

        resp = service.files().list(
            q=f"'{folder_id}' in parents and mimeType = '{self.FOLDER_MIME}' and trashed = false",
            fields="files(id, name)",
            pageSize=200,
        ).execute()
        dirs = sorted(
            [(item["name"], item["id"]) for item in resp.get("files", [])],
            key=lambda x: x[0].lower(),
        )

        parents = meta.get("parents", [])
        parent_id = parents[0] if parents and folder_id != self._root_folder_id else None

        return DirBrowseResult(
            current_path=folder_id,
            parent_path=parent_id,
            directories=dirs,
        )


# ---------------------------------------------------------------------------
# Mega.nz backend
# ---------------------------------------------------------------------------

class MegaStorageBackend(StorageBackend):
    def __init__(self, email: str, password: str, root_path: str) -> None:
        self._email = email
        self._password = password
        self._root_path = root_path.strip("/")
        self._client = None

    def _get_client(self):
        if self._client is None:
            # mega.py 1.0.8 requires tenacity<6 which uses the removed
            # asyncio.coroutine decorator. Inject a compatible stub before import.
            import sys, types
            if 'tenacity' not in sys.modules:
                _fake = types.ModuleType('tenacity')
                def _retry(*args, **kwargs):
                    def _deco(fn): return fn
                    if args and callable(args[0]): return args[0]
                    return _deco
                _fake.retry = _retry
                _fake.wait_exponential = lambda **kw: None
                _fake.retry_if_exception_type = lambda *a: None
                sys.modules['tenacity'] = _fake
                sys.modules['tenacity._asyncio'] = types.ModuleType('tenacity._asyncio')
            from mega import Mega
            m = Mega()
            self._client = m.login(self._email, self._password)
        return self._client

    def _get_all_files(self) -> dict:
        return self._get_client().get_files()

    def _get_node_name(self, node: dict) -> str:
        return node.get("n") or node.get("a", {}).get("n", "")

    def _get_root_node(self, files: dict) -> dict:
        root = next((v for v in files.values() if v.get("t") == 2), None)
        if root is None:
            raise FileNotFoundError("Mega root not found")
        return root

    def _find_child(self, files: dict, parent_id: str, name: str) -> dict:
        for node in files.values():
            if node.get("p") == parent_id and self._get_node_name(node) == name:
                return node
        raise FileNotFoundError(f"Not found: {name}")

    def _find_node(self, relative_path: str) -> dict:
        files = self._get_all_files()
        current = self._get_root_node(files)

        # Navigate to configured root_path within Mega
        if self._root_path:
            for part in self._root_path.split("/"):
                current = self._find_child(files, current["h"], part)

        if not relative_path:
            return current

        for part in relative_path.split("/"):
            current = self._find_child(files, current["h"], part)

        return current

    @property
    def root_display(self) -> str:
        path = self._root_path or "/"
        return f"mega://{self._email}/{path}"

    def list_children(self, relative_path: str) -> list[StorageEntry]:
        files = self._get_all_files()
        parent_node = self._find_node(relative_path)
        parent_id = parent_node["h"]

        result = []
        for node in files.values():
            if node.get("p") != parent_id:
                continue
            node_type = node.get("t", -1)
            if node_type not in (0, 1):
                continue
            name = self._get_node_name(node)
            child_rel = f"{relative_path}/{name}" if relative_path else name
            result.append(StorageEntry(
                name=name,
                relative_path=child_rel,
                is_dir=(node_type == 1),
            ))
        return result

    def exists(self, relative_path: str) -> bool:
        try:
            self._find_node(relative_path)
            return True
        except FileNotFoundError:
            return False

    def is_file(self, relative_path: str) -> bool:
        try:
            return self._find_node(relative_path).get("t") == 0
        except Exception:
            return False

    def is_dir(self, relative_path: str) -> bool:
        if not relative_path:
            return True
        try:
            return self._find_node(relative_path).get("t") == 1
        except Exception:
            return False

    def read_bytes(self, relative_path: str) -> bytes:
        node = self._find_node(relative_path)
        with tempfile.TemporaryDirectory() as tmpdir:
            self._get_client().download(node, dest_path=tmpdir)
            name = self._get_node_name(node)
            return (Path(tmpdir) / name).read_bytes()

    def read_text(self, relative_path: str) -> str:
        return self.read_bytes(relative_path).decode("utf-8")

    def write_bytes(self, relative_path: str, content: bytes) -> None:
        m = self._get_client()
        parent_rel = str(Path(relative_path).parent)
        if parent_rel == ".":
            parent_rel = ""
        name = Path(relative_path).name
        parent_node = self._find_node(parent_rel)

        # If file exists, delete it first
        try:
            old_node = self._find_node(relative_path)
            m.delete(old_node)
        except FileNotFoundError:
            pass

        suffix = Path(relative_path).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            m.upload(tmp_path, dest=parent_node, dest_filename=name)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def write_text(self, relative_path: str, content: str) -> None:
        self.write_bytes(relative_path, content.encode("utf-8"))

    def create_file(self, relative_path: str) -> None:
        self.write_bytes(relative_path, b"")

    def create_dir(self, relative_path: str) -> None:
        m = self._get_client()
        parent_rel = str(Path(relative_path).parent)
        if parent_rel == ".":
            parent_rel = ""
        name = Path(relative_path).name
        parent_node = self._find_node(parent_rel)
        m.create_folder(name, dest=parent_node)

    def delete(self, relative_path: str) -> None:
        m = self._get_client()
        node = self._find_node(relative_path)
        m.delete(node)

    def rename(self, src_relative: str, dst_relative: str) -> None:
        m = self._get_client()
        src_node = self._find_node(src_relative)
        dst_parent_rel = str(Path(dst_relative).parent)
        if dst_parent_rel == ".":
            dst_parent_rel = ""
        dst_parent_node = self._find_node(dst_parent_rel)
        m.move(src_node, dst_parent_node)

    def rglob_files(self, relative_path: str) -> list[str]:
        result: list[str] = []
        self._rglob_recursive(relative_path, result)
        return result

    def _rglob_recursive(self, rel: str, result: list[str]) -> None:
        for entry in self.list_children(rel):
            if entry.is_dir:
                self._rglob_recursive(entry.relative_path, result)
            else:
                result.append(entry.relative_path)

    def get_as_local_path(self, relative_path: str) -> tuple[Path, bool]:
        content = self.read_bytes(relative_path)
        suffix = Path(relative_path).suffix
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(content)
        tmp.close()
        return Path(tmp.name), True

    def browse_dirs(self, path: str | None) -> DirBrowseResult:
        # path is "HANDLE:relative_path" to allow navigation
        if path and ":" in path:
            _, rel = path.split(":", 1)
        else:
            rel = path or ""

        files = self._get_all_files()
        current_node = self._find_node(rel)
        current_id = current_node["h"]

        dirs = []
        for node in files.values():
            if node.get("p") == current_id and node.get("t") == 1:
                name = self._get_node_name(node)
                child_rel = f"{rel}/{name}" if rel else name
                dirs.append((name, child_rel))
        dirs.sort(key=lambda x: x[0].lower())

        parent_rel = str(Path(rel).parent) if rel else None
        if parent_rel == ".":
            parent_rel = ""
        elif parent_rel is None:
            parent_rel = None

        return DirBrowseResult(
            current_path=rel or "/",
            parent_path=parent_rel,
            directories=dirs,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_sftp_cache: dict[tuple, SFTPStorageBackend] = {}
_gdrive_cache: dict[str, GoogleDriveStorageBackend] = {}
_mega_cache: dict[tuple, MegaStorageBackend] = {}


def build_backend(prefs) -> StorageBackend:
    source_type = getattr(prefs, "source_type", "local")

    if source_type == "sftp":
        key = (prefs.sftp_host, prefs.sftp_port, prefs.sftp_username, prefs.sftp_password, prefs.sftp_path)
        if key not in _sftp_cache:
            _sftp_cache[key] = SFTPStorageBackend(*key)
        return _sftp_cache[key]

    if source_type == "gdrive":
        creds = getattr(prefs, "gdrive_credentials", "")
        folder_id = getattr(prefs, "gdrive_folder_id", "root")
        cache_key = f"{folder_id}:{creds[:32]}"
        if cache_key not in _gdrive_cache:
            _gdrive_cache[cache_key] = GoogleDriveStorageBackend(folder_id, creds)
        return _gdrive_cache[cache_key]

    if source_type == "mega":
        key = (prefs.mega_email, prefs.mega_password, prefs.mega_path)
        if key not in _mega_cache:
            _mega_cache[key] = MegaStorageBackend(*key)
        return _mega_cache[key]

    return LocalStorageBackend(Path(prefs.content_root))


def invalidate_sftp_cache() -> None:
    for backend in _sftp_cache.values():
        try:
            if backend._sftp:
                backend._sftp.close()
        except Exception:
            pass
        try:
            if backend._ssh:
                backend._ssh.close()
        except Exception:
            pass
    _sftp_cache.clear()
    _gdrive_cache.clear()
    _mega_cache.clear()
