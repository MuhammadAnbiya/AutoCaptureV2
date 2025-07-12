from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

def setup_drive():
    gauth = GoogleAuth()
    
    # Coba load token
    gauth.LoadCredentialsFile("mycreds.txt")

    if gauth.credentials is None:
        print("[INFO] Pertama kali login, buka browser untuk autentikasi...")
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    # Simpan token agar tidak perlu login ulang
    gauth.SaveCredentialsFile("mycreds.txt")

    return GoogleDrive(gauth)


def upload_worker(queue, drive, folder_id='1G5B8fwXdofqldea8UUHwzAs-teswuz7g'):
    while True:
        filepath = queue.get()
        try:
            filename = os.path.basename(filepath)
            file = drive.CreateFile({
                'title': filename,
                'parents': [{'id': folder_id}]
            })
            file.SetContentFile(filepath)
            file.Upload()
            print(f"✅ Uploaded: {filename}")
            print(f"🌐 Link: https://drive.google.com/file/d/{file['id']}/view")
        except Exception as e:
            print(f"[ERROR] Gagal upload: {e}")
        finally:
            queue.task_done()
