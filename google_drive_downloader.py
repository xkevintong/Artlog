import io

from googleapiclient import discovery
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools

# Find Artlog folder

# Download all files to temp processing

# Extract all URLs to JSON

# Move folders in Drive to a processed folder
# Check if the number of image links equals the number of files in the folder
# Should be 1:1 so if its equal move everything to the processed folder


def get_drive_service():
    scopes = 'https://www.googleapis.com/auth/drive'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_id.json', scopes)
        creds = tools.run_flow(flow, store)
    return discovery.build('drive', 'v3', http=creds.authorize(Http()))


def extract_url_from_file(bytes):
    file_string = bytes.decode('utf-8')
    if 'https://www.pixiv.net' in file_string:
        return 'pixiv', file_string.strip()
    elif 'https://twitter.com' in file_string:
        return 'twitter', file_string[file_string.rfind('https://twitter.com'):]
    else:
        return 'other', file_string


def download_files_from_drive(service):
    folder_response = service.files().list(
        q="mimeType = 'application/vnd.google-apps.folder' and name = 'Artlog'",
        spaces='drive',
        fields='files(id)').execute()
    folder_id = folder_response.get('files', []).pop()['id']

    page_token = None
    while True:
        file_response = service.files().list(q=f"parents in '{folder_id}'",
                                             spaces='drive',
                                             fields='nextPageToken, files(id, name)',
                                             pageToken=page_token).execute()
        for drive_file in file_response.get('files', []):
            # todo: add each file_id (and file name?) to list for downloading, or read file contents
            # probably have to download and process immediately to avoid problems with duplicate twitter.txt files
            download_request = service.files().get_media(fileId=drive_file.get('id'))
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, download_request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            website, url = extract_url_from_file(fh.getvalue())
            print(url)
        page_token = file_response.get('nextPageToken', None)
        if page_token is None:
            break


def get_urls_from_drive():
    service = get_drive_service()
    download_files_from_drive(service)


if __name__ == "__main__":
    get_urls_from_drive()
