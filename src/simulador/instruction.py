# src/simulador/instruction.py

# ====================================================================
# Funções auxiliares
# ====================================================================

def bin_to_int(binary_str: str) -> int:
    """Converte string binária para inteiro, tratando sinal (2's complement)."""
    if not binary_str:
        return 0
    # Garante 32 bits
    if len(binary_str) < 32:
        # estende pelo bit de sinal
        sign = binary_str[0]
        binary_str = sign * (32 - len(binary_str)) + binary_str

    if binary_str[0] == '1':
        # complemento de dois
        inverted = ''.join('1' if b == '0' else '0' for b in binary_str)
        return -(int(inverted, 2) + 1)
    else:
        return int(binary_str, 2)


def reg_to_bin(reg_str: str) -> str:
    """Converte 'R<num>' para 4 bits (0..15)."""
    try:
        reg_num = int(reg_str[1:])
        if not (0 <= reg_num <= 15):
            raise ValueError
        return format(reg_num, '04b')
    except Exception:
        raise ValueError(f"Formato de registrador inválido: {reg_str}")


# ====================================================================
# MAPA DE OPCODES E DECODIFICAÇÃO
# ====================================================================
OPCODE_MAP = {
    # R-Type (existentes)
    '00000001': {'name': 'ADD', 'type': 'R'},
    '00000010': {'name': 'SUB', 'type': 'R'},
    '00000011': {'name': 'ZERO', 'type': 'R'},
    '00000100': {'name': 'XOR', 'type': 'R'},
    '00000101': {'name': 'OR', 'type': 'R'},
    '00000110': {'name': 'NOT', 'type': 'R'},
    '00000111': {'name': 'AND', 'type': 'R'},
    '00001000': {'name': 'SLA', 'type': 'R'},
    '00001001': {'name': 'SRA', 'type': 'R'},
    '00001010': {'name': 'SLL', 'type': 'R'},
    '00001011': {'name': 'SRL', 'type': 'R'},
    '00001100': {'name': 'COPY', 'type': 'R'},
    # JR
    '00001101': {'name': 'JR', 'type': 'R'},

    # R-type extras
    '00010100': {'name': 'MUL', 'type': 'R'},
    '00010101': {'name': 'DIV', 'type': 'R'},
    '00011011': {'name': 'NOR', 'type': 'R'},

    # I-ARITH
    '00011000': {'name': 'ADDI', 'type': 'I_ARITH'},
    '00011001': {'name': 'SUBI', 'type': 'I_ARITH'},
    '00010110': {'name': 'MULI', 'type': 'I_ARITH'},
    '00010111': {'name': 'ANDI', 'type': 'I_ARITH'},
    '00011100': {'name': 'SLTI', 'type': 'I_ARITH'},

    # Logical R-types (duplicated codes handled already)
    '00000101': {'name': 'OR', 'type': 'R'},
    '00000111': {'name': 'AND', 'type': 'R'},

    # I-CONST / I-MEM
    '00001110': {'name': 'LUI', 'type': 'I_CONST'},
    '00011010': {'name': 'LLI', 'type': 'I_CONST'},
    '00010000': {'name': 'LW', 'type': 'I_MEM'},
    '00010001': {'name': 'SW', 'type': 'I_MEM'},

    # CONTROLE (novas instruções de salto/branch)
    # JEQ: jump if equal (I-style: Rt, Rs, Imm)  -- we'll store Immediate as UNSIGNED 16-bit (absolute byte addr)
    '00011101': {'name': 'JEQ', 'type': 'I_BRANCH'},
    # JNE: jump if not equal
    '00011110': {'name': 'JNE', 'type': 'I_BRANCH'},
    # J: jump absolute (imm target)
    '00011111': {'name': 'J', 'type': 'I_BRANCH'},
    # JAL: jump and link (salva o PC_word+1 em R15)
    '00100000': {'name': 'JAL', 'type': 'I_BRANCH'},

    # HALT / NOP
    '11111111': {'name': 'HALT', 'type': 'HALT'},
    '00000000': {'name': 'NOP', 'type': 'NOP'}
}


def decode_instruction(instruction_binary: str) -> dict:
    """Decodifica instrução de 32 bits e retorna campos."""
    if not instruction_binary or len(instruction_binary) < 8:
        raise ValueError("Instrução inválida/curta.")

    opcode = instruction_binary[0:8]
    op_info = OPCODE_MAP.get(opcode)
    if not op_info:
        raise ValueError(f"Opcode não reconhecido: {opcode}")

    decoded = {'Opcode': opcode, 'Mnemonic': op_info['name'], 'Type': op_info['type']}

    # Campos comuns: F1(8:12), F2(12:16), F3(16:32)
    if op_info['type'] in ['R', 'I_ARITH', 'I_MEM', 'I_BRANCH']:
        F1 = instruction_binary[8:12]   # Rd (R) ou Rt (I)
        F2 = instruction_binary[12:16]  # Rs
        F3 = instruction_binary[16:32]  # Rt (R) ou Imm (I)

        decoded['Rs'] = int(F2, 2)

        if op_info['type'] == 'R':
            # R: OP | Rd(4) | Rs(4) | Rt(4) + fill(12)
            decoded['Rd'] = int(F1, 2)
            decoded['Rt'] = int(F3[0:4], 2)
        else:
            # I_ARITH, I_MEM: immediate é signed (ex.: offsets)
            if op_info['type'] in ['I_ARITH', 'I_MEM']:
                decoded['Rt'] = int(F1, 2)
                # Imediato de 16 bits com sinal
                decoded['Immediate'] = bin_to_int(F3)
            else:
                # I_BRANCH: Immediate é endereço absoluto de 16 bits (UNSIGNED)
                decoded['Rt'] = int(F1, 2)
                decoded['Immediate'] = int(F3, 2)

    elif op_info['type'] == 'I_CONST':
        # OP | Rt(4) | Imm_H(8) | Imm_L(8)
        F1 = instruction_binary[8:12]  # Rt
        F2 = instruction_binary[12:20]  # Imm_H (8)
        F3 = instruction_binary[20:28]  # Imm_L (8)
        decoded['Rt'] = int(F1, 2)
        imm_16 = F2 + F3  # 16 bits
        decoded['Immediate'] = int(imm_16, 2)

    return decoded
