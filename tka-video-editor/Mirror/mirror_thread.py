from PyQt6.QtCore import pyqtSignal, QThread
import os
import subprocess

class MirrorThread(QThread):   
    progress_update = pyqtSignal(int)
    result_ready = pyqtSignal(str)

    def __init__(self, source_file, destination_file):
        super().__init__()

        self.source_file = source_file
        self.destination_file = destination_file
        self.process = None

    def run(self):
        # Get the directory, filename and extension of the source file
        dirname, basename = os.path.split(self.source_file)
        name, ext = os.path.splitext(basename)

        # Generate the names for the intermediate and final files
        processed_name = f'{name}_mirrored{ext}'
        self.destination_file = os.path.join(dirname, processed_name)
        temp_filename = os.path.join(dirname, 'processed_temp.mp4')
        crop_filename = os.path.join(dirname, 'crop.mp4')

        # Run the crop detect command and parse the output
        command = ['ffmpeg', '-i', self.source_file, '-vf', 'cropdetect=24:16:0', '-f', 'null', '-']
        result = subprocess.run(command, capture_output=True, text=True)
        crop_line = [line for line in result.stderr.split('\n') if 'crop=' in line]
        crop_values = crop_line[-1][crop_line[-1].index('crop='):].split(' ')[0]

        # Run the commands to process the video
        command = ['ffmpeg', '-i', self.source_file, '-vf', crop_values, '-c:v', 'libx264', '-c:a', 'copy', crop_filename]
        command.insert(1, '-nostdin')
        self.run_command(command)

        command = ['ffmpeg', '-i', crop_filename, '-filter_complex', '[0:v]split[m][a];[a]hflip[b];[m][b]hstack', '-c:v', 'libx264', '-c:a', 'copy', temp_filename]
        command.insert(1, '-nostdin')
        self.run_command(command)

        command = ['ffmpeg', '-i', temp_filename, '-filter_complex', '[0:v]split[m][a];[a]vflip[b];[m][b]vstack', '-c:v', 'libx264', '-c:a', 'copy', self.destination_file]
        command.insert(1, '-nostdin')
        self.run_command(command)

        # Clean up the temporary files
        os.remove(temp_filename)
        os.remove(crop_filename)

        # Signal that the process is done
        self.result_ready.emit(self.destination_file)

    def run_command(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        line = b""
        progress = 0

        while True:
            byte = process.stdout.read(1)
            if byte:
                line += byte
                if byte == b'\n':
                    print(line.decode().strip())  # print the line for debugging
                    line = b""
                    progress += 1
                    self.progress_update.emit(progress)
            elif process.poll() is not None:
                break

        process.poll()
