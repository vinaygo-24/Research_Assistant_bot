from azure.storage.blob import BlobServiceClient
import os

def download_blob_data():
    """
    Connects to Azure Blob Storage and downloads the file as bytes.
    Uses Env variables for security.
    """
    connection_string = os.getenv("AZURE_CONN_STRING")
    container_name = os.getenv("AZURE_CONTAINER")
    blob_name = os.getenv("AZURE_BLOB_NAME")

    try:
        print(f"[read_data] Connecting to Azure Blob: {blob_name}...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_container_client(container_name).get_blob_client(blob_name)
        
        pdf_bytes = blob_client.download_blob().readall()
        print(f"[read_data] Download successful. Size: {len(pdf_bytes)} bytes.")
        return pdf_bytes
    except Exception as e:
        print(f"[read_data] Error: {e}")
        return None