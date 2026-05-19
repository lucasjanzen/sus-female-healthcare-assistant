from azure.storage.blob import BlobServiceClient
from app.core.config import settings

_CONTAINER = "casf-audio-temp"


def _client() -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)


def upload_audio(blob_name: str, data: bytes) -> None:
    client = _client()
    container = client.get_container_client(_CONTAINER)
    if not container.exists():
        container.create_container()
    container.upload_blob(name=blob_name, data=data, overwrite=True)


def download_audio(blob_name: str) -> bytes:
    return _client().get_container_client(_CONTAINER).download_blob(blob_name).readall()


def delete_audio(blob_name: str) -> None:
    try:
        _client().get_container_client(_CONTAINER).delete_blob(blob_name)
    except Exception:
        pass
