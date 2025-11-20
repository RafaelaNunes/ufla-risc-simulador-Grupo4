# src/simulador/cpu.py

from src.simulador.registers import create_registers, read_reg, write_reg
from src.simulador.instruction import (
    get_opcode, get_ra, get_rb, get_rc,
    get_const16_high, get_const16_low, get_jump_address
)

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

        # Saída do EX/MEM
        self.exec_result = None
        self.exec_rc = None

    # --------------------------
    # Atualizar flags
    # --------------------------
    def update_flags(self, value):
        val = value & 0xFFFFFFFF

        self.flag_zero = 1 if val == 0 else 0
        self.flag_neg = 1 if ((val >> 31) & 1) else 0

        return val

    # --------------------------
    # IF — buscar instrução
    # --------------------------
    def IF(self):
        self.ir = self.memory[self.pc]
        self.pc += 1

        if self.ir == HALT_INSTRUCTION:
            self.halted = True

    # --------------------------
    # ID — decodificar instrução
    # --------------------------
    def ID(self):
        self.opcode = get_opcode(self.ir)
        self.ra = get_ra(self.ir)
        self.rb = get_rb(self.ir)
        self.rc = get_rc(self.ir)

        self.const_high = get_const16_high(self.ir)
        self.const_low = get_const16_low(self.ir)
        self.jump_addr = get_jump_address(self.ir)

    # --------------------------
    # Implementações das instruções
    # --------------------------
    def exec_add(self):
        a = self.registers[self.ra]
        b = self.registers[self.rb]
        result = a + b

        self.flag_carry = 1 if result > 0xFFFFFFFF else 0

        sa = (a >> 31) & 1
        sb = (b >> 31) & 1
        sr = (result >> 31) & 1
        self.flag_overflow = 1 if (sa == sb and sa != sr) else 0

        result &= 0xFFFFFFFF
        result = self.update_flags(result)

        self.exec_result = result
        self.exec_rc = self.rc

    def exec_sub(self):
        a = self.registers[self.ra]
        b = self.registers[self.rb]
        result = a - b

        self.flag_carry = 1 if a >= b else 0

        sa = (a >> 31) & 1
        sb = (b >> 31) & 1
        sr = (result >> 31) & 1
        self.flag_overflow = 1 if (sa != sb and sa != sr) else 0

        result &= 0xFFFFFFFF
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
        result = self.registers[self.ra] ^ self.registers[self.rb]
        result = self.update_flags(result)
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = result
        self.exec_rc = self.rc

    def exec_or(self):
        result = self.registers[self.ra] | self.registers[self.rb]
        result = self.update_flags(result)
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = result
        self.exec_rc = self.rc

    def exec_and(self):
        result = self.registers[self.ra] & self.registers[self.rb]
        result = self.update_flags(result)
        self.flag_carry = 0
        self.flag_overflow = 0
        self.exec_result = result
        self.exec_rc = self.rc

    # --------------------------
    # EX/MEM
    # --------------------------
    def EX_MEM(self):
        self.exec_result = None
        self.exec_rc = self.rc

        if self.opcode == 1:
            self.exec_add()
        elif self.opcode == 2:
            self.exec_sub()
        elif self.opcode == 3:
            self.exec_zero()
        elif self.opcode == 4:
            self.exec_xor()
        elif self.opcode == 5:
            self.exec_or()
        elif self.opcode == 7:
            self.exec_and()
        # Outras instruções virão depois

    # --------------------------
    # WB
    # --------------------------
    def WB(self):
        if self.exec_result is not None:
            write_reg(self.registers, self.exec_rc, self.exec_result)

    # --------------------------
    # STEP — aqui estava seu erro!
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
    # RUN
    # --------------------------
    def run(self):
        while not self.halted:
            self.step()
