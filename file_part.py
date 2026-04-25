import os
import pyzipper
from typing import List

MAX_PART_SIZE = 45 * 1024 * 1024
ZIP_PASSWORD = None  # example: b"my_secret_password"

def split_file(file_path: str) -> List[str]:
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"file {file_path} not found")
    
    base_dir = os.path.dirname(file_path) or "."
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    
    parts_dir = os.path.join(base_dir, f"{base_name}_parts")
    
    if not os.path.exists(parts_dir):
        os.makedirs(parts_dir)
        print(f"[SPLIT] folder {parts_dir} created")
    
    try:
        compression = pyzipper.ZIP_DEFLATED
        encryption = pyzipper.WZ_AES if ZIP_PASSWORD else None
        
        with open(file_path, 'rb') as original_file:
            file_content = original_file.read()
        
        total_size = len(file_content)
        print(f"[SPLIT] file volume: {total_size / (1024*1024):.2f} MB")
        
        effective_part_size = int(MAX_PART_SIZE * 0.99)
        num_parts = (total_size + effective_part_size - 1) // effective_part_size
        print(f"[SPLIT] parts: {num_parts}")
        
        parts_list = []
        
        for i in range(num_parts):
            part_num = i + 1
            start_byte = i * effective_part_size
            end_byte = min((i + 1) * effective_part_size, total_size)
            
            part_name = f"{base_name}.part{part_num:03d}.zip"
            part_path = os.path.join(parts_dir, part_name)
            
            print(f"[SPLIT] creating part {part_num}/{num_parts}: {part_name}")
            print(f"[SPLIT] bytes {start_byte} to {end_byte}")
            
            with pyzipper.AESZipFile(
                part_path,
                'w',
                compression=compression,
                encryption=encryption
            ) as zip_file:
                
                if ZIP_PASSWORD:
                    zip_file.setpassword(ZIP_PASSWORD)
                
                zip_file.writestr(file_name, file_content[start_byte:end_byte])
            
            part_size = os.path.getsize(part_path)
            part_size_mb = part_size / (1024 * 1024)
            parts_list.append(part_path)
            
            print(f"[SPLIT] part {part_num} create: {part_size_mb:.2f} MB")
            
            if part_size > MAX_PART_SIZE:
                print(f"[WARNING] part {part_num} larger than the allowed limit! {part_size_mb:.2f}MB > 45MB")
        
        os.remove(file_path)
        print(f"[SPLIT] main file {file_path} deleted.")
        
        print(f"[SPLIT] ✅ success.")
        print(f"[SPLIT] 📁 {len(parts_list)} part in folder {parts_dir}")
        
        return parts_list
        
    except Exception as e:
        print(f"[SPLIT ERROR] error: {e}")
        import shutil
        if os.path.exists(parts_dir):
            shutil.rmtree(parts_dir)
        raise



if __name__ == "__main__":
    split_file("./25557.jpg")
