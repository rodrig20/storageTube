from pytube import YouTube
from pytube.exceptions import VideoUnavailable, RegexMatchError
import os


def download(video_url: str, output_folder: str="./", output_file_name: str="") -> str:
    """
    Download a YouTube video.

    Args:
        video_url (str): URL of the YouTube video.
        output_folder (str): Path to the output folder (default is the current folder).
        output_file_name (str): Name of the output file (default is the video title).

    Returns:
        str: Full path to the downloaded video file if successful, empty string otherwise.
    """
    try:
        # Attempt to create an instance of the YouTube object
        yt = YouTube(video_url)
        print(f"Downloading {yt.title}")
        video = yt.streams.filter(res="720p").first()

        if video:
            video.download(output_folder, filename=output_file_name)
            # If no errors occurred up to this point, assume the video is valid
            return os.path.join(output_folder, (yt.title + ".mp4") if output_file_name == "" else output_file_name)
        else:
            return ""

    except (VideoUnavailable, RegexMatchError):
        return ""
