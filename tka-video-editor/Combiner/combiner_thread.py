from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import numpy as np
import traceback
from PIL import Image
import cv2


def merge(image_path, video_path, output_path, preserve_aspect_ratio=True, progress_callback=None, stop_flag_callback=None):
    try:
        # Load the image
        image = Image.open(image_path)

        if image is None:
            raise ValueError(f"Failed to load the image from: {image_path}")
            
        image = np.array(image)
        # Change image color order from RGB to BGR (to make it compatible with OpenCV)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Obtain image dimensions
        image_height, image_width, _ = image.shape

        # Open the video
        video = cv2.VideoCapture(video_path)
        video_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_fps = int(video.get(cv2.CAP_PROP_FPS))
        video_frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

        if preserve_aspect_ratio:
            # Maintain aspect ratio, add black borders to make the image square
            max_dim = max(image_width, image_height)
            square_image = np.zeros((max_dim, max_dim, 3), dtype=np.uint8)

            y_offset = (max_dim - image_height) // 2
            x_offset = (max_dim - image_width) // 2
            square_image[y_offset:y_offset+image_height, x_offset:x_offset+image_width] = image

            # Now resize the square image to the video size
            resized_image = cv2.resize(square_image, (video_width, video_height), interpolation=cv2.INTER_LANCZOS4)
            new_image_width = video_width
        else:
            # Resize the image to match the video height while keeping the aspect ratio
            new_image_width = int(image_width * (video_height / image_height))
            resized_image = cv2.resize(image, (new_image_width, video_height), interpolation = cv2.INTER_LANCZOS4)
        
        # Set up the video writer with a new frame size to accommodate the image and video side by side
        combined_width = video_width + new_image_width
        fourcc = cv2.VideoWriter(*'mp4v')
        output = cv2.VideoWriter(output_path, fourcc, video_fps, (combined_width, video_height))

        # Process the frames
        current_frame = 0
        while video.isOpened():
            ret, frame = video.read()
            if not ret:
                break

            if frame is None:
                raise ValueError("Failed to read a frame from the video")

            # Check if a stop was requested
            if stop_flag_callback is not None and stop_flag_callback():
                print("Stopping the video merge process...")
                break

            # Combine the resized image and video frame side by side
            combined_frame = np.hstack((resized_image, frame))

            output.write(combined_frame)

            current_frame += 1
            if progress_callback:
                progress = int((current_frame / video_frame_count) * 100)
                progress_callback(progress)

        # Close the video files
        video.release()
        output.release()

    except Exception as e:
        print("Error in merge:", str(e))
        print(traceback.format_exc())
        
class MergeFiles(QThread):
    progress_signal = pyqtSignal(int)
    stopped = pyqtSignal()

    def __init__(self, image_path=None, video_path=None, output_path=None, preserve_aspect_ratio=True, parent=None):
        super().__init__(parent)

        self.image_path = image_path
        self.video_path = video_path
        self.output_path = output_path
        self.preserve_aspect_ratio = preserve_aspect_ratio
        self.stop_flag = False

    def run(self):
        merge(
            self.image_path, 
            self.video_path, 
            self.output_path, 
            self.preserve_aspect_ratio, 
            self.progress_signal.emit, 
            self.get_stop_flag
        )
        self.stopped.emit()

    def get_stop_flag(self):
        return self.stop_flag