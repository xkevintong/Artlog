import io
import json

from googleapiclient import discovery
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools
import pendulum


def get_drive_service():
    scopes = "https://www.googleapis.com/auth/drive"
    store = file.Storage("storage.json")
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets("client_id.json", scopes)
        creds = tools.run_flow(flow, store)
    return discovery.build("drive", "v3", http=creds.authorize(Http()))


def extract_url_from_file(bytes):
    file_string = bytes.decode("utf-8")
    if "https://www.pixiv.net" in file_string:
        return "pixiv", file_string.strip()
    elif "https://twitter.com" in file_string:
        return "twitter", file_string[file_string.rfind("https://twitter.com") :]
    else:
        return "misc", file_string


def download_files_from_drive(service):
    folder_response = (
        service.files()
        .list(
            q="mimeType = 'application/vnd.google-apps.folder' and name = 'Artlog'",
            spaces="drive",
            fields="files(id)",
        )
        .execute()
    )
    folder_id = folder_response.get("files", []).pop()["id"]

    pixiv_list = []
    twitter_list = []
    misc_list = []

    page_token = None
    file_count = 0
    while True:
        file_response = (
            service.files()
            .list(
                q=f"parents in '{folder_id}'",
                spaces="drive",
                fields="nextPageToken, files(id, createdTime)",
                pageToken=page_token,
            )
            .execute()
        )
        files = file_response.get("files", [])
        file_count += len(files)
        for drive_file in files:
            file_id = drive_file.get("id")
            download_request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, download_request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            website, url = extract_url_from_file(fh.getvalue())
            formatted_time = (
                pendulum.parse(drive_file.get("createdTime"))
                .in_tz("America/Los_Angeles")
                .format("YYYY-MM-DD HH:mm")
            )
            file_info = {"url": url, "time": formatted_time, "drive_id": file_id}
            if website == "pixiv":
                pixiv_list.append(file_info)
            elif website == "twitter":
                twitter_list.append(file_info)
            elif website == "misc":
                misc_list.append(file_info)
            print(url, formatted_time)

        page_token = file_response.get("nextPageToken", None)
        if page_token is None:
            break

    timestamp = pendulum.now().format("YYYY-MM-DD_HHmm")
    with open(f"drive_links/drive_links_{timestamp}.json", "w") as links_file:
        json.dump(
            {"pixiv": pixiv_list, "twitter": twitter_list, "misc": misc_list},
            links_file,
            indent=4,
        )

    return file_count, timestamp


def move_files_in_drive(service, num_files_in_drive, timestamp):
    processed_folder_response = (
        service.files()
        .list(
            q="mimeType = 'application/vnd.google-apps.folder' and name = 'Artlog_Processed'",
            spaces="drive",
            fields="files(id)",
        )
        .execute()
    )
    processed_folder_id = processed_folder_response.get("files", []).pop()["id"]

    with open(f"drive_links/drive_links_{timestamp}.json") as links_file:
        links = json.load(links_file)
        num_files_in_json = sum(len(urls) for urls in links.values())
        if num_files_in_json == num_files_in_drive:
            for website in (links["pixiv"], links["twitter"], links["misc"]):
                for image in website:
                    file_id = image["drive_id"]
                    # Retrieve the existing parents to remove
                    drive_file = (
                        service.files().get(fileId=file_id, fields="parents").execute()
                    )
                    previous_parents = ",".join(drive_file.get("parents"))
                    # Move the file to the new folder
                    drive_file = (
                        service.files()
                        .update(
                            fileId=file_id,
                            addParents=processed_folder_id,
                            removeParents=previous_parents,
                            fields="id, parents",
                        )
                        .execute()
                    )
                    print(f"Moved {image['url']} to Artlog_Processed")

            print(f"{num_files_in_drive} files moved")

        else:
            print(
                "Number of files in the Artlog folder does not match the number of URLs."
            )


def upload_json():
    pass

def get_urls_from_drive():
    service = get_drive_service()
    num_files_in_drive, timestamp = download_files_from_drive(service)
    move_files_in_drive(service, num_files_in_drive, timestamp)
    # todo: upload the json to another google drive folder
    upload_json(service)


if __name__ == "__main__":
    get_urls_from_drive()
