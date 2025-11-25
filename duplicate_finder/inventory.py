import csv
import json
import logging
from collections import defaultdict
from pathlib import Path


class Inventory(object):
    def __init__(self, inventory_file:Path=None, pre_path:Path=None):
        self.logger=logging.getLogger("duplicate_finder")

        self.inventory_file = inventory_file
        self.pre_path = pre_path
        self.by_size = None
        self.by_hash_fast = None
        self.by_hash_full = None
        if inventory_file:
            self.inventory = self.load_file_inventory(inventory_file)
        else:
            self.inventory = dict()
        self.create_indexes()
        
    
    @staticmethod
    def load_file_inventory(inventory_path:Path, logger=logging.getLogger("duplicate_finder")):
        """ Load inventory file """
        logger.info(f"Lendo inventário gravado em {inventory_path}")
        inventory = dict()

        # Verifica se o tipo do arquivo é compatível
        if inventory_path.suffix.lower() not in ['.csv', '.json']:
            raise ValueError("O formato do arquivo não foi reconhecido, deve ser informado um arquivo CSV ou JSON")

        # Verifica se o arquivo existe
        if not inventory_path.exists():
            logger.info("Arquivo não existe, será criado um novo arquivo de inventário")
            return inventory
        
        # Carrega CSV
        if inventory_path.suffix.lower() == '.csv':
            with open(inventory_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row[0] == "path":
                        continue
                    inventory[row[0]] = {"size": row[1], "hash_fast": row[2], "hash_full": row[3], "alg": row[4]}
        # Carrega JSON
        elif inventory_path.suffix.lower() == '.json':
            with open(inventory_path, "r", encoding="utf-8") as jsonfile:
                inventory = json.load(jsonfile)
            
        
        logger.info(f"Inventário recuperado. {len(inventory.keys())} registros encontrados.")
        return inventory
        

    def record_file_inventory(self):
        self.logger.info(f"Gravando inventário em {self.inventory_file}")

        if not self.inventory_file:
            raise ValueError("Não foi informado arquivo de inventário, favor verificar")

        # Grava CSV
        if self.inventory_file.suffix.lower() == ".csv":
            with open(self.inventory_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["path", "size", "hash_fast", "hash_full", "alg"])
                for k in self.inventory.keys():
                    writer.writerow(
                        [k], # path
                        self.inventory[k]['size'], # size
                        self.inventory[k]["hash_fast"] if "hash_fast" in self.inventory[k].keys() else None, # hash_fast
                        self.inventory[k]["hash_full"] if "hash_full" in self.inventory[k].keys() else None, # hash_full
                        self.inventory[k]["alg"] if "alg" in self.inventory[k].keys() else None # alg
                        )
            self.logger.info(f"Inventário CSV salvo em {self.inventory_file}")

        # Grava JSON
        elif self.inventory_file.suffix.lower() == ".json":
            with open(self.inventory_file, "w", encoding="utf-8") as jsonfile:
                json.dump(self.inventory, jsonfile, indent=4, ensure_ascii=False)
            self.logger.info(f"Inventário JSON salvo em {self.inventory_file}")

        else:
            raise ValueError("O formato do arquivo não foi reconhecido, deve ser informado um arquivo CSV ou JSON")
    
    
    def create_indexes(self):
        self.by_size = defaultdict(list)
        self.by_hash_fast = defaultdict(list)
        self.by_hash_full = defaultdict(list)

        for k in self.inventory.keys():
            self.by_size[self.inventory[k]['size']].append(k)
            if 'hash_fast' in self.inventory[k].keys():
                self.by_hash_fast[self.inventory[k]['hash_fast']].append(k)
            if 'hash_full' in self.inventory[k].keys():
                self.by_hash_full[self.inventory[k]['hash_full']].append(k)


    def path_to_key(self, path:Path) -> str:
        if self.pre_path and path.is_relative_to(self.pre_path):
            path = path.relative_to(self.pre_path)
        return str(path)


    def add_item(self, path:Path):
        try:
            size = path.stat().st_size
            path_key = self.path_to_key(path)
            if path_key not in self.inventory.keys():
                self.inventory[path_key] = {}
                self.inventory[path_key]['size'] = size
                self.by_size[size].append(path_key)
        except FileNotFoundError:
            self.logger.warning(f"Arquivo {path} inacessível.")


    def remove_item(self, path:Path):
        path_key = self.path_to_key(path)
        if path_key in self.inventory.keys():
            self.by_size[self.inventory[path_key]['size']].remove(path_key)
            if 'hash_fast' in self.inventory[path_key].keys():
                self.by_hash_fast[self.inventory[path_key]['hash_fast']].remove(path_key)
            if 'hash_full' in self.inventory[path_key].keys():
                self.by_hash_full[self.inventory[path_key]['hash_full']].remove(path_key)
            self.inventory.pop(path_key)
        else:
            self.logger.warning(f"Arquivo {path_key} não está no inventário")
    
    
    def update_item(self, path:Path, size:int=None, hash_fast:str=None, hash_full:str=None, alg:str=None):
        path_key = self.path_to_key(path)

        if size:
            prev_size = self.inventory[path_key]['size'] if 'size' in self.inventory[path_key].keys() else None
            if prev_size and prev_size != size and path_key in self.by_size[prev_size]:
                self.by_size[prev_size].pop(path_key)
            if path_key not in self.by_size[size]:
                self.by_size[size].append(path_key)
            self.inventory[path_key]['size'] = size

        if hash_fast:
            prev_hash_fast = self.inventory[path_key]['hash_fast'] if 'hash_fast' in self.inventory[path_key].keys() else None
            if prev_hash_fast and prev_hash_fast != hash_fast and path_key in self.by_hash_fast[prev_hash_fast]:
                self.by_hash_fast[prev_hash_fast].pop(path_key)
            if path_key not in self.by_hash_fast[hash_fast]:
                self.by_hash_fast[hash_fast].append(path_key)
            self.inventory[path_key]['hash_fast'] = hash_fast

        if hash_full:
            prev_hash_full = self.inventory[path_key]['hash_full'] if 'hash_full' in self.inventory[path_key].keys() else None
            if prev_hash_full and prev_hash_full != hash_full and path_key in self.by_hash_full[prev_hash_full]:
                self.by_hash_full[prev_hash_full].pop(path_key)
            if path_key not in self.by_hash_full[hash_full]:
                self.by_hash_full[hash_full].append(path_key)
            self.inventory[path_key]['hash_full'] = hash_full

        if alg:
            self.inventory[path_key]['alg'] = alg

    
    def has_item(self, path):
        path_key = self.path_to_key(path)
        return path_key in self.inventory.keys()


    def get_by_size_list(self):
        return self.by_size.items()
    

    def get_by_hash_fast_list(self):
        return self.by_hash_fast.items()
    

    def get_by_hash_full_list(self):
        return self.by_hash_full.items()


    def __str__(self):
        return json.dumps(self.inventory, indent=4, ensure_ascii=False)