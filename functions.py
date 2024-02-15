from tqdm import tqdm
import numpy as np
import cv2
import os
from multiprocessing import Process, Queue
from threading import Thread
import tempfile


aum = 4


def binarize_img(image_src: np.ndarray) -> np.ndarray:
    """
    Binarize an input image.

    Args:
        image_src (numpy.ndarray): Source image in RGB format.

    Returns:
        numpy.ndarray: Binary image represented as an array of binary pixels.
    """
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image_src, cv2.COLOR_RGB2GRAY)

    # Binarize the grayscale image
    _, binary_pixels = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY)

    # Convert binary image to array of binary pixels (0 or 1) with rounding
    binary_pixels = np.around(binary_pixels.astype(np.uint8)).astype(int)

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


def load_frames(input_video: str, dir_name: str, file_name: str, num_of_divisions: int, num_part: int, last_frame_size: int, aum: int, queue: Queue):
    """
    Process frames from a video and save partial results to binary files.

    Args:
        input_video (str): Path to the input video file.
        dir_name (str): Directory where the output binary files will be stored.
        file_name (str): Name of the output binary file.
        num_of_divisions (int): Number of divisions to split the video into.
        num_part (int): Current part number (starting from 0).
        last_frame_size (int): Size of the last frame in the video.
        aum (int): Factor to resize frames.
        queue (Queue): Queue for progress updates.
    """
    # Create output path
    if (num_part):
        path = os.path.join(dir_name, f"{num_part}.bin")
    else:
        path = os.path.join(dir_name, file_name)
    
    # Open video file
    cap = cv2.VideoCapture(input_video)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Get the starter point
    division_poin = ((length//num_of_divisions) * num_part) + 1

    # Set the reader to the given frame number (division_poin)
    cap.set(cv2.CAP_PROP_POS_FRAMES, division_poin)
    final_part = num_of_divisions - 1 ==  num_part
    
    # Counting the number of frames that need to be read
    if final_part:
        count = length - division_poin
    else:
        count = length // num_of_divisions
    
    while count!=0:
        # Read the frame
        ret, frame = cap.read()
        
        if not ret:
            break
        
        count -= 1
        # Resize and process the frame 
        frame = cv2.resize(frame, (1280 // aum, 720 // aum))
        bytes_str = array_to_bytes(frame, (last_frame_size if final_part and count==0 else -1))
        
        # Write info
        with open(path, "ab") as file:
            file.write(bytes_str)
        
        # Update queue
        queue.put(1)
    cap.release()

   
def progress_thread(queue: Queue, size: int) -> None:
    """
    Monitors a progress queue and updates a tqdm progress bar accordingly.

    Args:
        queue (Queue): The queue for monitoring progress updates.
        size (int): The total size of the progress (number of updates).
    """
    i=size-1
    pbar = tqdm(total=i, desc="Load", unit="Frames", unit_scale=True, dynamic_ncols=True, bar_format="[{elapsed}│{desc}: {percentage:3.0f}%▕{bar}▎{n}/{total}│{unit}│{remaining}]")
    # Wait to update the bar
    while i:
        queue.get()
        pbar.update(1)
        i-=1
    pbar.close()


def load(input_video: str, output_folder: str, output_file_name: str="") -> None:
    """
    Load frames from a video and save them to a file.

    Args:
        input_video (str): Path to the input video file.
        output_folder (str): Path to the output folder.
    """
    # Open video file and get first frame
    cap = cv2.VideoCapture(input_video)
    ret, frame = cap.read()
    size = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if ret and size > 1:
        frame = cv2.resize(frame, (1280 // aum, 720 // aum), interpolation=cv2.INTER_NEAREST)
        
        # Get file info from first frame
        frame_bytes = array_to_bytes(frame)
        file_name, num_total_bytes = read_info_from_file(frame_bytes)
        
        # Get the size of the information in the last frame.
        last_frame_size = num_total_bytes - (((size-2) * ((1280 // aum) * (720 // aum))) // 8)

        # Create the output file path
        if output_file_name != "":
            full_path = os.path.join(output_folder, output_file_name)
            full_path += os.path.splitext(file_name)[1]
        else:
            full_path = os.path.join(output_folder, file_name)
        
        # Create temp dir and clear the output_path
        temp_dir = tempfile.mkdtemp()
        open(full_path, "wb").close()
        
        th_num = 2
        if size < th_num:
            th_num = 1
                
        # Create an empty list of processes and a queue
        prs = []
        queue = Queue()
        
        # Start progress bar Thread
        th_bar = Thread(target=progress_thread, args=(queue, size), daemon=True)
        th_bar.start()
        
        for i in range(th_num):
            # Defines where the file information fragments will be stored
            if (i == 0):
                dir_name = output_folder
                file_name = os.path.basename(full_path)
            else:
                dir_name = temp_dir
                file_name = ""

            # Start process to processing a frame
            prs.append(Process(target=load_frames, args=(input_video, dir_name, file_name, th_num, i, last_frame_size, aum, queue)))
            prs[-1].start()
        
        # Wait for all processes
        for i in range(th_num):
            prs.pop(0).join()
            if i:
                # Copy info to th real file
                with open(full_path, "ab") as w_f:
                    with open(os.path.join(temp_dir, f"{i}.bin"), "rb") as r_f:
                        w_f.write(r_f.read())       
        
        # Close progress bar Thread
        th_bar.join()
    else:
        print("Error opening the video.")