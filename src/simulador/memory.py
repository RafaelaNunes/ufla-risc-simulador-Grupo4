

MEMORY_SIZE_WORDS = 65536  # 2^16 posições (memória endereçada por palavra)

def create_memory():
    """
    Cria a memória do processador como uma lista de inteiros (palavras de 32 bits).
    Inicialmente todas as posições valem 0.
    Retorna: lista com MEMORY_SIZE_WORDS elementos.
    """
    return [0] * MEMORY_SIZE_WORDS
