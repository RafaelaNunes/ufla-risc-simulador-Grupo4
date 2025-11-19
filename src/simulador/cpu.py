# src/simulador/cpu.py
# CPU completa do simulador UFLA-RISC com máscara de registradores,
# operações ALU, shifts, loads/stores, jumps e flags.
# 100% compatível com loader, registers e memory.

from src.simulador.registers import create_registers, write_reg
from src.simulador.instruction import (
    get_opcode, get_ra, get_rb, get_rc,
    get_const16_high, get_const16_low, get_jump_address
)
from src.simulador.memory import MEMORY_SIZE_WORDS

HALT_INSTRUCTION = 0xFFFFFFFF


class CPU:
    def __init__(self, memory):
        self.memory = memory
        self.registers = create_registers()
        self.pc = 0
        self.ir = 0
        self.halted = False

        # Flags
        self.flag_neg = 0
        self.flag_zero = 0
        self.flag_carry = 0
        self.flag_overflow = 0

        # Execução intermediária
        self.exec_result = None
        self.exec_rc = None

        # Decodificados
        self.opcode = 0
        self.ra = 0
        self.rb = 0
        self.rc = 0
        self.const_high = 0
        self.const_low = 0
        self.jump_addr = 0

    # --------------------------
    # Flags
    # --------------------------
    def update_flags(self, value):
        val = value & 0xFFFFFFFF
        self.flag_zero = 1 if val == 0 else 0
        self.flag_neg = 1 if (val >> 31) & 1 else 0
        return val

    def reg(self, idx):
        """Acessa registrador com máscara de 5 bits"""
        return self.registers[idx & 0x1F]

    # --------------------------
    # IF
    # --------------------------
    def IF(self):
        self.ir = self.memory[self.pc]
        self.pc += 1
        if self.ir == HALT_INSTRUCTION:
            self.halted = True

    # --------------------------
    # ID
    # --------------------------
    def ID(self):
        self.opcode = get_opcode(self.ir)
        self.ra = get_ra(self.ir)
        self.rb = get_rb(self.ir)
        self.rc = get_rc(self.ir)
        self.const_high = get_const16_high(self.ir)
        self.const_low = get_const16_low(self.ir)
        self.jump_addr = get_jump_address(self.ir)

    # ==========================================================
    # EXE — INSTRUÇÕES
    # ==========================================================

    # --- ALU ---
    def exec_add(self):
        a = self.reg(self.ra)
        b = self.reg(self.rb)
        result = a + b
        self.flag_carry = 1 if result > 0xFFFFFFFF else 0
        sa, sb, sr = (a >> 31) & 1, (b >> 31) & 1, (result >> 31) & 1
        self.flag_overflow = 1 if (sa == sb and sa != sr) else 0
        result = self.update_flags(result)
        self.exec_result = result
        self.exec_rc = self.rc

    def exec_sub(self):
        a = self.reg(self.ra)
        b = self.reg(self.rb)
        result = a - b
        self.flag_carry = 1 if a >= b else 0
        sa, sb, sr = (a >> 31) & 1, (b >> 31) & 1, (result >> 31) & 1
        self.flag_overflow = 1 if (sa != sb and sa != sr) else 0
        result = self.update_flags(result)
        self.exec_result = result
        self.exec_rc = self.rc

    def exec_zero(self):
        self.exec_result = 0
        self.exec_rc = self.rc
        self.flag_zero = 1
        self.flag_neg = 0
        self.flag_carry = 0
        self.flag_overflow = 0

    def exec_xor(self):
        result = self.reg(self.ra) ^ self.reg(self.rb)
        self.exec_result = self.update_flags(result)
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_rc = self.rc

    def exec_or(self):
        result = self.reg(self.ra) | self.reg(self.rb)
        self.exec_result = self.update_flags(result)
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_rc = self.rc

    def exec_and(self):
        result = self.reg(self.ra) & self.reg(self.rb)
        self.exec_result = self.update_flags(result)
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_rc = self.rc

    # --- SHIFTS ---
    def exec_asl(self):
        value = self.reg(self.ra)
        shift = self.reg(self.rb) & 31
        wide = value << shift
        self.flag_carry = 1 if (wide & (~0xFFFFFFFF)) else 0
        result = self.update_flags(wide & 0xFFFFFFFF)
        self.exec_result = result
        self.exec_rc = self.rc

    def exec_asr(self):
        value = self.reg(self.ra)
        shift = self.reg(self.rb) & 31
        if value & 0x80000000:
            signed = value - (1 << 32)
            result = (signed >> shift) & 0xFFFFFFFF
        else:
            result = (value >> shift) & 0xFFFFFFFF
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = self.update_flags(result)
        self.exec_rc = self.rc

    def exec_lsl(self):
        value = self.reg(self.ra)
        shift = self.reg(self.rb) & 31
        wide = value << shift
        self.flag_carry = 1 if (wide & (~0xFFFFFFFF)) else 0
        result = self.update_flags(wide & 0xFFFFFFFF)
        self.exec_result = result
        self.exec_rc = self.rc

    def exec_lsr(self):
        value = self.reg(self.ra)
        shift = self.reg(self.rb) & 31
        result = (value >> shift) & 0xFFFFFFFF
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = self.update_flags(result)
        self.exec_rc = self.rc

    # --- CONSTS ---
    def exec_lclh(self):
        high = (self.const_high & 0xFFFF) << 16
        low = self.reg(self.rc) & 0xFFFF
        result = high | low
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = self.update_flags(result)
        self.exec_rc = self.rc

    def exec_lcll(self):
        high = self.reg(self.rc) & 0xFFFF0000
        low = self.const_high & 0xFFFF
        result = high | low
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = self.update_flags(result)
        self.exec_rc = self.rc

    # --- LOAD / STORE ---
    def exec_ld(self):
        addr = self.reg(self.ra)
        if addr >= MEMORY_SIZE_WORDS:
            self.halted = True
            return
        value = self.memory[addr] & 0xFFFFFFFF
        self.exec_result = self.update_flags(value)
        self.exec_rc = self.rc
        self.flag_carry = 0
        self.flag_overflow = 0

    def exec_st(self):
        addr = self.reg(self.rc)
        if addr >= MEMORY_SIZE_WORDS:
            self.halted = True
            return
        self.memory[addr] = self.reg(self.ra) & 0xFFFFFFFF
        self.exec_result = None

    # --- JUMPS ---
    def exec_jal(self):
        ret = self.pc
        self.exec_result = ret
        self.exec_rc = 31
        dest = self.jump_addr & 0xFFFFFF
        if dest >= MEMORY_SIZE_WORDS:
            self.halted = True
            return
        self.pc = dest

    def exec_jr(self):
        dest = self.reg(self.rc)
        if dest >= MEMORY_SIZE_WORDS:
            self.halted = True
            return
        self.pc = dest
        self.exec_result = None

    def exec_beq(self):
        if self.reg(self.ra) == self.reg(self.rb):
            dest = self.jump_addr
            if dest >= MEMORY_SIZE_WORDS:
                self.halted = True
                return
            self.pc = dest
        self.exec_result = None

    def exec_bne(self):
        if self.reg(self.ra) != self.reg(self.rb):
            dest = self.jump_addr
            if dest >= MEMORY_SIZE_WORDS:
                self.halted = True
                return
            self.pc = dest
        self.exec_result = None

    def exec_j(self):
        dest = self.jump_addr
        if dest >= MEMORY_SIZE_WORDS:
            self.halted = True
            return
        self.pc = dest
        self.exec_result = None

    # --------------------------
    # EX/MEM dispatcher
    # --------------------------
    def EX_MEM(self):
        self.exec_result = None
        self.exec_rc = self.rc

        match self.opcode:
            case 1: self.exec_add()
            case 2: self.exec_sub()
            case 3: self.exec_zero()
            case 4: self.exec_xor()
            case 5: self.exec_or()
            case 7: self.exec_and()

            case 16: self.exec_asl()
            case 17: self.exec_asr()
            case 18: self.exec_lsl()
            case 19: self.exec_lsr()

            case 20: self.exec_lclh()
            case 21: self.exec_lcll()

            case 22: self.exec_ld()
            case 23: self.exec_st()

            case 24: self.exec_jal()
            case 25: self.exec_jr()
            case 26: self.exec_beq()
            case 27: self.exec_bne()
            case 28: self.exec_j()

            case _:
                self.exec_result = None

    # --------------------------
    # WB
    # --------------------------
    def WB(self):
        if self.exec_result is not None:
            write_reg(self.registers, self.exec_rc & 0x1F, self.exec_result)

    # --------------------------
    # Step
    # --------------------------
    def step(self):
        if self.halted:
            return
        self.IF()
        if self.halted:
            return
        self.ID()
        self.EX_MEM()
        self.WB()

    # --------------------------
    # Run
    # --------------------------
    def run(self):
        while not self.halted:
            self.step()
