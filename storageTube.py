import youtube_functions
import functions
import argparse
import requests
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def create_path(path: str) -> bool:
    """
    Create path to a certain folder

    Args:
        path (str): Path to folder

    Returns:
        bool: success
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


def is_valid_file(path: str, parser: argparse.ArgumentParser) -> str:
    """
    Check if is a file.

    Args:
        path (str): Path to file
        parser: ArgumentParser instance

    Returns:
        str: Validated file path

    Raises:
        ArgumentTypeError: If the file does not exist
    """
    is_valid_archive(path, parser)
    if not os.path.isfile(path):
        parser.error(f'The file {path} does not exist.')
    return path


def is_valid_archive(path: str, parser: argparse.ArgumentParser) -> str:
    """
    Check if the file/folder exists.

    Args:
        path (str): Path to file/folder
        parser: ArgumentParser instance

    Returns:
        str: Validated path

    Raises:
        ArgumentTypeError: If the file/folder does not exist
    """
    if not os.path.exists(path):
        parser.error(f'The file/folder {path} does not exist.')
    return path


def is_valid_youtube_id(youtube_url: str) -> bool:
    """
    Check if the YouTube video ID is valid.

    Args:
        youtube_url (str): YouTube video URL

    Returns:
        bool: True if the video ID is valid, False otherwise
    """
    # Create youtube checker url
    checker_url = "https://www.youtube.com/oembed?url="
    youtube_checker_url = checker_url + youtube_url

    request: requests.Response = requests.get(youtube_checker_url)
    
    # Check response
    return request.status_code == 200


def get_youtube_url(youtube_id: str) -> str:
    """
    Get the complete YouTube URL from a given ID.

    Args:
        youtube_id (str): YouTube video ID or URL fragment

    Returns:
        str: Complete YouTube URL
    """
    if youtube_id.startswith("youtu"):
        youtube_url = "https://" + youtube_id
    elif not youtube_id.startswith("https://youtu") and not youtube_id.startswith("http://youtu"):
        youtube_url = "https://youtu.be/" + youtube_id
    else:
        youtube_url = youtube_id
    
    return youtube_url


def parse_args() -> None:
    """
    Parse command-line arguments for the StorageTube script.

    The script allows for various operations related to videos, including loading, saving,
    compressing, and downloading from YouTube.

    Command-line arguments:
    - -z, --zip: Indicates whether the file will be compressed first.
    - -f, --output-folder: Path to the output folder.
    - -n, --output-name: Name of the file generated.
    - -l, --load: Path to the video (load mode).
    - -s, --save: Path to the file/folder to be saved (save mode).
    - -y, --youtube-id: YouTube video ID (YouTube mode).
    """
    parser = argparse.ArgumentParser(description="StorageTube")

    # Add arguments
    parser.add_argument('-z', '--zip', action='store_true', help='Indicates whether the file will be compressed first.')
    parser.add_argument('-f', '--output-folder', type=str, dest="out_folder", default=".\\", metavar='OUTPUT FOLDER', help='Path to the output folder')
    parser.add_argument('-n', '--output-name', type=str, dest="out_name", default=".", metavar='OUTPUT FILE NAME', help='Name of file generated')
    # Add mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-l', '--load', dest='load', type=lambda val: is_valid_file(val, parser), metavar='VIDEO', help='Path to the video')
    mode_group.add_argument('-s', '--save', dest='save', type=lambda val: is_valid_archive(val, parser), metavar='ARQUIVO/FOLDER', help='Path to the file/folder to be Saved')
    mode_group.add_argument('-y', '--youtube-id', dest='youtube_id', type=str, metavar='YOUTUBE_ID', help='YouTube video ID')
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Process output path
    if args.out_name == "." or args.out_name == "":  # Default name
        args.out_name = ""
        out_name = os.path.splitext(os.path.basename(Path(args.save or args.load or args.youtube_id).name))[0]
    else:
        out_name = args.out_name
        
    full_path = os.path.join(args.out_folder, out_name)
    
    # If in save mode
    if args.save and os.path.exists(args.save):
        # If the --zip flag is used on a folder
        if args.zip and os.path.isdir(args.save):
            parser.error("The flag --zip cannot be used on folder.")
        else:
            # If it is necessary to compress the output path.
            if (os.path.isfile(args.save) and args.zip) or (os.path.isdir(args.save)):
                zip_path = full_path + ".zip"
                # Create the output folder
                if create_path(os.path.dirname(zip_path)):
                    print("Compressing...")
                    # Create zip file
                    with ZipFile(zip_path, 'w') as zip_object:
                        zip_object.write(args.save, Path(args.save).name, ZIP_DEFLATED)
                    args.save = zip_path
                else:
                    parser.error("A problem occurred while creating the output folder.")
            else:
                # Create the path
                if not create_path(os.path.dirname(full_path)):
                    parser.error("A problem occurred while creating the output folder.")
            
            # Save file on video
            functions.save(args.save, full_path + ".mp4")
    
    # If in load mode
    elif args.load and os.path.exists(args.load):
        # If the --zip flag is used load mode
        if args.zip:
            parser.error("The flag --zip cannot be used on load mode.")
        # If the file is not an mp4 file
        elif not args.load.endswith(".mp4"):
            parser.error(f"It seems that the path {args.load} is not an mp4 file.")
        else:
            # Create the path
            if not create_path(args.out_folder):
                parser.error("A problem occurred while creating the output folder.")
                
            # Load mp4
            functions.load(args.load, args.out_folder, output_file_name=args.out_name)
        
    # If in youtube mode
    elif args.youtube_id:
        # Process the id to get youtube url
        youtube_url = get_youtube_url(args.youtube_id)
        
        # Check if youtube_url is válid and exists
        if is_valid_youtube_id(youtube_url):
            # Download youtube video
            video_path = youtube_functions.download(youtube_url, args.out_folder, args.out_name + ("" if args.out_name == "" else ".mp4"))
            if video_path:
                # Load downloaded mp4
                functions.load(video_path, args.out_folder, output_file_name=args.out_name)
                
            else:
                parser.error(f'Could not find a video at {youtube_url}.')
                
        else:
            parser.error(f'The video with id {youtube_url[17:]} is invalid.')

  
if __name__ == "__main__":
    parse_args()
