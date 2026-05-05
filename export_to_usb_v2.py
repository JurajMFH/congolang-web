import shutil
import os
import time

def export_project(drive_letter):
    # Ensure drive letter format
    drive_letter = drive_letter.strip().upper().replace(':', '')
    destination_base = f"{drive_letter}:\\"
    destination_path = os.path.join(destination_base, "CongoLang_Master_Backup")
    source_path = os.getcwd()

    print(f"Starting export to {destination_path}...")
    
    # Strictly exclude heavy/temp folders and specific extensions
    ignore_list = {
        '__pycache__', 'node_modules', 'build', '.dart_tool', 
        '.pub-cache', '.firebase', 'venv', 'env', '.git'
    }
    ignore_extensions = {'.apk', '.exe'}

    def ignore_func(directory, contents):
        ignored = []
        for item in contents:
            full_path = os.path.join(directory, item)
            # Ignore directories in the list
            if os.path.isdir(full_path) and item in ignore_list:
                ignored.append(item)
            # Ignore files with specific extensions
            elif os.path.isfile(full_path):
                if any(item.endswith(ext) for ext in ignore_extensions):
                    ignored.append(item)
        return ignored

    # Clean up destination if it exists
    if os.path.exists(destination_path):
        print(f"Removing old backup at {destination_path}...")
        shutil.rmtree(destination_path)

    start_time = time.time()
    try:
        shutil.copytree(source_path, destination_path, ignore=ignore_func)
        
        # Count files for summary
        file_count = 0
        for root, dirs, files in os.walk(destination_path):
            file_count += len(files)
            
        duration = time.time() - start_time
        print("-" * 40)
        print("SUCCESS: Backup Completed Successfully!")
        print(f"Total Files Transferred: {file_count}")
        print(f"Time Taken: {duration:.2f} seconds")
        print(f"Location: {destination_path}")
        print("-" * 40)
        
    except Exception as e:
        print(f"ERROR during backup: {str(e)}")

if __name__ == "__main__":
    # The drive letter was provided as 'D'
    export_project('D')
