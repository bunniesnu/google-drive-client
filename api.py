from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    def download_file(self, file_id: str, destination: str | None = None, verbose: bool = False):
        """
        Downloads a file from Google Drive using service account authentication.

        * file_id: The ID of the file to download.
        * destination: The path to save the file to. If None, the file will be yielded.
        * verbose: Whether to print download status messages.
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
                if verbose:
                    tqdm.write(f"File downloaded: {file_id} -> {destination}")
        else:
            error_msg = f"Failed to download file: {response.status_code} - {response.text}"
            tqdm.write(error_msg)
            raise Exception(error_msg)
    def iter_images(self, folder_id: str, page_size: int = 100):
        """
        Iterates through all images in the specified folder.

        * folder_id: The ID of the Google Drive folder to iterate through.
        * page_size: The number of files to fetch per page.
        """
        for file in self.list_files(folder_id, page_size):
            yield self.download_file(file["id"])
    def download_images(self, folder_id: str, destination_folder_path: str, page_size: int = 100, verbose: bool = False, show_tqdm: bool = True):
        """
        Downloads all images in the specified folder to a local directory.

        * folder_id: The ID of the Google Drive folder to download images from.
        * destination_folder_path: The path to save the images to.
        * page_size: The number of files to fetch per page.
        * verbose: Whether to print download status messages.
        * show_tqdm: Whether to display a progress bar.
        """
        os.makedirs(destination_folder_path, exist_ok=True)
        def download_task(file_id: str, file_name: str):
            self.download_file(file_id, os.path.join(destination_folder_path, file_name), verbose)
        files: list[tuple[str, str]] = []
        for file in self.list_files(folder_id, page_size):
            files.append((str(file["id"]), str(file["name"])))
        if show_tqdm:
            with ThreadPoolExecutor() as executor, tqdm(total=len(files), desc=f"Downloading: {folder_id} -> {destination_folder_path}", ncols=100) as pbar:
                futures = {executor.submit(download_task, file_id, file_name) for file_id, file_name in files}
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
        else:
            with ThreadPoolExecutor() as executor:
                executor.map(lambda args: download_task(*args), files)
    def upload_file(self, file_path: str, folder_id: str, file_name: str | None = None, verbose: bool = False):
        """
        Uploads a file to Google Drive using service account authentication.

        * file_path: The path to the file to upload.
        * folder_id: The ID of the folder to upload the file to.
        * file_name: Optional name for the file in Drive. If None, uses original filename.
        * verbose: Whether to print upload status messages.
        """
        if file_name is None:
            file_name = os.path.basename(file_path)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(
            file_path,
            resumable=True
        )

        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            if verbose:
                tqdm.write(f"File uploaded successfully. File ID: {file.get('id')}")
            return file.get('id')
        except Exception as e:
            if verbose:
                tqdm.write(f"An error occurred while uploading the file: {e}")
            return None
    def delete_folder_contents(self, folder_id: str, verbose: bool = False):
        """
        Deletes all files within a specified folder but keeps the folder itself.

        * folder_id: The ID of the Google Drive folder whose contents should be deleted.
        * verbose: Whether to print status messages.
        """
        try:
            # List all files in the folder
            files = self.list_files(folder_id)
            
            # Delete each file
            for file in files:
                try:
                    self.service.files().delete(fileId=file['id']).execute()
                    if verbose:
                        tqdm.write(f"Deleted file: {file['name']}")
                except Exception as e:
                    if verbose:
                        tqdm.write(f"Error deleting file {file['name']}: {e}")
            
            if verbose:
                tqdm.write(f"Successfully deleted all contents of folder {folder_id}")
            return True
        except Exception as e:
            if verbose:
                tqdm.write(f"An error occurred while deleting folder contents: {e}")
            return False