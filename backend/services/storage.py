import os
import io
import json
import logging
import posixpath


class FileStorage:
    """Unified file access for local and Databricks volumes"""

    def __init__(self) -> None:
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(levelname)s %(name)s - %(message)s",
            )
        self.use_databricks = bool(os.getenv("VOLUME_PATH", ""))
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)

        if self.use_databricks:
            from databricks.sdk import WorkspaceClient

            self._client = WorkspaceClient()
            raw_base = os.getenv("VOLUME_PATH", "")
            self._base = self._normalize_databricks_base(raw_base)
        else:
            self._base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"FileStorage initialized. Using Databricks: {self.use_databricks} Base path: {self._base}")

    def _normalize_databricks_base(self, base: str) -> str:
        """Normalize Databricks base path for Files API usage."""
        base = (base or "").strip().rstrip("/")
        if not base:
            return base

        if base.startswith("dbfs:/"):
            return "/dbfs/" + base[len("dbfs:/"):]

        if base.startswith("/"):
            return base

        if base.lower().startswith("volumes/"):
            return "/" + base

        self._logger.info(
            "VOLUME_PATH is not absolute. Using as-is: %s",
            base,
        )
        return base

    def _log_file_action(self, function_name: str, path: str) -> None:
        self._logger.info("%s: %s", function_name, path)

    def _log_file_error(self, function_name: str, path: str, error: Exception) -> None:
        self._logger.exception("%s failed: %s", function_name, path, exc_info=error)

    def _log_file_content(self, function_name: str, path: str, content: str, max_chars: int = 200) -> None:
        if content is None:
            return
        preview = content if len(content) <= max_chars else f"{content[:max_chars]}...<truncated>"
        self._logger.info("%s content (%s chars): %s", function_name, len(content), preview)

    def get_path(self, *path_parts: str) -> str:
        """Get full path in the storage system"""
        if self.use_databricks:
            return posixpath.join(self._base, *path_parts)
        else:
            relative_path = os.path.join(*path_parts)
            return os.path.join(self._base, relative_path)

    def exists(self, path: str) -> bool:
        """Check if file exists"""
        if self.use_databricks:
            try:
                self._client.files.get_metadata(path)
                return True
            except:
                return False
        else:
            return os.path.exists(path)

    def read_text(self, path: str) -> str:
        """Read text file content"""
        self._log_file_action("read_text", path)
        try:
            if self.use_databricks:
                resp = self._client.files.download(path)
                if resp.contents is None:
                    raise FileNotFoundError(f"File not found in Databricks: {path}")
                content = resp.contents.read().decode("utf-8")
                self._log_file_content("read_text", path, content)
                return content
            else:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self._log_file_content("read_text", path, content)
                    return content
        except Exception as exc:
            self._log_file_error("read_text", path, exc)
            raise

    def read_json(self, path: str) -> dict:
        """Read JSON file content"""
        text = self.read_text(path)
        return json.loads(text)

    def read_bytes(self, path: str) -> io.BytesIO:
        """Read binary file content"""
        self._log_file_action("read_bytes", path)
        try:
            if self.use_databricks:
                resp = self._client.files.download(path)
                if resp.contents is None:
                    raise FileNotFoundError(f"File not found in Databricks: {path}")
                data = resp.contents.read()
                self._log_file_content("read_bytes", path, data.decode("utf-8", errors="replace"))
                return io.BytesIO(data)
            else:
                with open(path, "rb") as f:
                    data = f.read()
                    self._log_file_content("read_bytes", path, data.decode("utf-8", errors="replace"))
                    return io.BytesIO(data)
        except Exception as exc:
            self._log_file_error("read_bytes", path, exc)
            raise

    def write_text(self, path: str, content: str) -> None:
        """Write text file content"""
        self._log_file_action("write_text", path)
        self._log_file_content("write_text", path, content)
        try:
            if self.use_databricks:
                bio = io.BytesIO(content.encode("utf-8"))
                self._client.files.upload(path, bio, overwrite=True)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception as exc:
            self._log_file_error("write_text", path, exc)
            raise

    def write_json(self, path: str, data: dict) -> None:
        """Write JSON file content"""
        text = json.dumps(data, indent=2)
        self.write_text(path, text)

    def write_bytes(self, path: str, data: bytes) -> None:
        """Write binary file content"""
        self._log_file_action("write_bytes", path)
        try:
            if self.use_databricks:
                bio = io.BytesIO(data)
                self._client.files.upload(path, bio, overwrite=True)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(data)
        except Exception as exc:
            self._log_file_error("write_bytes", path, exc)
            raise

    def write_csv(self, path: str, df, **kwargs) -> None:
        """Write a DataFrame to CSV format"""
        self._log_file_action("write_csv", path)
        try:
            if self.use_databricks:
                buffer = io.BytesIO()
                df.to_csv(buffer, index=False, **kwargs)
                buffer.seek(0)
                self._client.files.upload(path, buffer, overwrite=True)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                df.to_csv(path, index=False, **kwargs)
        except Exception as exc:
            self._log_file_error("write_csv", path, exc)
            raise

    def read_csv(self, path: str, **kwargs):
        """Read a CSV file into a DataFrame"""
        import pandas as pd

        self._log_file_action("read_csv", path)
        try:
            if self.use_databricks:
                resp = self._client.files.download(path)
                if resp.contents is None:
                    raise FileNotFoundError(f"File not found in Databricks: {path}")
                return pd.read_csv(io.BytesIO(resp.contents.read()), **kwargs)
            else:
                return pd.read_csv(path, **kwargs)
        except Exception as exc:
            self._log_file_error("read_csv", path, exc)
            raise

    def list_files(self, directory: str) -> list[str]:
        """List files in a directory"""
        if self.use_databricks:
            files = self._client.files.list_directory_contents(directory)
            return [f.name for f in files if f.name is not None]
        else:
            return os.listdir(directory)


fileStorage = FileStorage()