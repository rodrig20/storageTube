from tqdm import tqdm
import numpy as np
import cv2
import os
import moviepy.editor as mp

aum = 4


def binarize_img(image_src: np.ndarray) -> np.ndarray:
    """
    Binarize an input image.

    Args:
        image_src (numpy.ndarray): Source image in RGB format.

    Returns:
        numpy.ndarray: Binary image represented as an array of binary pixels.
    """
    # Threshold the image to create a binary representation
    _, array_rgb = cv2.threshold(src=image_src, thresh=256 // 2, maxval=255, type=cv2.THRESH_BINARY)
    
    # Define a white pixel value for comparison
    white_value = np.array([255, 255, 255], dtype=np.uint8)

    # Create an array of binary pixels (1 for white, 0 for non-white)
    binary_pixels = np.all(array_rgb == white_value, axis=-1).astype(int)
    
    return binary_pixels



def read_info_from_file(frame_bytes: bytes) -> tuple[str, int]:
    """
    Read information from a byte sequence.

    Args:
        frame_bytes (bytes): Byte sequence containing name and size information.

    Returns:
        tuple: A tuple containing the decoded name (str) and size (int).
    """
    # Split the byte sequence into name and size
    name, size = frame_bytes.split(b"\0", 2)[:-1]
    return name.decode("utf8"), int(size.decode("utf8"))


def array_to_bytes(array_rgb: np.ndarray, size: int=-1) -> bytes:
    """
    Convert an RGB image array to a byte representation.

    Args:
        array_rgb (numpy.ndarray): RGB image array.
        size (int): Maximum size for the output bytes (default is -1).

    Returns:
        bytes: Byte sequence representing the bit representation of the image.
    """
    # Binarize the RGB image 
    bin_image = binarize_img(array_rgb)
    
    # Resize the bits to one dimension
    bytes_array = bin_image.reshape((-1, 8))
    
    # Pack the bits into bytes
    bytes_array = np.packbits(bytes_array, axis=-1)

    # Convert the bytes array to a bytes string
    bytes_string = bytes_array.tobytes()

    # Limit the size of the output bytes if specified
    if size != -1:
        bytes_string = bytes_string[:size]
    
    return bytes_string


def bytes_to_array(bytes_data_str: bytes, num_rows: int, num_columns: int) -> np.ndarray:
    """
    Convert a byte string to a NumPy array of bits.

    Args:
        bytes_data_str (bytes): Byte string containing binary data.
        num_rows (int): Number of rows for the resulting array.
        num_columns (int): Number of columns for the resulting array.

    Returns:
        numpy.ndarray: NumPy array representing the bits, reshaped into the specified dimensions.
    """
    # Convert the bytes string to a NumPy array
    bytes_data = np.frombuffer(bytes_data_str, dtype=np.uint8)
    
    # Convert the bytes to bits
    bits = np.unpackbits(np.array(bytes_data, dtype=np.uint8))
    
    # Calculate the total number of elements required
    total_elements = (num_rows * num_columns)
    
    # Pad with zeros as needed
    bits = np.pad(bits, (0, total_elements - len(bits)), 'constant', constant_values=(0, 0))

    # Reshape to the desired new shape
    bits = bits.reshape((num_rows, num_columns))
    
    # Create a colored array by scaling bits to 0 or 255
    colored_array = bits * 255
    colored_array = np.stack([colored_array] * 3, axis=-1)

    return colored_array


def create_info_from_file(file_path: str) -> bytes:
    """
    Create byte sequence containing file name and size information.

    Args:
        file_path (str): Path to the file.

    Returns:
        bytes: Byte sequence containing encoded file name and size information.
    """
    # Extract file name from the file path
    file_name = os.path.basename(file_path)
    
    # Get the file size in bytes
    file_byte_size = os.path.getsize(file_path)
    
    # Encode file name and size information into a byte sequence
    full_info = f"{file_name}\0{file_byte_size}\0".encode("utf8")
    
    return full_info


def save(input_file: str, output_video: str) -> None:
    """
    Save frames to a video file.

    Args:
        input_file (str): Path to the input file.
        output_video (str): Path to the output video file.
        aum (int): Upsampling factor (default is 1).
    """
    save_aum = aum

    # Calculate resized width and height
    width = 1280 // save_aum
    height = 720 // save_aum

    # Define codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video, fourcc, 20, (width * save_aum, height * save_aum))

    # Create byte sequence containing file name and size information
    info = create_info_from_file(input_file)

    # Calculate the number of iterations needed for processing
    iteracoes = 1 + (os.path.getsize(input_file) // ((width * height) // 8) + (1 if os.path.getsize(input_file) % ((width * height) // 8) else 0))
    
    # Initialize tqdm progress bar
    pbar = tqdm(total=iteracoes, desc="Save", unit="Frames", unit_scale=True, dynamic_ncols=True, bar_format="[{elapsed}│{desc}: {percentage:3.0f}%▕{bar}▎{n}/{total}│{unit}│{remaining}]")

    # Process and save the first frame
    array = bytes_to_array(info, height, width)
    array = cv2.resize(array, (width * save_aum, height * save_aum), interpolation=cv2.INTER_NEAREST)
    video_writer.write(array)
    pbar.update(1)

    # Process and save the remaining frames
    file = open(input_file, "rb")
    while (bytes_str := file.read((width * height) // 8)):
        array = bytes_to_array(bytes_str, height, width)
        array = cv2.resize(array, (width * save_aum, height * save_aum), interpolation=cv2.INTER_NEAREST)
        video_writer.write(array)
        pbar.update(1)

    # Close tqdm progress bar, file, and release VideoWriter
    pbar.close()
    file.close()
    video_writer.release()


def load(input_video: str, output_folder: str, output_file_name: str="") -> None:
    """
    Load frames from a video and save them to a file.

    Args:
        input_video (str): Path to the input video file.
        output_folder (str): Path to the output folder.
    """
    try:
        # Load the video clip
        clip = mp.VideoFileClip(input_video)

    # Check if video opening was successful
    except OSError:
        print("Error opening the video.")
        return

    # Resize the video clip
    clip = clip.resize(height=720 // aum)

    first_frame = True
    num_bytes = 0

    # Initialize tqdm progress bar
    pbar = tqdm(total=int(clip.fps * clip.duration), desc="Load", unit="Frames", unit_scale=True, dynamic_ncols=True, bar_format="[{elapsed}│{desc}: {percentage:3.0f}%▕{bar}▎{n}/{total}│{unit}│{remaining}]")

    for frame in clip.iter_frames(fps=clip.fps, dtype="uint8"):
        if first_frame:
            first_frame = False
            frame_bytes = array_to_bytes(frame)
            file_name, num_total_bytes = read_info_from_file(frame_bytes)

            # Create the output file path
            if output_file_name != "":
                full_path = os.path.join(output_folder, output_file_name)
                full_path += os.path.splitext(file_name)[1]
            else:
                full_path = os.path.join(output_folder, file_name)

            # Create an empty file
            with open(full_path, "wb+"):
                pass

        else:
            # Convert frame to bytes and write to the output file
            bytes_str = array_to_bytes(frame, (None if (num_total_bytes - num_bytes) > ((frame.shape[0] * frame.shape[1]) // 8) else num_total_bytes - num_bytes))

            with open(full_path, "ab") as file:
                file.write(bytes_str)

            # Update the number of loaded bytes
            loaded_bytes = min(num_total_bytes - num_bytes, (frame.shape[0] * frame.shape[1]) // 8)
            num_bytes += loaded_bytes

        # Update the progress bar
        pbar.update(1)

    # Close the progress bar
    pbar.close()
