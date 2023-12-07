from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QProgressBar, QFileDialog, QSlider
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt
from .mirror_thread import MirrorThread
import os

class MirrorTab(QWidget):
    def __init__(self, parent=None):
        super(MirrorTab, self).__init__(parent)
        
        self.setWindowTitle("PyQt Video Player")

        self.media_player: QMediaPlayer = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        self.openButton = QPushButton("Open Video")
        self.openButton.clicked.connect(self.open_file)

        self.mirrorButton = QPushButton("Mirror")
        self.mirrorButton.clicked.connect(self.process_and_play)
        self.mirrorButton.setEnabled(False)

        self.playButton = QPushButton("Play")
        self.playButton.clicked.connect(self.play_pause)
        self.playButton.setEnabled(False)

        self.positionSlider = QSlider(Qt.Orientation.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.set_position)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)  # Indeterminate mode
        self.progressBar.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.openButton)
        layout.addWidget(self.mirrorButton)
        layout.addWidget(self.video_widget)
        layout.addWidget(self.playButton)
        layout.addWidget(self.positionSlider)
        layout.addWidget(self.progressBar)

        self.setLayout(layout)

        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.hasVideoChanged.connect(self.update_play_button_text)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)

        self.worker = None



    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename != '':
            url = QUrl.fromUserInput(os.path.abspath(filename))
            self.media_player.setSource(QUrl.fromLocalFile(url))
            self.filename = filename
            self.mirrorButton.setEnabled(True)
            self.video_widget.show()
            self.media_player.setPosition(0)

    def process_and_play(self):
        import tempfile
        self.media_player.pause()
        self.mirrorButton.setEnabled(False)

        filename = self.filename

        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_filename = temp_file.name
        temp_file.close()

        self.worker = MirrorThread(filename, temp_filename)
        self.worker.progress_update.connect(self.update_progress_bar)
        self.worker.result_ready.connect(self.finalize_mirror)
        self.worker.start()

        self.progressBar.setRange(0, 100)  # Percent mode
        self.progressBar.show()  # Show the progress bar


    def update_progress_bar(self, progress):
        self.progressBar.setValue(progress)

    def finalize_mirror(self, processed_filename):
        self.progressBar.hide()  # Hide the progress bar
        url = QUrl.fromUserInput(os.path.abspath(processed_filename))
        self.media_player.setSource(QUrl.fromLocalFile(url))
        self.playButton.setEnabled(True)
        self.mirrorButton.setEnabled(True)
        self.progressBar.setRange(0, 0)  # Reset to indeterminate mode


    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.playButton.setEnabled(True)
            if self.media_player.position() == 0:  # check if it's the first time the media is being loaded
                self.media_player.pause()
                
    def update_play_button_text(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playButton.setText("Pause")
        else:
            self.playButton.setText("Play")
            
    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def position_changed(self, position):
        self.positionSlider.setValue(position)

    def duration_changed(self, duration):
        self.positionSlider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)
