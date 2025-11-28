# src/interpretador/assembler.py

import os
import sys
from src.simulador.instruction import OPCODE_MAP

DEFAULT_ASSEMBLY_CONTENT = """
# Teste salto
ADDI R1, R0, 7
ADDI R2, R0, 3
MUL R3, R1, R2
SW R3, 4(R0)
LW R4, 4(R0)
XOR R5, R4, R2
ANDI R6, R5, 1
SLTI R7, R6, 1
HALT
"""

def reg_to_bin(reg_str: str) -> str:
    try:
        idx = int(reg_str[1:])
        if idx < 0 or idx > 15:
            raise ValueError()
        return format(idx, '04b')
    except Exception:
        raise ValueError(f"Registrador inválido: {reg_str}")

def imm_to_bin(value: int, num_bits: int) -> str:
    val = int(value)
    if val < 0:
        val = (1 << num_bits) + val
    return format(val & ((1 << num_bits) - 1), f'0{num_bits}b')

def assemble_line(assembly_line: str) -> str:
    line = assembly_line.strip()
    if not line or line.startswith('#'):
        return ""
    parts = line.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
    if not parts:
        return ""
    mnemonic = parts[0].upper()

    # find opcode binary from OPCODE_MAP by name
    op_bin = next((op for op, info in OPCODE_MAP.items() if info['name'] == mnemonic), None)
    if not op_bin:
        raise ValueError(f"Mnemônico desconhecido: {mnemonic}")

    op_info = OPCODE_MAP[op_bin]
    t = op_info['type']

    if op_info['name'] == 'HALT':
        return '11111111' + '0' * 24
    if op_info['name'] == 'NOP':
        return '0' * 32

    # R-type
    if t == 'R':
        # expect: MN Rdest, Rsrc1, Rsrc2   (JR: uses Rs as target)
        if len(parts) == 2 and mnemonic == 'JR':
            # JR Rsrc
            Rd_bin = '0000'
            Rs_bin = reg_to_bin(parts[1])
            Rt_bin_4 = '0000'
        else:
            if len(parts) < 3:
                raise ValueError(f"Faltam operandos para {mnemonic}")
            Rd_bin = reg_to_bin(parts[1])
            Rs_bin = reg_to_bin(parts[2])
            Rt_bin_4 = reg_to_bin(parts[3]) if len(parts) >= 4 else '0000'
        F3 = Rt_bin_4 + '0' * 12
        return op_bin + Rd_bin + Rs_bin + F3

    # I_ARITH or I_BRANCH or I_MEM or I_CONST
    if t in ['I_ARITH', 'I_MEM', 'I_BRANCH', 'I_CONST']:
        # I_ARITH: MN Rt, Rs, imm
        if op_info['type'] == 'I_ARITH':
            if len(parts) != 4:
                raise ValueError(f"Formato inválido para {mnemonic}. Ex: {mnemonic} Rdest, Rsrc, imm")
            Rt_bin = reg_to_bin(parts[1])
            Rs_bin = reg_to_bin(parts[2])
            Imm_bin = imm_to_bin(int(parts[3]), 16)
            return op_bin + Rt_bin + Rs_bin + Imm_bin

        # I_MEM: LW Rt, offset(Rs) -> parsed by split earlier into parts:[LW,Rt,offset,Rs]
        if op_info['type'] == 'I_MEM':
            if len(parts) != 4:
                raise ValueError(f"Formato inválido para {mnemonic}. Ex: {mnemonic} Rt, offset(Rs)")
            Rt_bin = reg_to_bin(parts[1])
            offset = int(parts[2])
            Rs_bin = reg_to_bin(parts[3])
            Imm_bin = imm_to_bin(offset, 16)
            return op_bin + Rt_bin + Rs_bin + Imm_bin

        # I_BRANCH: JEQ/JNE/J/JAL => we'll use: MN Rt, Rs, targetAddress
        if op_info['type'] == 'I_BRANCH':
            # JEQ Rt, Rs, target
            if mnemonic in ['JEQ', 'JNE']:
                if len(parts) != 4:
                    raise ValueError(f"Formato inválido para {mnemonic}. Ex: {mnemonic} Rs, Rt, target")
                # parts: [JEQ, Rs, Rt, target]
                Rt_bin = reg_to_bin(parts[2])
                Rs_bin = reg_to_bin(parts[1])
                Imm_bin = imm_to_bin(int(parts[3]), 16)
                return op_bin + Rt_bin + Rs_bin + Imm_bin
            elif mnemonic in ['J', 'JAL']:
                # J target  -> we place target in Imm (Rt/Rs ignored)
                if len(parts) != 2:
                    raise ValueError(f"Formato inválido para {mnemonic}. Ex: {mnemonic} target")
                Rt_bin = '0000'
                Rs_bin = '0000'
                Imm_bin = imm_to_bin(int(parts[1]), 16)
                return op_bin + Rt_bin + Rs_bin + Imm_bin

        # I_CONST (LUI/LLI) handled simply as Rt + Imm 16 bits splitted
        if op_info['type'] == 'I_CONST':
            if len(parts) != 3:
                raise ValueError(f"Formato inválido para {mnemonic}. Ex: {mnemonic} Rt, imm")
            Rt_bin = reg_to_bin(parts[1])
            imm_val = int(parts[2])
            imm_16 = format(imm_val & 0xFFFF, '016b')
            imm_h = imm_16[:8]
            imm_l = imm_16[8:]
            # imm_l padded to 8 -> F3 uses 12 bits in decode, but we'll append 4 zeros as legacy
            imm_l_12 = imm_l + '0' * 4
            return op_bin + Rt_bin + imm_h + imm_l_12

    raise ValueError(f"Formato não tratado para {mnemonic}")
    

