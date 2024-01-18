# StorageTube - Video Encoding and Decoding Application

## Overview

StorageTube is a Python application that provides functionalities for encoding files into videos and decoding them back to the original files. Additionally, it allows users to download files from YouTube and reverse the process.

## Files

### 1. youtube_functions.py
   - Contains functions related to downloading videos from YouTube using the Pytube library.
   - Provides a `download` function to download YouTube videos.

### 2. storageTube.py
   - Main script to execute the StorageTube application.
   - Integrates functionalities from `youtube_functions.py` and `functions.py`.
   - Handles command-line arguments using `argparse` for various operations, including loading, saving, compressing, and downloading from YouTube.
   - Utilizes custom functions and modules for specific tasks.

### 3. functions.py
   - Contains functions for processing video frames, converting them to binary data, and saving/loading them.
   - Includes functions for binarizing images, handling byte sequences, and saving/loading video frames.
   - Used by `storageTube.py` for video-related operations.

### 4. requirements.txt
   - Specifies the required Python libraries and their versions for running the StorageTube application.

## Usage

To run the StorageTube application, execute the following command:

```bash
python storageTube.py [arguments]
```

Replace `[arguments]` with the desired command-line options based on the operation you want to perform (e.g., encoding, decoding, downloading from YouTube).

## Features

- **File Encoding and Decoding:**
  - Encode files into video frames.
  - Decode video frames back to the original files.

- **YouTube Integration:**
  - Download files from YouTube.
  - Reverse the encoding process for downloaded YouTube videos.

## Dependencies

Ensure you have the required dependencies installed by running:

```bash
pip install -r requirements.txt
```

## Example Commands

### Encode File to Video
```bash
python storageTube.py -s input_file.txt -f output_folder -n output_file_name -z
```

### Decode Video to File
```bash
python storageTube.py -l input_video.mp4 -f output_folder
```

### Download from YouTube and Decode
```bash
python storageTube.py -y youtube_video_id -f output_folder
```

For detailed information on command-line options, run:

```bash
python storageTube.py -h
```