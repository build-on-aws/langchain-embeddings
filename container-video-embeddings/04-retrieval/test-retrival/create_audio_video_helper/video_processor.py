import shutil
import os
import subprocess

"""
extract_sec_number(): Extracts second numbers from file paths for frame ordering
ffmpeg_check(): Checks if ffmpeg is installed on the system
run_ffmpeg_command(): Runs ffmpeg commands with proper error handling
extract_frames(): Extracts video frames at regular intervals using ffmpeg
"""
class VideoProcessor:

    def extract_sec_number(self,filepath: str) -> int:
        """Extract the number after 'sec_' from the filepath."""
        second = filepath.split('sec_')[1].split('.')[0]
        return int(second)


    def ffmpeg_check(self) -> bool:
        try:
            # Check if ffmpeg is installed
            command = ["ffmpeg", "-version"]
            return_code, stdout, stderr = self.run_ffmpeg_command(command)
            print(f"ffmpeg:",stdout)
            return return_code == 0
        except FileNotFoundError:
            return False

    def run_ffmpeg_command(self,command: list) -> tuple:
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


    def extract_frames(self,file_location, output_dir, every=1):

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        print ("processing frames...")
        
        #personalize the frame rate by changing the FPS 
        command = [
            'ffmpeg',
            '-v', 'quiet',
            '-stats',
            '-i', file_location,
            '-vf', 'fps=1,scale=1024:-1',
            '-y',
            f'{output_dir}/sec_%05d.jpg'
        ]
        return_code, stdout, stderr = self.run_ffmpeg_command(command)
        print ("code:",return_code, "stdout:",stdout, "stderr:", stderr)
        files = os.listdir(output_dir)
        images_files = []
        for file in files:
            images_files.append(f"{output_dir}/{file}")
        print (f"done processing frames => {len(images_files)}")
        return sorted(images_files, key=self.extract_sec_number)