def assemble_file(input_file: str, output_file_txt: str, output_file_bin: str):
    os.makedirs(os.path.dirname(output_file_txt), exist_ok=True)
    lines_written = 0
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file_txt, 'w', encoding='utf-8') as outfile_txt, \
             open(output_file_bin, 'wb') as outfile_bin:

            outfile_txt.write("address 0000000000000000\n")
            for line in infile:
                try:
                    binary_instruction = assemble_line(line)
                    if binary_instruction and len(binary_instruction) == 32:
                        outfile_txt.write(binary_instruction + '\n')
                        raw_bytes = bytes([
                            int(binary_instruction[0:8], 2),
                            int(binary_instruction[8:16], 2),
                            int(binary_instruction[16:24], 2),
                            int(binary_instruction[24:32], 2)
                        ])
                        outfile_bin.write(raw_bytes)
                        lines_written += 1
                except Exception as e:
                    print(f"[ASSEMBLER] ERRO na linha '{line.strip()}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"[ASSEMBLER] ERRO FATAL de I/O: {e}", file=sys.stderr)
        return False

    if lines_written == 0:
        print("[ASSEMBLER] Aviso: Nenhuma instrução válida foi gerada.")
        return False

    print(f"[ASSEMBLER] Sucesso: {lines_written} instruções geradas.")
    return True


def check_and_generate_bin(asm_path: str, bin_path: str, txt_path: str):
    os.makedirs(os.path.dirname(asm_path), exist_ok=True)
    if not os.path.exists(asm_path) or os.stat(asm_path).st_size == 0:
        with open(asm_path, 'w') as f:
            f.write(DEFAULT_ASSEMBLY_CONTENT.strip())
    should_assemble = not os.path.exists(bin_path)
    if os.path.exists(bin_path) and os.path.getmtime(asm_path) > os.path.getmtime(bin_path):
        should_assemble = True
    if should_assemble:
        print("\n--- 📝 FASE DE MONTAGEM AUTOMÁTICA ---")
        return assemble_file(asm_path, txt_path, bin_path)
    return False
