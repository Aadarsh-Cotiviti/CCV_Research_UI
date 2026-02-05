import os
import io
import json

class FileStorage:
    """Unified file access for local and Databricks volumes"""

    def __init__(self) -> None:
        self.use_databricks = len(os.getenv("VOLUME_PATH", "")) > 0

        if self.use_databricks:
            from databricks.sdk import WorkspaceClient 
            self._client = WorkspaceClient()
            self._base = os.getenv("VOLUME_PATH", "").rstrip("/")
    
    def get_path(self, *path_parts: str) -> str:
        """Get full path in the storage system"""
        relative_path = os.path.join(*path_parts)
        if self.use_databricks:
            return f"{self._base}/{relative_path}"
        else:
            return relative_path

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
        if self.use_databricks:
            resp = self._client.files.download(path)
            if resp.contents is None:
                raise FileNotFoundError(f"File not found in Databricks: {path}")
            return resp.contents.read().decode('utf-8')
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def read_json(self, path: str) -> dict:
        """Read JSON file content"""
        text = self.read_text(path)
        return json.loads(text)
    
    def read_bytes(self, path: str) -> bytes:
        """Read binary file content"""
        if self.use_databricks:
            resp = self._client.files.download(path)
            if resp.contents is None:
                raise FileNotFoundError(f"File not found in Databricks: {path}")
            return resp.contents.read()
        else:
            with open(path, 'rb') as f:
                return f.read()
            
    def write_text(self, path: str, content: str) -> None:
        """Write text file content"""
        if self.use_databricks:
            bio = io.BytesIO(content.encode('utf-8'))
            self._client.files.upload(path, bio, overwrite=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

    def write_json(self, path: str, data: dict) -> None:
        """Write JSON file content"""
        text = json.dumps(data, indent=2)
        self.write_text(path, text)
    
    def write_bytes(self, path: str, data: bytes) -> None:
        """Write binary file content"""
        if self.use_databricks:
            bio = io.BytesIO(data)
            self._client.files.upload(path, bio, overwrite=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data)
    
    def write_csv(self, path: str, df, **kwargs) -> None:
        """Write a DataFrame to CSV format"""
        if self.use_databricks:
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False, **kwargs)
            buffer.seek(0)
            self._client.files.upload(path, buffer, overwrite=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            df.to_csv(path, index=False, **kwargs)
    def read_csv(self, path: str, **kwargs):
        """Read a CSV file into a DataFrame"""
        import pandas as pd
        if self.use_databricks:
            resp = self._client.files.download(path)
            if resp.contents is None:
                raise FileNotFoundError(f"File not found in Databricks: {path}")
            return pd.read_csv(io.BytesIO(resp.contents.read()), **kwargs)
        else:
            return pd.read_csv(path, **kwargs)
    
    def list_files(self, directory: str) -> list[str]:
        """List files in a directory"""
        if self.use_databricks:
            files = self._client.files.list_directory_contents(directory)
            return [f.name for f in files if f.name is not None]
        else:
            return os.listdir(directory)
        

storage = FileStorage()