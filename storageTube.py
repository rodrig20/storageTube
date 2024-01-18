import youtube_functions
import functions
import argparse
import requests
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def criar_caminho(caminho):
    try:
        partes_do_caminho = caminho.split(os.path.sep)
        caminho_atual = ''
        for parte in partes_do_caminho:
            caminho_atual = os.path.join(caminho_atual, parte)
            if not os.path.exists(caminho_atual):
                os.mkdir(caminho_atual)
        return True
    except OSError:
            
        return False


def is_valid_path_string(path_string, type):
    try:
        Path(path_string)
        if type == ".mp4" and not path_string.endswith(".mp4"):
            if path_string.endswith("\\") or path_string.endswith("/") or path_string == "":
                path_string += "output_video.mp4"
            else:
                if not os.path.exists(path_string):
                    os.makedirs(path_string)
                path_string += "\\output_video.mp4"
                
        if type == ".mp4" and not path_string.endswith(".mp4"):
            if path_string.endswith("\\") or path_string.endswith("/") or path_string == "":
                path_string += "output_video.mp4"
            else:
                if not os.path.exists(path_string):
                    os.makedirs(path_string)
                path_string += "\\output_video.mp4"
                
        elif type == "folder":
            if not criar_caminho(path_string):
                print(f"A string '{path_string}' não é um {type} válido.")
                return False

        return path_string
    except Exception as e:
        print(f"A string '{path_string}' não é um {type} válido.\nErro: {e}")
        return False


def is_valid_file(arg):
    is_valid_archive(arg)
    if not os.path.isfile(arg):
        print(f'O arquivo {arg} não existe!')
    return arg


def is_valid_archive(arg):
    if not os.path.exists(arg):
        print(f'O arquivo/pasta {arg} não existe!')
    return arg


def is_valid_youtube_id(video_id):
    checker_url = "https://www.youtube.com/oembed?url="
    video_url = checker_url + video_id

    request = requests.get(video_url)
    
    return request.status_code == 200

  
def parse_args():
    parser = argparse.ArgumentParser(description="StorageTube")

    # Adicionando argumentos
    # parser.add_argument('-p', '--path', type=str, help='Caminho para o arquivo a ser processado')
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-l', '--load', dest='load', type=is_valid_file, metavar='VIDEO', help='Caminho para o video a ser Carregado')
    mode_group.add_argument('-s', '--save', dest='save', type=is_valid_archive, metavar='ARQUIVO/FOLDER', help='Caminho para o ficheiro/pasta a ser Guardado')
    mode_group.add_argument('-y', '--youtube-id', dest='youtube_id', type=str, metavar='YOUTUBE_ID', help='Id de um video do Youtube')
    
    parser.add_argument('-z', '--zip', action='store_true', help='Indica se o ficheiro vai ser comprimido primeiro')
    parser.add_argument('-f', '--output-folder', type=str, dest="out_folder", default=".\\", metavar='OUTPUT FOLDER', help='Caminho para a pasta de saida')
    parser.add_argument('-n', '--output-name', type=str, dest="out_name", default=".", metavar='OUTPUT FILE NAME', help='Nome do arquivo gerado sem extensão')

    # Parseando os argumentos da linha de comando
    args = parser.parse_args()
    if args.out_name == ".":
        args.out_name = None
        out_name = os.path.splitext(os.path.basename(Path(args.save or args.load or args.youtube_id).name))[0]
    else:
        out_name = args.out_name
    
    full_path = os.path.join(args.out_folder, out_name)
    
    if args.save and os.path.exists(args.save):
        if args.zip and os.path.isdir(args.save):
            print("A flag --zip não pode ser usada em pastas")
        else:
            if os.path.isfile(args.save) and args.zip:
                zip_path = full_path + ".zip"
                criar_caminho(os.path.dirname(zip_path))
                print("A comprimir o ficheiro")
                with ZipFile(zip_path, 'w') as zip_object:
                    zip_object.write(args.save, Path(args.save).name, ZIP_DEFLATED)
                args.save = zip_path

            elif os.path.isdir(args.save):
                zip_path = full_path + ".zip"
                criar_caminho(os.path.dirname(zip_path))
                print("A comprimir a pasta")
                with ZipFile(zip_path, 'w') as zip_object:
                    zip_object.write(args.save, Path(args.save).name, ZIP_DEFLATED)
                args.save = zip_path
            criar_caminho(os.path.dirname(full_path))
            functions.save(args.save, full_path + ".mp4")
                
    elif args.load and os.path.exists(args.load):
        if args.zip:
            print("A flag --zip não pode ser usada em load")
        elif not args.load.endswith(".mp4"):
            print(f"Parece que o caminho {args.load} não é um ficheiro .mp4")
        else:
            criar_caminho(args.out_folder)
            functions.load(args.load, args.out_folder, output_file_name=args.out_name)
        
    elif args.youtube_id:
        if args.youtube_id.startswith("youtu"):
            video_url = "https://" + args.youtube_id
        elif not args.youtube_id.startswith("https://youtu") and not args.youtube_id.startswith("http://youtu"):
            video_url = "https://youtu.be/" + args.youtube_id
        else:
            video_url = args.youtube_id
        if is_valid_youtube_id(video_url):
            video_path = youtube_functions.download(video_url, args.out_folder, args.out_name + ("" if args.out_name is None else ".mp4"))
            if video_path:
                functions.load(video_path, args.out_folder, output_file_name=args.out_name)
                
            else:
                print(f'Não foi possivel encontar um video em {video_url}!')
                
        else:
            print(f'Não foi possivel encontrar um video com id {video_url[17:]}!')

  
if __name__ == "__main__":
    parse_args()
