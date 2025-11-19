import argparse
import logging
import json

from utils import *


# ==================================================================
# Configura Logging
# ==================================================================
logger=logging.getLogger("duplicate_finder")
logger.setLevel(logging.DEBUG)


def setup_logging(log_file):
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"LOG iniciado: {log_file}")


# ==================================================================
# CLI
# ==================================================================
def print_params(args):
    #print(args)
    logger.info(f"Diretório de Saída: \"{args.path}\"")
    if args.input_dir is None:
        logger.info("Analisando apenas diretório de saída em busca de duplicatas")
    else:
        logger.info(f"Diretório de Entrada: \"{args.input_dir}\"")
    logger.info(f"Algoritmo de Hash: {args.alg}")
    logger.info(f"Extensões de arquivo a ignorar: {args.exclude}")
    if args.move_dups is not None:
        args.delete = False
        logger.info(f"Diretório de quarentena: {args.move_dups}")
    logger.info(f"Deletar arquivos duplicados: {'Sim' if args.delete else 'Não'}")


def main():
    parser = argparse.ArgumentParser(description="Duplicate File Finder")

    parser.add_argument("path", help="Diretório de saída dos arquivos")
    parser.add_argument("-i", "--input-dir", default=None, help="Diretório de entrada dos arquivos (não informar caso queira analisar apenas o diretório de saída)")
    parser.add_argument("--inventory-file", metavar="ARQUIVO", help="Salva e lê (quando disponível) arquivo contendo inventário na saída")
    parser.add_argument("-a", "--alg", default="md5", choices=["md5", "sha1", "sha256"])
    parser.add_argument("--exclude", nargs="*", default=[], help="Extensões para ignorar (.tmp .mp4 ...)")
    parser.add_argument("--delete", action="store_true", help="Deleta arquivos duplicados (será mantido o primeiro arquivo encontrado)")
    parser.add_argument("--move-dups", metavar="PASTA", help="Move arquivos duplicados para uma pasta de quarentena (sobrepõe --delete)")

    args = parser.parse_args()

    # Configurar log
    setup_logging("duplicate_finder.log")

    # Imprimir parametros
    print_params(args)

    duplicates = None

    # Lê arquivo de inventário
    inventory = None
    if args.inventory_file:
        inventory = read_inventory(args.inventory_file)

    # Lista arquivos na saída
    logger.info(f"Escaneando pasta de saída: \"{args.path}\"")
    list_output = scan_files(args.path, exclude_ext=[e.lower() for e in args.exclude])

    # Lista arquivos na pasta de entrada
    list_input = None
    if args.input_dir:
        list_input = scan_files(args.input_dir, exclude_ext=[e.lower() for e in args.exclude])
    else:
        inventory, duplicates = find_duplicates(list_output, args.path, alg=args.alg, inventory=inventory)
    
    # Encontrar arquivos duplicados
    inventory, duplicates = find_duplicates(list_output, args.path, alg=args.alg, inventory=inventory)
    logger.info(f"Duplicatas encontradas: {len(duplicates)} grupos.")
    
    # Deleta arquivos duplicados
    if args.delete:
        #delete_duplicates(duplicates, inventory)
        pass
    
    # Move arquivos duplicados
    if args.move_dups:
        # move_duplicates(duplicates)
        pass

    if args.inventory_file:
        dump_inventory(inventory, args.inventory_file)


if __name__ == "__main__":
    main()