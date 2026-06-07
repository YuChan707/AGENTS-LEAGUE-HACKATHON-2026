import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class BlobStorageService:
    def __init__(self):
        conn_str = os.getenv("AZURE_BLOB_CONNECTION_STRING")
        self._enabled = bool(conn_str)
        if not self._enabled:
            print("WARNING: Azure Blob Storage not configured — file upload disabled")
            return
        from azure.storage.blobs import BlobServiceClient, ContentSettings
        self._ContentSettings = ContentSettings
        container = os.getenv("AZURE_BLOB_CONTAINER", "onlooker-reports")
        self._client = BlobServiceClient.from_connection_string(conn_str)
        self._container = container
        try:
            self._client.create_container(container, public_access="blob")
        except Exception:
            pass

    async def upload_pptx(self, file_bytes: bytes, session_id: str) -> str | None:
        if not self._enabled:
            return None
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"{session_id}/report_{timestamp}.pptx"
        blob_client = self._client.get_blob_client(
            container=self._container, blob=blob_name
        )
        blob_client.upload_blob(
            file_bytes,
            overwrite=True,
            content_settings=self._ContentSettings(
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        )
        return blob_client.url

blob_storage = BlobStorageService()
