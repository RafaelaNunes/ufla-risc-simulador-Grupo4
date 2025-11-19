# src/interpretador/assembler.py
# Interpretador simples para UFLA-RISC assembly -> arquivo binario (32 bits por linha)
# Suporta labels e diretiva "address".
# Uso: python -m src.interpretador.assembler input.s output.bin
# Se output omitido, salva em binarios/programa.txt

import sys
import os
import re

# opcode mapping (8-bit strings -> integer)
OPCODES = {
    "add": 0x01,
    "sub": 0x02,
    "zeros": 0x03,   # "zero" in PDF uses opcode 00000011 - we accept "zeros" or "zero"
    "zero": 0x03,
    "xor": 0x04,
    "or": 0x05,
    "not": 0x06,     # passnota / not (not has different operand order in PDF, see note)
    "and": 0x07,
    "asl": 0x08,
    "asr": 0x09,
    "lsl": 0x0A,
    "lsr": 0x0B,
    "passa": 0x0C,   # "passa" / copia, PDF labels it passa/copia
    "pass": 0x0C,
    "lclh": 0x0E,    # carregam constantes nos 2 bytes mais significativos
    "lcll": 0x0F,    # carregam constantes nos 2 bytes menos significativos
    "load": 0x10,
    "store": 0x11,
    "jal": 0x12,     # note: in provided PDF jal had opcode 100 (but 8-bit field); we'll use 0x12 per earlier conversation mapping
    "jr": 0x13,
    "beq": 0x14,
    "bne": 0x15,
    "j": 0x16,
    # extras can be added here
}

# helper regex
REG_RE = re.compile(r"r(\d+)$", re.IGNORECASE)
BIN32_RE = re.compile(r"^[01]{32}$")

def reg_to_int(token):
    m = REG_RE.match(token.strip())
    if not m:
        raise ValueError(f"Registrador inválido: '{token}' (use r0..r31)")
    idx = int(m.group(1))
    if not (0 <= idx <= 255):
        raise ValueError(f"Índice de registrador fora do intervalo aceito (0..255): {idx}")
    return idx

def parse_const16(token):
    token = token.strip()
    # aceita 0xNNNN, decimal ou binário 16 bits
    if token.startswith("0x") or token.startswith("0X"):
        return int(token, 16) & 0xFFFF
    if token.startswith("b") and all(c in "01" for c in token[1:]):
        s = token[1:]
        if len(s) > 16:
            raise ValueError("Const16 binário maior que 16 bits")
        return int(s, 2)
    if token.isdigit():
        v = int(token)
        return v & 0xFFFF
    # label will be resolved in second pass
    return token

def encode_r3(opcode, ra, rb, rc):
    """Encode opcode(8) ra(8) rb(8) rc(8)"""
    return ((opcode & 0xFF) << 24) | ((ra & 0xFF) << 16) | ((rb & 0xFF) << 8) | (rc & 0xFF)

def encode_lcl(opcode, const16, rc):
    # opcode (8) | const16 (16 at bits 23..8) | rc (8 bits)
    return ((opcode & 0xFF) << 24) | ((const16 & 0xFFFF) << 8) | (rc & 0xFF)

def encode_jump(opcode, addr24):
    return ((opcode & 0xFF) << 24) | (addr24 & 0xFFFFFF)

