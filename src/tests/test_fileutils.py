from unittest import TestCase

import settings

from fileutils import get_project_file_location


class TestFileUtils(TestCase):
    def test_get_subdir_for_file(self):
        settings.ProjectDir = '/project/root'

        self.assertIn("Graphics", get_project_file_location('mypic.jpg'))
        self.assertIn("Graphics", get_project_file_location('mypic.png'))
        self.assertIn("Graphics", get_project_file_location('mypic.jpeg'))
        self.assertIn("Graphics", get_project_file_location('mypic.gif'))
        self.assertIn("Graphics", get_project_file_location('mypic.JPG'))

        self.assertIn("Video", get_project_file_location('myvid.mp4'))
        self.assertIn("Video", get_project_file_location('myvid.webm'))
        self.assertIn("Video", get_project_file_location('myvid.mpg'))
        self.assertIn("Video", get_project_file_location('myvid.avi'))
        self.assertIn("Video", get_project_file_location('myvid.mov'))
        self.assertIn("Video", get_project_file_location('myvid.MP4'))

        self.assertIn("Audio", get_project_file_location('myaudio.aac'))
        self.assertIn("Audio", get_project_file_location('myaudio.mp3'))
        self.assertIn("Audio", get_project_file_location('myaudio.wav'))
        self.assertIn("Audio", get_project_file_location('myaudio.WAV'))

        self.assertIn("File", get_project_file_location('myfile.pdf'))
        self.assertIn("File", get_project_file_location('myfile.h5p'))
        self.assertIn("File", get_project_file_location('myfile.blahblah'))
