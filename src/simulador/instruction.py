# src/simulador/instruction.py

def bin_to_int(binary_str: str) -> int:
    """Converte string binária para inteiro, tratando sinal (2's complement)."""
    if not binary_str: return 0
    if len(binary_str) < 32:
        sign = binary_str[0]
        binary_str = sign * (32 - len(binary_str)) + binary_str
    if binary_str[0] == '1':
        inverted = ''.join('1' if b == '0' else '0' for b in binary_str)
        return -(int(inverted, 2) + 1)
    else:
        return int(binary_str, 2)

# Mapeamento estendido com suas instruções novas
OPCODE_MAP = {
    # R-Type (Padrão UFLA)
    '00000001': {'name': 'ADD', 'type': 'R'},
    '00000010': {'name': 'SUB', 'type': 'R'},
    '00000011': {'name': 'ZERO', 'type': 'R_SPECIAL'}, # ZERO Rc
    '00000100': {'name': 'XOR', 'type': 'R'},
    '00000101': {'name': 'OR', 'type': 'R'},
    '00000110': {'name': 'NOT', 'type': 'R_NOT'},      # NOT Rc, Ra
    '00000111': {'name': 'AND', 'type': 'R'},
    '00001000': {'name': 'SLA', 'type': 'R'},
    '00001001': {'name': 'SRA', 'type': 'R'},
    '00001010': {'name': 'SLL', 'type': 'R'},
    '00001011': {'name': 'SRL', 'type': 'R'},
    '00001100': {'name': 'COPY', 'type': 'R_COPY'},    # COPY Rc, Ra
    
    # NOVAS R-Type
    '00010100': {'name': 'MUL', 'type': 'R'},
    '00010101': {'name': 'DIV', 'type': 'R'},
    '00011011': {'name': 'NOR', 'type': 'R'},
    
    # I-CONST / I-MEM (Padrão UFLA)
    '00001110': {'name': 'LUI', 'type': 'LCL'},  # Carrega Constante Alta
    '00001111': {'name': 'LLI', 'type': 'LCL'},  # Carrega Constante Baixa
    '00010000': {'name': 'LW', 'type': 'MEM'},   # LOAD Rc, Ra
    '00010001': {'name': 'SW', 'type': 'MEM_S'}, # STORE Rc, Ra (Mem[Rc] = Ra)

    # JUMPS (Padrão UFLA)
    '00010010': {'name': 'JAL', 'type': 'J_LINK'}, # JAL Endereço
    '00010011': {'name': 'JR', 'type': 'J_REG'},   # JR Rc
    '00010100': {'name': 'BEQ', 'type': 'BRANCH'}, # BEQ Ra, Rb, End
    '00010101': {'name': 'BNE', 'type': 'BRANCH'}, # BNE Ra, Rb, End
    '00010110': {'name': 'J', 'type': 'JUMP'},     # J Endereço

    # NOVAS IMEDIATAS (Adaptação Livre - Usaremos formato I-Type MIPS-like adaptado)
    # Sugestão: Opcode(8) | Rt(8) | Rs(8) | Imm(8) -> Imm muito curto.
    # Vamos usar: Opcode(8) | Rt(4)|Rs(4) | Imm(16) para as SUAS instruções novas apenas.
    '00011000': {'name': 'ADDI', 'type': 'I_CUSTOM'},
    '00011001': {'name': 'SUBI', 'type': 'I_CUSTOM'},
    '00010110': {'name': 'MULI', 'type': 'I_CUSTOM'},
    '00010111': {'name': 'ANDI', 'type': 'I_CUSTOM'},
    '00011100': {'name': 'SLTI', 'type': 'I_CUSTOM'},

    '11111111': {'name': 'HALT', 'type': 'HALT'},
    '00000000': {'name': 'NOP', 'type': 'NOP'}
}

def decode_instruction(instruction_binary: str) -> dict:
    if not instruction_binary or len(instruction_binary) < 32:
        return {'Mnemonic': 'NOP', 'Opcode': '00000000'}

    opcode = instruction_binary[0:8]
    op_info = OPCODE_MAP.get(opcode, {'name': 'UNKNOWN', 'type': 'UNKNOWN'})
    t = op_info['type']
    
    decoded = {
        'Opcode': opcode,
        'Mnemonic': op_info['name'],
        'Rs': 0, 'Rt': 0, 'Rd': 0, 'Immediate': 0
    }

    # Decodificação baseada nos Apêndices B (Campos de 8 bits)
    # Padrão R: Opcode(31-24) | Ra(23-16) | Rb(15-8) | Rc(7-0)
    ra = int(instruction_binary[8:16], 2)
    rb = int(instruction_binary[16:24], 2)
    rc = int(instruction_binary[24:32], 2)

    if t == 'R': # ADD, SUB, AND... (Rc = Ra op Rb)
        decoded['Rs'] = ra # Fonte 1
        decoded['Rt'] = rb # Fonte 2
        decoded['Rd'] = rc # Destino
        
    elif t == 'R_NOT' or t == 'R_COPY': # NOT Rc, Ra / COPY Rc, Ra
        decoded['Rs'] = ra
        decoded['Rd'] = rc
        
    elif t == 'R_SPECIAL': # ZERO Rc
        decoded['Rd'] = rc

    elif t == 'LCL': # LCL Rc, Const16
        # Opcode(8) | Const16(23-8) | Rc(7-0)
        # Nota: O PDF diz Const16 nos bits 23-8. Isso significa bits do meio.
        const16 = int(instruction_binary[8:24], 2)
        decoded['Rd'] = rc
        decoded['Immediate'] = const16

    elif t == 'MEM': # LOAD Rc, Ra (Rc = Mem[Ra])
        decoded['Rs'] = ra # Endereço base
        decoded['Rd'] = rc # Destino

    elif t == 'MEM_S': # STORE Rc, Ra (Mem[Rc] = Ra) -> Cuidado: PDF diz Store Rc, Ra => Mem[Rc] = Ra
        decoded['Rs'] = rc # Endereço (Rc é usado como base)
        decoded['Rt'] = ra # Dado a salvar (Ra)
    
    elif t == 'BRANCH': # BEQ Ra, Rb, End
        # PDF: Opcode | Ra | Rb | End(8 bits)
        decoded['Rs'] = ra
        decoded['Rt'] = rb
        decoded['Immediate'] = rc # Endereço curto (8 bits)

    elif t == 'J_LINK': # JAL Endereço (24 bits)
        # PDF: Opcode | Endereço (23-0)
        addr = int(instruction_binary[8:32], 2)
        decoded['Immediate'] = addr

    elif t == 'J_REG': # JR Rc
        # PDF: Opcode | ... | Rc
        decoded['Rs'] = rc # Rc contém o endereço alvo

    elif t == 'JUMP': # J Endereço
        addr = int(instruction_binary[8:32], 2)
        decoded['Immediate'] = addr

    elif t == 'I_CUSTOM': # Suas instruções extras (ADDI...)
        # Usaremos formato híbrido para caber imediato de 16 bits
        # Opcode(8) | Rt(4) Rs(4) | Imm(16)
        rt_custom = int(instruction_binary[8:12], 2)
        rs_custom = int(instruction_binary[12:16], 2)
        imm_custom = bin_to_int(instruction_binary[16:32])
        decoded['Rt'] = rt_custom # Destino
        decoded['Rs'] = rs_custom # Fonte
        decoded['Immediate'] = imm_custom

    return decoded