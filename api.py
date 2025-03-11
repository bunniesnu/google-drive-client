from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests

class GoogleDriveClient:
    """
    Google Drive API client for iterating through images in a folder.

    Usage:

      client = GoogleDriveClient("path/to/credentials.json")

      iter = client.iter_images("folder_id")
    """
    def __init__(self, credentials_path: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.credentials)
    
    def list_files(self, folder_id: str, page_size: int = 100):
        """
        List all files in the specified folder.

        * folder_id: The ID of the Google Drive folder to iterate through.
        * page_size: The number of files to fetch per page.
        """
        query = f"'{folder_id}' in parents and trashed=false"
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageSize=page_size,
                pageToken=page_token
            ).execute()
            
            for file in response.get("files", []):
                yield file
            
            page_token = response.get("nextPageToken")
            if not page_token:
                break
    def download_file(self, file_id: str, destination: str | None = None):
        """
        Downloads a file from Google Drive using service account authentication.

        * file_id: The ID of the file to download.
        * destination: The path to save the file to. If None, the file will be yielded.
        """
        headers = {"Authorization": f"Bearer {self.credentials.token}"}
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        response = requests.get(url, headers=headers, stream=True)
        
        if response.status_code == 200:
            if destination is None:
                return response.content
            else:
                with open(destination, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"File downloaded: {destination}")
        else:
            print(f"Failed to download file: {response.status_code} - {response.text}")
    def iter_images(self, folder_id: str, page_size: int = 100):
        """
        Iterates through all images in the specified folder.

        * folder_id: The ID of the Google Drive folder to iterate through.
        * page_size: The number of files to fetch per page.
        """
        for file in self.list_files(folder_id, page_size):
            yield self.download_file(file["id"])