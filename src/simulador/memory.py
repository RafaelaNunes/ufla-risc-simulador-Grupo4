# memory.py

MEMORY_SIZE_WORDS = 65536  # 2^16 posições de palavra (palavra = 4 bytes)

def create_memory():
    """Cria a memória do processador como uma lista de inteiros (palavras de 32 bits)."""
    return [0] * MEMORY_SIZE_WORDS

def read_mem(memory: list, address: int) -> int:

    if address % 4 != 0:
        raise ValueError(f"Endereço de memória não alinhado: {address}")

    word_index = address // 4
    if 0 <= word_index < MEMORY_SIZE_WORDS:
        return memory[word_index]
    raise IndexError(f"Endereço de memória fora do limite: {address}")

def write_mem(memory: list, address: int, value: int):

    if address % 4 != 0:
        raise ValueError(f"Endereço de memória não alinhado: {address}")
        
    word_index = address // 4
    if 0 <= word_index < MEMORY_SIZE_WORDS:
        memory[word_index] = value & 0xFFFFFFFF
    else:
        raise IndexError(f"Endereço de memória fora do limite para escrita: {address}")

def load_instruction_mem(memory: dict, address: int, binary_string: str):
    memory[address] = binary_string

def print_memory_data(memory: list):
    
    print("--- Memória de Dados (Primeiras Palavras, Decimal) ---")
    
    for i in range(0, 16): 
        address = i * 4
        value = memory[i]
        print(f"Endereço {address:<4}: {value}")