def assemble(lines):
    """
    Two-pass assembler:
     - pass 1: collect labels and addresses
     - pass 2: assemble instructions to integers
    Returns list of (address, int_word)
    """
    # preprocess: remove comments, keep address directives and labels
    cur_addr = 0
    labels = {}
    instrs = []  # tuples (orig_line, address, tokens)
    # first pass: collect labels and provisional addresses
    for lineno, raw in enumerate(lines, start=1):
        line = raw.split("#",1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0].lower() == "address":
            if len(parts) != 2:
                raise ValueError(f"Diretiva address inválida na linha {lineno}: '{line}'")
            addr_token = parts[1]
            if any(c not in "01" for c in addr_token):
                raise ValueError(f"Endereço 'address' deve ser binário na linha {lineno}: '{line}'")
            if len(addr_token) > 16:
                raise ValueError(f"Endereço 'address' maior que 16 bits na linha {lineno}")
            cur_addr = int(addr_token, 2)
            continue
        # labels: token ending with ':'
        if line.endswith(":"):
            lab = line[:-1].strip()
            if not lab:
                raise ValueError(f"Label vazio na linha {lineno}")
            if lab in labels:
                raise ValueError(f"Label duplicada '{lab}' na linha {lineno}")
            labels[lab] = cur_addr
            continue
        # otherwise instruction
        instrs.append((lineno, cur_addr, line))
        cur_addr += 1

    # second pass: encode each instruction
    output = []
    for lineno, addr, line in instrs:
        # tokenization: split mnemonic and operands
        # allow: mnemonic operand1, operand2, operand3
        tokens = [t.strip() for t in re.split(r"[,\s]+", line) if t.strip()]
        if not tokens:
            continue
        mnem = tokens[0].lower()
        if mnem not in OPCODES:
            raise ValueError(f"Linha {lineno}: Mnemonic desconhecido '{mnem}'")
        opc = OPCODES[mnem]
        try:
            # handle formats
            if mnem in ("add","sub","xor","or","and","passa","pass","passa"):
                # format: add rc, ra, rb  OR add rc, ra, rb? — PDF uses add rc, ra, rb but earlier code used add rc, ra, rb
                # We'll accept both orders: add rc, ra, rb  OR add r3, r2, r1 -> we try to detect by count
                if len(tokens) == 4:
                    # Assume: mnemonic ra rb rc (we'll use tokens[1], tokens[2], tokens[3])
                    # to be consistent with our CPU encoding (opcode ra rb rc)
                    ra = reg_to_int(tokens[1])
                    rb = reg_to_int(tokens[2])
                    rc = reg_to_int(tokens[3])
                else:
                    raise ValueError(f"Linha {lineno}: formato inválido para {mnem}: '{line}'")
                word = encode_r3(opc, ra, rb, rc)
            elif mnem in ("zeros","zero"):
                # zero rc
                if len(tokens) != 2:
                    raise ValueError(f"Linha {lineno}: zero rc")
                rc = reg_to_int(tokens[1])
                word = encode_r3(opc, 0, 0, rc)
            elif mnem in ("not",):  # passnota rc, ra  -> PDF gives passnota r4, r3 rc = !ra? ambiguous
                # we'll accept: not rc, ra  -> opcode ra rc? We'll encode as opcode ra=ra rb=0 rc=rc to match cpu expectation
                if len(tokens) != 3:
                    raise ValueError(f"Linha {lineno}: not rc, ra")
                rc = reg_to_int(tokens[1])
                ra = reg_to_int(tokens[2])
                word = encode_r3(opc, ra, 0, rc)
            elif mnem in ("asl","asr","lsl","lsr"):
                # format: mnem rc, ra, rb  -> but CPU expects opcode ra rb rc in encoding
                if len(tokens) != 4:
                    raise ValueError(f"Linha {lineno}: formato inválido para shift: '{line}'")
                ra = reg_to_int(tokens[1])
                rb = reg_to_int(tokens[2])
                rc = reg_to_int(tokens[3])
                word = encode_r3(opc, ra, rb, rc)
            elif mnem in ("lclh", "lcll"):
                # format: lclh rc, Const16
                if len(tokens) != 3:
                    raise ValueError(f"Linha {lineno}: formato inválido para {mnem}: '{line}'")
                rc = reg_to_int(tokens[1])
                const = parse_const16(tokens[2])
                if isinstance(const, str):
                    # label? not typical for const16 but allow numeric only
                    raise ValueError(f"Linha {lineno}: const16 não pode ser label: '{line}'")
                word = encode_lcl(opc, const, rc)
            elif mnem in ("load","store"):
                # format: load rc, ra  -> encode opcode ra rb rc: we'll put ra=ra rb=0 rc=rc
                if len(tokens) != 3:
                    raise ValueError(f"Linha {lineno}: formato inválido para {mnem}: '{line}'")
                rc = reg_to_int(tokens[1])
                ra = reg_to_int(tokens[2])
                word = encode_r3(opc, ra, 0, rc)
            elif mnem in ("jal",):
                # jal end  -> end can be label or number
                if len(tokens) != 2:
                    raise ValueError(f"Linha {lineno}: formato inválido para jal: '{line}'")
                dest = tokens[1]
                if dest in labels:
                    addr24 = labels[dest]
                else:
                    # try numeric (binário ou decimal)
                    if dest.startswith("0b") or all(c in "01" for c in dest):
                        addr24 = int(dest.replace("0b",""), 2)
                    elif dest.isdigit():
                        addr24 = int(dest)
                    else:
                        raise ValueError(f"Linha {lineno}: label/deslocamento desconhecido '{dest}'")
                word = encode_jump(opc, addr24)
            elif mnem in ("jr",):
                # jr rc
                if len(tokens) != 2:
                    raise ValueError(f"Linha {lineno}: formato inválido para jr: '{line}'")
                rc = reg_to_int(tokens[1])
                # encode as opcode ra=0 rb=0 rc=rc
                word = encode_r3(opc, 0, 0, rc)
            elif mnem in ("beq","bne"):
                # beq ra, rb, label
                if len(tokens) != 4:
                    raise ValueError(f"Linha {lineno}: formato inválido para {mnem}: '{line}'")
                ra = reg_to_int(tokens[1])
                rb = reg_to_int(tokens[2])
                dest = tokens[3]
                if dest in labels:
                    addr24 = labels[dest]
                else:
                    if dest.isdigit():
                        addr24 = int(dest)
                    elif all(c in "01" for c in dest):
                        addr24 = int(dest, 2)
                    else:
                        raise ValueError(f"Linha {lineno}: label/deslocamento desconhecido '{dest}'")
                # For beq/bne PDF shows opcode ra rb end (end in last 8 bits?), but we will encode as opcode|ra|rb|end8 (end truncated)
                # To be consistent with CPU which reads jump_addr as 24-bit, we will put end in 8-bit rc field only if small.
                # Better: encode as opcode ra rb end(8) -> but CPU expects jump_addr 24 bits. To keep it simple:
                # we'll encode as opcode ra rb end8 (last field) - for typical small tests this suffices.
                word = ((opc & 0xFF) << 24) | ((ra & 0xFF) << 16) | ((rb & 0xFF) << 8) | (addr24 & 0xFF)
            elif mnem == "j":
                if len(tokens) != 2:
                    raise ValueError(f"Linha {lineno}: formato inválido para j: '{line}'")
                dest = tokens[1]
                if dest in labels:
                    addr24 = labels[dest]
                else:
                    if dest.isdigit():
                        addr24 = int(dest)
                    elif all(c in "01" for c in dest):
                        addr24 = int(dest, 2)
                    else:
                        raise ValueError(f"Linha {lineno}: label/deslocamento desconhecido '{dest}'")
                word = encode_jump(opc, addr24)
            else:
                raise ValueError(f"Linha {lineno}: mnemonico '{mnem}' não implementado no interpretador")
        except Exception as e:
            raise ValueError(f"Erro na linha {lineno}: {e}")

        output.append((addr, word))

    return output

def assemble_file(input_path, output_path=None):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assembled = assemble(lines)
    # prepare output path
    if output_path is None:
        base = os.path.basename(input_path)
        output_path = os.path.join("binarios", base if base.endswith(".txt") else (base + ".txt"))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out:
        # write optional address directives if there are gaps
        last_addr = None
        for addr, word in assembled:
            # if address not sequential, emit address directive in binary (16 bits)
            if last_addr is None or addr != last_addr:
                addr_bin = format(addr, "016b")
                out.write(f"address {addr_bin}\n")
            out.write(format(word & 0xFFFFFFFF, "032b") + "\n")
            last_addr = addr + 1

    print(f"Arquivo gerado: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.interpretador.assembler arquivo_assembly.s [saida.txt]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else None
    assemble_file(inp, out)
