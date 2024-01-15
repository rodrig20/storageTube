import functions
import argparse
import os

  
def parse_args():
    parser = argparse.ArgumentParser(description="StorageTube")

    # Adicionando argumentos
    parser.add_argument('--file', type=str, help='Caminho para o arquivo a ser processado')
    parser.add_argument('--mode', choices=['load', 'save'], help='Escolha o modo: "load" para carregar obter o ficheiro original, "save" para guardar me um video')

    # Parseando os argumentos da linha de comando
    args = parser.parse_args()

    if os.path.exists(args.file) and os.path.isfile(args.file):
        if args.mode == "save":
            functions.save(args.file)
        elif args.mode == "load":
            functions.load(args.file)
    else:
        parser.error(f"Não foi possivle encontar nehum ficheiro válido no caminho '{args.file}'. Certifique-se de que o caminho existe e é um ficheiro.")

  
if __name__ == "__main__":
    parse_args()
