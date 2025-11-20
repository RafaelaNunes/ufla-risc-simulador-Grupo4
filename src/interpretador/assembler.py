# -----------------------------------------------
#  Assembler para UFLA-RISC — versão corrigida
#  COMPATÍVEL COM A CPU QUE VOCÊ IMPLEMENTOU
# -----------------------------------------------

import sys

# Estrutura das instruções
INSTR_R = {"add":0, "sub":1, "and":2, "or":3, "xor":4,
           "lsl":5, "lsr":6, "asr":7, "asl":8}

INSTR_I = {"addi":9, "subi":10, "andi":11, "ori":12,
           "xori":13}

INSTR_MEM = {"lw":14, "sw":15}

INSTR_BRANCH = {"beq":16, "bne":17}

INSTR_JUMP = {"j":18, "jal":19, "jr":20}

INSTR_LCL = {"lclh":21, "lcll":22}

HALT_OPCODE = 255


def reg_number(r):
    if not r.startswith("r"):
        raise ValueError(f"Registrador inválido: {r}")
    return int(r[1:])


def assemble_R(op, ra, rb, rc):
    opcode = INSTR_R[op]
    ra = reg_number(ra)
    rb = reg_number(rb)
    rc = reg_number(rc)
    return (opcode << 24) | (ra << 19) | (rb << 14) | (rc << 9)


def assemble_I(op, ra, rb, imm):
    opcode = INSTR_I[op]
    ra = reg_number(ra)
    rb = reg_number(rb)
    imm = int(imm) & 0x1FF  # 9 bits
    return (opcode << 24) | (ra << 19) | (rb << 14) | imm


def assemble_MEM(op, ra, rb, offset):
    opcode = INSTR_MEM[op]
    ra = reg_number(ra)
    rb = reg_number(rb)
    offset = int(offset) & 0x3FFF  # 14 bits
    return (opcode << 24) | (ra << 19) | (rb << 14) | offset


def assemble_BRANCH(op, ra, rb, offset):
    opcode = INSTR_BRANCH[op]
    ra = reg_number(ra)
    rb = reg_number(rb)
    offset = int(offset) & 0x3FFF
    return (opcode << 24) | (ra << 19) | (rb << 14) | offset


def assemble_J(op, offset):
    opcode = INSTR_JUMP[op]
    offset = int(offset) & 0xFFFFFF
    return (opcode << 24) | offset


def assemble_JR(op, ra):
    opcode = INSTR_JUMP[op]
    ra = reg_number(ra)
    return (opcode << 24) | (ra << 19)


def assemble_LCLH_LCLL(op, ra, imm):
    opcode = INSTR_LCL[op]
    ra = reg_number(ra)
    imm = int(imm) & 0x7FFFF
    return (opcode << 24) | (ra << 19) | imm


def assemble_line(line):
    parts = line.replace(",", " ").split()
    if not parts:
        return None

    op = parts[0].lower()

    # HALT
    if op == "halt":
        return (HALT_OPCODE << 24)

    # R-type
    if op in INSTR_R:
        return assemble_R(op, parts[1], parts[2], parts[3])

    # Immediate arithmetic
    if op in INSTR_I:
        return assemble_I(op, parts[1], parts[2], parts[3])

    # memory
    if op in INSTR_MEM:
        return assemble_MEM(op, parts[1], parts[2], parts[3])

    # branches
    if op in INSTR_BRANCH:
        return assemble_BRANCH(op, parts[1], parts[2], parts[3])

    # jumps
    if op in ("j", "jal"):
        return assemble_J(op, parts[1])

    if op == "jr":
        return assemble_JR(op, parts[1])

    # LCLH / LCLL
    if op in INSTR_LCL:
        return assemble_LCLH_LCLL(op, parts[1], parts[2])

    raise ValueError(f"Instrução desconhecida: {op}")


def assemble_file(input_path, output_path):
    result = []
    with open(input_path, "r") as f:
        for line in f:
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue
            word = assemble_line(clean)
            if word is not None:
                result.append(word)

    with open(output_path, "w") as f:
        f.write("address 0000000000000000\n")
        for w in result:
            f.write(f"{w:032b}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python -m src.interpretador.assembler <input.s> <output.txt>")
        sys.exit(1)

    assemble_file(sys.argv[1], sys.argv[2])
    print(f"Arquivo binário gerado em: {sys.argv[2]}")
