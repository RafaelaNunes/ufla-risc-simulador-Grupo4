# src/simulador/loader.py

import os
from typing import List
from src.simulador.memory import MEMORY_SIZE_WORDS


class LoaderError(Exception):
    pass

def binstr_to_word(binstr: str) -> int:
    """
    Converte uma string de 32 bits '0101...' para um inteiro.
    Valida comprimento e caracteres.
    """
    s = binstr.strip()
    if len(s) != 32:
        raise ValueError(f"Instrucao invalida: esperado 32 bits, encontrado {len(s)} bits -> '{s}'")
    if any(c not in "01" for c in s):
        raise ValueError(f"Instrucao invalida: caracteres diferentes de 0/1 -> '{s}'")
    return int(s, 2)

def parse_address_directive(line: str) -> int:
    """
    Recebe uma linha do tipo: 'address 0000000000010101'
    Retorna o endereco em decimal (int).
    Valida que o endereco tem no maximo 16 bits (0..65535).
    """
    parts = line.strip().split()
    if len(parts) != 2 or parts[0].lower() != "address":
        raise ValueError(f"Diretiva 'address' mal formada: '{line.strip()}'")
    addr_bin = parts[1].strip()
    if any(c not in "01" for c in addr_bin):
        raise ValueError(f"Endereco 'address' contem caracteres invalidos: '{addr_bin}'")
    if len(addr_bin) > 16:
        raise ValueError(f"Endereco 'address' maior que 16 bits: {len(addr_bin)} bits")
    addr = int(addr_bin, 2)
    if not (0 <= addr < MEMORY_SIZE_WORDS):
        raise ValueError(f"Endereco 'address' fora dos limites (0..{MEMORY_SIZE_WORDS-1}): {addr}")
    return addr

def load_binary_file(filepath: str, memory: List[int], default_start: int = 0) -> int:
    """
    Carrega um arquivo de instrucoes binario (texto) na memoria.
    - filepath: caminho para o arquivo de texto
    - memory: lista retornada por create_memory() (tamanho MEMORY_SIZE_WORDS)
    - default_start: endereco inicial (se nao houver 'address')
    Retorna: proximo endereco livre (int)
    Lanca LoaderError em caso de erros irrecuperaveis.
    """
    if not os.path.exists(filepath):
        raise LoaderError(f"Arquivo nao encontrado: {filepath}")

    address = default_start
    line_no = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line_no += 1
            line = raw_line.strip()
            if line == "" or line.startswith("#"):  # permite comentarios com #
                continue

            # Diretiva address
            if line.lower().startswith("address"):
                try:
                    address = parse_address_directive(line)
                except Exception as e:
                    raise LoaderError(f"Erro na linha {line_no}: {e}")
                continue

            # Espera-se uma instrucao binaria de 32 bits
            try:
                word = binstr_to_word(line)
            except ValueError as e:
                raise LoaderError(f"Erro na linha {line_no}: {e}")

            if not (0 <= address < MEMORY_SIZE_WORDS):
                raise LoaderError(f"Endereco {address} fora da memoria ao tentar escrever (linha {line_no})")

            memory[address] = word
            address += 1

    return address

def dump_loaded_memory(memory: List[int], start: int = 0, end: int = 64):
    """
    Imprime as primeiras (ou intervalo) posicoes da memoria que sejam diferentes de zero.
    Para debug.
    """
    print("Dump de memoria (apenas posicoes nao-nulas no intervalo):")
    for addr in range(start, min(end, len(memory))):
        val = memory[addr]
        if val != 0:
            binstr = format(val, '032b')
            print(f"  [{addr:5}] {binstr}  (0x{val:08X})")
