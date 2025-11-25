import argparse
import logging
import json

from pathlib import Path
from utils import *
from inventory import Inventory


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
    logger.info(f"********** ARGUMENTOS **********")
    logger.info(f"Diretório de Destino: \"{args.path}\"")
    match (args.op):
        case "dedup":
            logger.info(f"Operação: Detecção de arquivos duplicados na pasta de destino")
        case "inc":
            logger.info(f"Operação: Incorporação de arquivos da entrada na pasta de destino")
    logger.info(f"Deletar arquivos duplicados: {'SIM' if args.delete else 'NÃO'}")
    if args.input_dir:
        logger.info(f"Diretório de Entrada: \"{args.input_dir}\"")
        if args.op == "dedup":
            logger.info("'--op dedup' passado, diretório de  entrada será ignorado")
    if args.inventory_file:
        logger.info(f"Arquivo de inventário: {args.inventory_file}")
    logger.info(f"Algoritmo de Hash: {args.alg}")
    # logger.info(f"Extensões de arquivo a ignorar: {args.exclude}")
    # if args.move_dups is not None:
    #     args.delete = False
    #     logger.info(f"Diretório de quarentena: {args.move_dups}")
    logger.info(f"********************************")


def main():
    parser = argparse.ArgumentParser(description="Duplicate File Finder")

    parser.add_argument("path", help="Diretório de destino dos arquivos")
    parser.add_argument("--op", choices=["dedup", "inc"], help="dedup = Apenas busca arquivos duplicados apenas na pasta de destino;inc = incorpora arquivos do diretório de entrada ao diretório de destino, ignorando duplicados")
    parser.add_argument("--delete", action="store_true", help="Deleta arquivos duplicados encontrados. Se não for passado, apenas imprime os duplicados encontrados", default=False)
    parser.add_argument("-i", "--input-dir", default=None, help="Diretório de entrada dos arquivos (não informar caso queira analisar apenas o diretório de saída)")
    parser.add_argument("--inventory-file", metavar="ARQUIVO", help="Salva e lê (quando disponível) arquivo contendo inventário")
    parser.add_argument("-a", "--alg", default="md5", choices=["md5", "sha1", "sha256"])

    args = parser.parse_args()

    # Configurar log
    setup_logging("duplicate_finder.log")

    # Imprimir parametros
    print_params(args)

    duplicates = None

    # Lê arquivo de inventário
    inventory = None
    if args.inventory_file:
        try:
            inventory = Inventory(Path(args.inventory_file), pre_path=Path(args.path))
        except ValueError as e:
            logger.error(e)
            quit()
    else:
        inventory = Inventory(pre_path=Path(args.path))
    
    # Performa operação
    if args.op == "dedup":
            logger.info("Detecção de arquivos duplicados na pasta de destino")
            file_list = scan_files(Path(args.path))
            duplicates = find_duplicates(file_list, Path(args.path), alg=args.alg, inventory=inventory)
            logger.info(f"Duplicatas encontradas: {len(duplicates)} grupos.")

            # Deleta (ou exibe) arquivos duplicados
            if args.delete:
                logger.info("***** Deletar arquivos duplicados encontrados *****")
                delete_duplicates(duplicates, Path(args.path), inventory)
                logger.info("***************************************************")
            else:
                logger.info("***** Lista de arquivos duplicados encontrados *****")
                for k in duplicates.keys():
                    logger.info(f"Hash '{k}':")
                    for f in duplicates[k]:
                        logger.info(f"Arquivo: {f}")
                logger.info("****************************************************")

    elif args.op == "inc":
            logger.info("Incorporação de arquivos da entrada na pasta de destino")

    # Grava arquivo de inventário atualizado
    if args.inventory_file:
        try:
            inventory.record_file_inventory()
        except e:
            logger.error(f"Não foi possível gravar o arquivo de inventário: {e}")


if __name__ == "__main__":
    main()