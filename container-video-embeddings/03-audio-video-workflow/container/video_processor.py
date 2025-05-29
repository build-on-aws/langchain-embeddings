import shutil
import os
import subprocess

def extract_sec_number(filepath: str) -> int:
    """Extract the number after 'sec_' from the filepath."""
    second = filepath.split('sec_')[1].split('.')[0]
    return int(second)


def ffmpeg_check() -> bool:
    try:
        # Check if ffmpeg is installed
        command = ["ffmpeg", "-version"]
        return_code, stdout, stderr = run_ffmpeg_command(command)
        print(f"ffmpeg:",stdout)
        return return_code == 0
    except FileNotFoundError:
        return False

def run_ffmpeg_command(command: list) -> tuple:
    try:

        #print (command)
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def extract_frames(file_location, output_dir, every=1):

    if os.path.exists(output_dir):
        if os.path.islink(output_dir):
            os.unlink(output_dir)
        else:
            shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print ("processing frames...")
    
    command = [
        'ffmpeg',
        '-i', file_location,
        '-vf', 'fps=1,scale=1024:-1',
        '-y',
        f'{output_dir}/sec_%05d.jpg'
    ]
    return_code, stdout, stderr = run_ffmpeg_command(command)
    print ("code:",return_code, "stdout:",stdout, "stderr:", stderr)
    files = os.listdir(output_dir)
    images_files = []
    for file in files:
        #print(f"- {file}")
        images_files.append(f"{output_dir}/{file}")

    return sorted(images_files, key=extract_sec_number)




