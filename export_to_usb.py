import os
import shutil
import time

def export_to_usb():
    # Configuration
    usb_drive = "D:\\"
    backup_folder_name = "CongoLang_Backup"
    destination = os.path.join(usb_drive, backup_folder_name)
    source = os.getcwd()
    
    # Folders to exclude
    exclude_patterns = [
        "__pycache__", 
        "node_modules", 
        "build", 
        ".dart_tool", 
        ".pub-cache", 
        ".firebase",
        ".git" # Usually good to exclude if the repo is large, but user didn't specify. I'll stick to their list.
    ]
    
    print(f"Starting CongoLang synchronization to {destination}...", flush=True)
    
    if not os.path.exists(usb_drive):
        print(f"Error: USB Drive {usb_drive} not found. Please ensure it is plugged in.", flush=True)
        return

    start_time = time.time()
    
    try:
        # Define ignore function
        ignore_func = shutil.ignore_patterns(*exclude_patterns)
        
        # Perform the copy
        if os.path.exists(destination):
            print(f"Updating existing backup at {destination}...", flush=True)
        
        shutil.copytree(source, destination, ignore=ignore_func, dirs_exist_ok=True)
        
        # Calculate size of transferred data
        total_size = 0
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(destination):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                file_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        size_mb = total_size / (1024 * 1024)
        
        print("\nBackup Complete!", flush=True)
        print("-" * 30, flush=True)
        print(f"Destination: {destination}", flush=True)
        print(f"Total Files: {file_count}", flush=True)
        print(f"Total Size:  {size_mb:.2f} MB", flush=True)
        print(f"Duration:    {duration:.2f} seconds", flush=True)
        print("-" * 30, flush=True)
        
    except Exception as e:
        print(f"Backup failed: {str(e)}", flush=True)

if __name__ == "__main__":
    export_to_usb()
