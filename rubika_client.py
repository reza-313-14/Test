import os
import json
import requests
from typing import Dict

class Rubika:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = "https://botapi.rubika.ir/v3"
    
    def send_file(self, file_path: str, file_type: str = "Image") -> Dict:
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"file not found: {file_path}"
            }
        
        try:
            print(f"[RUBIKA] 📋 get upload link for: {file_type}")
            upload_url_response = requests.post(
                f"{self.base_url}/{self.token}/requestSendFile",
                json={"type": file_type}
            )
            
            if upload_url_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"error in get upload link: {upload_url_response.text}"
                }
            
            upload_data = upload_url_response.json()
            upload_url = upload_data["data"]["upload_url"]
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            print(f"[RUBIKA] 📤 upload: {file_name}")
            print(f"[RUBIKA] 📦 volume: {file_size / 1024:.1f} KB")
            
            with open(file_path, "rb") as file_obj:
                files = {
                    "file": (file_name, file_obj, "application/octet-stream")
                }
                
                upload_response = requests.post(
                    url=upload_url,
                    files=files,
                    timeout=120
                )
            
            print(f"[RUBIKA] 📊 upload status: {upload_response.status_code}")
            
            if upload_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"error in upload: {upload_response.text}"
                }
            
            try:
                upload_result = upload_response.json()
                file_id = upload_result["data"]["file_id"]
            except (json.JSONDecodeError, KeyError) as e:
                return {
                    "success": False,
                    "error": f"error in get file_id: {str(e)}"
                }
            
            print(f"[RUBIKA] 📨 send file to chat {self.chat_id}")
            send_response = requests.post(
                f"{self.base_url}/{self.token}/sendFile",
                json={
                    "chat_id": self.chat_id,
                    "file_id": file_id
                }
            )
            
            print(f"[RUBIKA] ✅ send status: {send_response.status_code}")
            
            if send_response.status_code == 200:
                os.remove(file_path)
                return {
                    "success": True,
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "send_response": send_response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"error in send: {send_response.text}",
                    "file_id": file_id
                }
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "error timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "connection error"}
        except Exception as e:
            return {"success": False, "error": f"error: {str(e)}"}

rubika = Rubika(
        token=os.environ.get("TOKEN"),
        chat_id=os.environ.get("CHAT_ID")
    )

if __name__ == "__main__":
    rubika = Rubika(
        token=os.environ.get("TOKEN"),
        chat_id=os.environ.get("CHAT_ID")
    )
    
    result = rubika.send_file("./test.zip", "File")
