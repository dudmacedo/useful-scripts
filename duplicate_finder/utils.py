import csv
import hashlib
import json
import logging
import os
from collections import defaultdict
from pathlib import Path
try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False


logger=logging.getLogger("duplicate_finder")
logger.setLevel(logging.DEBUG)


def compute_hash(path, alg="md5", fast = False, chunk_size=1024*1024):
    """
    Calcula o hash do arquivo.

    Args:
        path (str): Caminho do arquivo
        alg="md5" (str): Algoritmo de hash (md5, sha1, sha256)
        fast=True (bool): Lê apenas os primeiros 4KB de dados
        chunk_size=1024*1024 (int): Tamanho dos blocos ao calcular o hash

    Returns:
        str: O hash do arquivo informado
    """
    hash = hashlib.new(alg)

    with open(path, "rb") as f:
        if fast:
            hash.update(f.read(4096))
        else:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash.update(chunk)
    
    return hash.hexdigest()


def scan_files(path, exclude_ext=None):
    """
    Varre diretório e retorna lista de arquivos

    Args:
        path (str): Caminho do diretório
        exclude_ext=None ([]): Lista de extensões dos tipos de arquivo a ignorar

    Returns:
        []: Lista de arquivos encontrados
    """
    basedir = Path(path)
    files = []

    for p in basedir.rglob("*"):
        if p.is_file():
            if exclude_ext and p.suffix.lower() in exclude_ext:
                continue
            files.append(p)

    return files


def find_duplicates(files, output_dir, alg="md5", inventory=None):
    logger.info("Iniciando busca por arquivos duplicados..")

    if not inventory:
        inventory = dict()

    by_size = defaultdict(list)
    for k in inventory.keys():
        by_size[inventory[k]["size"]].append()
    for f in files:
        try:
            size = f.stat().st_size
            fkey = str(Path(f).relative_to(Path(output_dir)))
            inventory[fkey] = {}
            inventory[fkey]['size'] = size
            by_size[size].append(f)
        except FileNotFoundError:
            logger.warning(f"Arquivo inacessível: {f}")
    
    # partial_hashes = defaultdict(list)
    # iterable = by_size.items()
    # if USE_TQDM:
    #     iterable = tqdm(iterable, desc="Hash parcial")
    # for size, flist in iterable:
    #     if len(flist) < 2:
    #         continue
    #     for f in flist:
    #         try:
    #             h = compute_hash(f, alg=alg, fast=True)
    #             fkey = str(Path(f).relative_to(Path(output_dir)))
    #             inventory[fkey]['hash_fast'] = h
    #             inventory[fkey]['alg'] = alg
    #             partial_hashes[(size, h)].append(f)
    #         except FileNotFoundError:
    #             logger.warning(f"Arquivo inacessível: {f}")

    # full_hashes = defaultdict(list)
    # iterable = partial_hashes.items()
    # if USE_TQDM:
    #     iterable = tqdm(iterable, desc="Hash completo")
    # for (size, ph), flist in iterable:
    #     if len(flist) < 2:
    #         continue
    #     for f in flist:
    #         try:
    #             h = compute_hash(f, alg=alg, fast=False)
    #             fkey = str(Path(f).relative_to(Path(output_dir)))
    #             inventory[fkey]['hash_full'] = h
    #             full_hashes[h].append(f)
    #         except FileNotFoundError:
    #             logger.warning(f"Arquivo inacessível: {f}")

    # duplicates = {h: flist for h, flist in full_hashes.items() if len(flist) > 1}
    
    return inventory, None # duplicates


def delete_duplicates(duplicates, inventory=None):
    for files in duplicates.values():
        keep = files[0]
        logger.info(f"Manter: {keep}")

        for f in files[1:]:
            try:
                os.remove(f)
                if inventory and str(f) in inventory.keys():
                    inventory.pop(str(f))
                logger.info(f"[DEL] {f}")
            except:
                logger.error(f"Falha ao deletar {f}")


##############################################################
# Controle do arquivo de inventário
##############################################################
def dump_inventory(inventory, path):
    output = []
    for k in inventory.keys():
        output.append({
            "path": k,
            "size": inventory[k]["size"],
            "hash_fast": inventory[k]["hash_fast"] if "hash_fast" in inventory[k].keys() else None,
            "hash_full": inventory[k]["hash_full"] if "hash_full" in inventory[k].keys() else None,
            "alg": inventory[k]["alg"] if "alg" in inventory[k].keys() else None
        })

    dump_path = Path(path)
    logger.info(f"Salvando arquivo de inventário em {path} ...")

    # Grava CSV
    if dump_path.suffix.lower() == ".csv":
        with open(dump_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["path", "size", "hash_fast", "hash_full", "alg"])
            for item in output:
                writer.writerow([item["path"], item["size"], item["hash_fast"], item["hash_full"], item["alg"]])

        logger.info(f"Inventário salvo em: {dump_path}")

    # Grava JSON
    elif dump_path.suffix.lower() == ".json":
        with open(dump_path, "w", encoding="utf-8") as jsonfile:
            json.dump(inventory, jsonfile, indent=4, ensure_ascii=False)
        logger.info(f"Inventário salvo em: {dump_path}")

    else:
        logger.warning("Extensão para o arquivo de inventário inválida. Use .csv ou .json")


def read_inventory(path):
    dump_path = Path(path)
    inventory = dict()
    logger.info(f"Lendo inventário gravado em {path}")

    if not os.path.exists(dump_path):
        logger.info(f"Arquivo não existe, será criado um novo arquivo")
        return None

    # Lê CSV
    if dump_path.suffix.lower() == ".csv":
        with open(dump_path, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == "path":
                    continue
                inventory[row[0]] = {"size": row[1], "hash_fast": row[2], "hash_full": row[3], "alg": row[4]}
    # Lê JSON
    elif dump_path.suffix.lower() == ".json":
        with open(dump_path, "r", encoding="utf-8") as jsonfile:
            inventory = json.load(jsonfile)


    else:
        logger.warning("Extensão para o arquivo de inventário inválida. Use .csv ou .json")
        return None

    logger.info(f"Inventário recuperado. {len(inventory.keys())} registros encontrados.")
    return inventory
