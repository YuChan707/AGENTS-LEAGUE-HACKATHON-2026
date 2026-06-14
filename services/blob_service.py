
import os
from datetime import datetime
from azure.storage.blobs import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

class BlobStorageService:
    """
    Uploads generated PPTX files to Azure Blob Storage.
    Returns a public URL the frontend can download directly.
    """

    def __init__(self):
        conn_str = os.getenv("AZURE_BLOB_CONNECTION_STRING")
        container = os.getenv("AZURE_BLOB_CONTAINER", "onlooker-reports")

        if not conn_str:
            print("WARNING: AZURE_BLOB_CONNECTION_STRING not set — blob upload disabled")
            self._enabled = False
            return

        self._enabled = True
        self._client = BlobServiceClient.from_connection_string(conn_str)
        self._container = container

        # Create container if it does not exist
        try:
            self._client.create_container(
                container,
                public_access="blob"    # blobs publicly readable, not container listing
            )
        except Exception:
            pass    # already exists

    async def upload_pptx(
        self,
        file_bytes: bytes,
        session_id: str
    ) -> str | None:
        """
        Upload a PPTX file and return its public URL.
        Returns None if blob storage is not configured.
        """
        if not self._enabled:
            return None

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"{session_id}/coaching_report_{timestamp}.pptx"

        blob_client = self._client.get_blob_client(
            container=self._container,
            blob=blob_name
        )

        blob_client.upload_blob(
            file_bytes,
            overwrite=True,
            content_settings=ContentSettings(
                content_type=(
                    "application/vnd.openxmlformats-officedocument"
                    ".presentationml.presentation"
                ),
                content_disposition=f'attachment; filename="onlooker_report.pptx"'
            )
        )

        return blob_client.url

    async def upload_json(
        self,
        data: dict,
        session_id: str,
        label: str = "data"
    ) -> str | None:
        """Upload JSON session data for archival."""
        if not self._enabled:
            return None

        import json
        blob_name = f"{session_id}/{label}.json"
        blob_client = self._client.get_blob_client(
            container=self._container,
            blob=blob_name
        )
        blob_client.upload_blob(
            json.dumps(data, default=str).encode(),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json")
        )
        return blob_client.url


# Singleton
blob_storage = BlobStorageService()