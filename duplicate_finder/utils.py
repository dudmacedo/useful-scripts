import csv
import hashlib
import json
import logging
import os
from collections import defaultdict
from inventory import Inventory
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


def scan_files(path:Path, exclude_ext=None):
    """
    Varre diretório e retorna lista de arquivos

    Args:
        path (str): Caminho do diretório
        exclude_ext=None ([]): Lista de extensões dos tipos de arquivo a ignorar

    Returns:
        []: Lista de arquivos encontrados
    """
    files = []

    for p in path.rglob("*"):
        if p.is_file():
            if exclude_ext and p.suffix.lower() in exclude_ext:
                continue
            files.append(p)

    return files


def find_duplicates(files, output_dir:Path, alg="md5", inventory:Inventory=None):
    logger.info("Iniciando busca por arquivos duplicados..")

    for f in files:
        if inventory:
            inventory.add_item(f)
    
    iterable = inventory.get_by_size_list()
    if USE_TQDM:
        iterable = tqdm(iterable, desc="Hash parcial (4096 bytes)")
        for size, flist in iterable:
            if len(flist) < 2:
                continue
            for f in flist:
                path = output_dir / Path(f)
                try:
                    h = compute_hash(path, alg=alg, fast=True)
                    inventory.update_item(path, hash_fast=h, alg=alg)
                except FileNotFoundError:
                    logger.warning(f"Arquivo inacessível: {f}")

    iterable = inventory.get_by_hash_fast_list()
    if USE_TQDM:
        iterable = tqdm(iterable, desc="Hash completo")
        for size, flist in iterable:
            if len(flist) < 2:
                continue
            for f in flist:
                path = output_dir / Path(f)
                try:
                    h= compute_hash(path, alg=alg, fast=False)
                    inventory.update_item(path, hash_full=h, alg=alg)
                except FileNotFoundError:
                    logger.warning(f"Arquivo inacessível: {f}")

    return {h: flist for h, flist in inventory.get_by_hash_full_list() if len(flist) > 1}


def delete_duplicates(duplicates, output_dir:Path, inventory:Inventory):
    for k in duplicates.keys():
        logger.info(f"Hash '{k}':")
        logger.info(f"[MANTER] {duplicates[k][0]}")
        for f in duplicates[k][1:]:
            try:
                os.remove(output_dir / Path(f))
                inventory.remove_item(Path(f))
                logger.info(f"[DEL] {f}")
            except Exception as e:
                logger.error(f"Falha ao deletar {f} - {e}")
