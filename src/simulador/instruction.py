# instruction.py

# Mapeamento dos Opcodes de 8 bits
OPCODE_MAP = {
    # 1. Instruções ALU (Tipo R: Rd, Rs, Rt)
    '00000001': {'name': 'ADD', 'type': 'R'}, # Adição de inteiros
    '00000010': {'name': 'SUB', 'type': 'R'}, # Subtração de inteiros
    '00000011': {'name': 'ZERO', 'type': 'R'}, # Zero
    '00000100': {'name': 'XOR', 'type': 'R'}, # Xor
    '00000101': {'name': 'OR', 'type': 'R'},  # Or
    '00000110': {'name': 'NOT', 'type': 'R'}, # Not
    '00000111': {'name': 'AND', 'type': 'R'}, # And
    '00001000': {'name': 'SLA', 'type': 'R'}, # Shift aritimético p/ esquerda
    '00001001': {'name': 'SRA', 'type': 'R'}, # Shift aritimético p/ direita
    '00001010': {'name': 'SLL', 'type': 'R'}, # Shift lógico à esquerda
    '00001011': {'name': 'SRL', 'type': 'R'}, # Shift lógico à direita
    '00001100': {'name': 'COPY', 'type': 'R'},# Cópia
    
    # 2. Instruções de Constante (Tipo I_CONST: Rt, Imediato 16 bits)
    '00001110': {'name': 'LUI', 'type': 'I_CONST'}, # Carrega constante 16 bits nos 2 bytes MAIS sig.
    '00001111': {'name': 'LLI', 'type': 'I_CONST'}, # Carrega constante 16 bits nos 2 bytes MENOS sig.
    
    # 3. Instruções de Memória (Tipo I_MEM: Rt, Offset(Rs))
    '00010000': {'name': 'LW', 'type': 'I_MEM'},    # Load Word
    '00010001': {'name': 'SW', 'type': 'I_MEM'},    # Store Word
    
    # 4. Controle
    '00000000': {'name': 'NOP', 'type': 'NOP'},   # NOP
    '11111111': {'name': 'HALT', 'type': 'HALT'}  # Parada
}

def _bin_to_reg_index(bin_str: str) -> int:
    """Converte string binária de 8 bits para índice de registrador (0-31)."""
    # Usa apenas os 5 bits inferiores para endereçar R0-R31
    return int(bin_str[-5:], 2)

def _bin_to_imm(bin_str: str) -> int:
    """Converte string binária (8 bits, complemento de dois) em valor inteiro decimal."""
    if bin_str[0] == '1':
        return int(bin_str, 2) - (1 << 8)
    else:
        return int(bin_str, 2)

def decode_instruction(binary_string: str) -> dict:
    """
    Decodifica a string binária de 32 bits e retorna um dicionário com os campos.
    """
    binary_string = binary_string.strip()
    if len(binary_string) != 32:
        raise ValueError("A string binária deve ter exatamente 32 bits.")

    # 1. Extrai campos brutos
    opcode_bin = binary_string[0:8]
    field_rt_bin = binary_string[8:16]
    field_rs_bin = binary_string[16:24]
    field_extra_bin = binary_string[24:32]

    # 2. Obtém informações do Opcode
    op_info = OPCODE_MAP.get(opcode_bin, {'name': 'UNKNOWN', 'type': 'UNKNOWN'})
    inst_type = op_info['type']
    
    result = {
        'opcode_bin': opcode_bin,
        'mnemonic': op_info['name'],
        'type': inst_type,
        'Rd': None, 'Rs': None, 'Rt': None, 'Immediate': None
    }
    
    # 3. Decodifica campos baseada no Tipo
    # Rt e Rs são lidos em ID/EX. A função aqui retorna apenas os ÍNDICES decimais.
    
    if inst_type == 'R':
        # Formato R: [Opcode (8), Rd (8), Rs (8), Rt (8)]
        # O campo 8:16 é o destino (Rd), 16:24 é a fonte 1 (Rs), 24:32 é a fonte 2 (Rt)
        result['Rd'] = _bin_to_reg_index(field_rt_bin)
        result['Rs'] = _bin_to_reg_index(field_rs_bin)
        result['Rt'] = _bin_to_reg_index(field_extra_bin)
        
    elif inst_type == 'I_MEM':
        # Formato I (Memória): [Opcode (8), Rt (8), Rs (8), Offset (8)]
        # O campo 8:16 é o destino/fonte (Rt), 16:24 é o registrador base (Rs), 24:32 é o Offset
        result['Rt'] = _bin_to_reg_index(field_rt_bin) # Registrador a ser carregado/armazenado
        result['Rs'] = _bin_to_reg_index(field_rs_bin) # Registrador base do endereço
        result['Immediate'] = _bin_to_imm(field_extra_bin) # Offset (Imediato de 8 bits)
        
    elif inst_type == 'I_CONST':
        # Formato I (Constante): [Opcode (8), Rt (8), Imediato (16 bits em Rs+Offset)]
        result['Rt'] = _bin_to_reg_index(field_rt_bin) # Registrador destino (Rd)
        
        # Concatena os 16 bits do imediato.
        immediate_16_bin = field_rs_bin + field_extra_bin
        # Para LUI/LLI, o valor de 16 bits é tratado como unsigned (sem sinal).
        result['Immediate'] = int(immediate_16_bin, 2)
        
    elif inst_type == 'HALT':
        # Não há campos relevantes, mas podemos preencher com NOPs para consistência
        pass
        
    return result