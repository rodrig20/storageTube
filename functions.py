from tqdm import tqdm
import numpy as np
import cv2
import os
import moviepy.editor as mp

aum = 4


def binarize_img(image_src):
    _, array_rgb = cv2.threshold(src=image_src, thresh=256 // 2, maxval=255, type=cv2.THRESH_BINARY)
    valor_branco = np.array([255, 255, 255], dtype=np.uint8)

    pixels_binarios = np.all(array_rgb == valor_branco, axis=-1).astype(int)
    
    return pixels_binarios


def read_info_from_file(frame_bytes):
    name, size = frame_bytes.split(b"\0", 2)[:-1]
    return name.decode("utf8"), int(size.decode("utf8"))
    

def array_to_bits(array_rgb, size=-1):
    bin_image = binarize_img(array_rgb)
    
    # Redimensionar os bits para uma dimensão
    bytes_array = bin_image.reshape((-1, 8))
    
    bytes_array = np.packbits(bytes_array, axis=-1)

    bytes_string = bytes_array.tobytes()

    if size != -1:
        bytes_string = bytes_string[:size]
    
    return bytes_string


def bits_to_array(bytes_data_str, num_rows, num_columns):
    # Convertendo a string de bytes para um array NumPy
    bytes_data = np.frombuffer(bytes_data_str, dtype=np.uint8)
    
    # Converter os bytes para bits
    bits = np.unpackbits(np.array(bytes_data, dtype=np.uint8))
    
    # Calcular o número total de elementos necessário
    total_elements = (num_rows * num_columns)
    
    # Preenchendo conforme necessário
    bits = np.pad(bits, (0, total_elements - len(bits)), 'constant', constant_values=(0, 0))

    # Redimensionando para a nova forma desejada
    bits = bits.reshape((num_rows, num_columns))
    
    colored_array = bits * 255
    colored_array = np.stack([colored_array] * 3, axis=-1)
    
    # return colored_array.repeat(aum, axis=0).repeat(aum, axis=1)
    return colored_array


def create_info_from_file(file_path):
    file_name = file_path.split("/")[-1].split("\\")[-1]
    file_byte_size = os.path.getsize(file_path)
    full_info = f"{file_name}\0{file_byte_size}\0".encode("utf8")
    
    return full_info


def save(input_file, output_video):
    save_aum = aum
    
    width = 1280 // save_aum
    height = 720 // save_aum

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
    video_writer = cv2.VideoWriter(output_video, fourcc, 20, (width * save_aum, height * save_aum))
        
    info = create_info_from_file(input_file)
    
    iteracoes = 1 + (os.path.getsize(input_file) // ((width * height) // 8) + (1 if os.path.getsize(input_file) % ((width * height) // 8) else 0))
    barra_progresso = tqdm(total=iteracoes, desc="Save", unit="Frames", unit_scale=True, dynamic_ncols=True, bar_format="[{elapsed}│{desc}: {percentage:3.0f}%▕{bar}▎{n}/{total}│{unit}│{remaining}]")
    
    array = bits_to_array(info, height, width)
    array = cv2.resize(array, (width * save_aum, height * save_aum), interpolation=cv2.INTER_NEAREST)
    video_writer.write(array)
    barra_progresso.update(1)
    file = open(input_file, "rb")
    while (bytes_str := file.read((width * height) // 8)):
        array = bits_to_array(bytes_str, height, width)
        array = cv2.resize(array, (width * save_aum, height * save_aum), interpolation=cv2.INTER_NEAREST)
        video_writer.write(array)
        barra_progresso.update(1)
    barra_progresso.close()
    file.close()
    video_writer.release()


def load(input_video, output_folder, output_file_name=None):
    try:
        clip = mp.VideoFileClip(input_video)
    
    # Verifique se a abertura do vídeo foi bem-sucedida
    except OSError:
        print("Erro ao abrir o vídeo.")
        return
    
    clip = clip.resize(height=720 // aum)
    
    first_frame = True
    num_bytes = 0
    barra_progresso = tqdm(total=int(clip.fps * clip.duration), desc="Load", unit="Frames", unit_scale=True, dynamic_ncols=True, bar_format="[{elapsed}│{desc}: {percentage:3.0f}%▕{bar}▎{n}/{total}│{unit}│{remaining}]")
    
    for frame in clip.iter_frames(fps=clip.fps, dtype="uint8"):
        if first_frame:
            first_frame = False
            frame_bytes = array_to_bits(frame)
            file_name, num_total_bytes = read_info_from_file(frame_bytes)
            
            if output_file_name is not None:
                full_path = os.path.join(output_folder, output_file_name)
                full_path += os.path.splitext(file_name)[1]
            else:
                full_path = os.path.join(output_folder, file_name)
            with open(full_path, "wb+"):
                pass

        else:
            bytes_str = array_to_bits(frame, (None if (num_total_bytes - num_bytes) > ((frame.shape[0] * frame.shape[1]) // 8) else num_total_bytes - num_bytes))
            
            with open(full_path, "ab") as file:
                file.write(bytes_str)
            loaded_bytes = min(num_total_bytes - num_bytes, (frame.shape[0] * frame.shape[1]) // 8)
            num_bytes += loaded_bytes
        barra_progresso.update(1)
        
    barra_progresso.close()
