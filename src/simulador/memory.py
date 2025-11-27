# src/simulador/memory.py

WORD_SIZE = 4 # 4 bytes por palavra

def read_mem(memory_list: list, address: int) -> int:
    """Lê uma palavra de 4 bytes da memória de dados (por índice de palavra)."""
    index = address // WORD_SIZE
    if index < len(memory_list):
        return memory_list[index]
    return 0

def write_mem(memory_list: list, address: int, data: int):
    """Escreve uma palavra de 4 bytes na memória de dados (por índice de palavra)."""
    index = address // WORD_SIZE
    if index < len(memory_list):
        memory_list[index] = data

def print_memory_data(memory_list: list):
    """Imprime o estado dos primeiros endereços da memória de dados."""
    print("--- Memória de Dados (Primeiras Palavras, Decimal) ---")
    for i in range(16):
        address = i * WORD_SIZE
        value = memory_list[i] if i < len(memory_list) else 0
        print(f"Endereço {address:<4}: {value}")