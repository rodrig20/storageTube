from pytube import YouTube
from pytube.exceptions import VideoUnavailable, RegexMatchError
import os


def download(video_url, output_folder="./", output_file_name=None):
    try:
        # Tenta criar uma instância do objeto YouTube
        yt = YouTube(video_url)
        print(f"A fazer o download de {yt.title}")
        video = yt.streams.filter(res="720p").first()
        
        if video:
            video.download(output_folder, filename=output_file_name)
        # Se nenhum erro ocorreu até este ponto, assume-se que o vídeo é válido
            return os.path.join(output_folder, yt.title if output_file_name is None else output_file_name)
        else:
            return False

    except (VideoUnavailable, RegexMatchError):
        return False
