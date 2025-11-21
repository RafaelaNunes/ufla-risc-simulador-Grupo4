# src/simulador/cpu.py
# Pipeline 5 estágios: IF - ID - EX - MEM - WB
# Sem hazard detection nem forwarding. Simples e determinístico.
from src.simulador.registers import create_registers, write_reg, read_reg
from src.simulador.instruction import (
    get_opcode, get_ra, get_rb, get_rc,
    get_const16_high, get_const16_low, get_jump_address
)
from src.simulador.memory import MEMORY_SIZE_WORDS

HALT_INSTRUCTION = 0xFFFFFFFF

def bubble():
    return {
        "ir": 0,
        "opcode": 0,
        "ra": 0,
        "rb": 0,
        "rc": 0,
        "const_high": 0,
        "const_low": 0,
        "jump_addr": 0,
        "valid": False
    }

class CPU:
    def __init__(self, memory):
        self.memory = memory
        self.registers = create_registers()
        self.pc = 0
        self.halted = False

        # flags
        self.flag_neg = 0
        self.flag_zero = 0
        self.flag_carry = 0
        self.flag_overflow = 0

        # pipeline regs
        self.IF_ID = bubble()
        self.ID_EX = bubble()
        self.EX_MEM = bubble()
        self.MEM_WB = bubble()

        # last fetched IR (debug)
        self.ir = 0
        self.cycle = 0

    # helpers
    def update_flags(self, value):
        val = value & 0xFFFFFFFF
        self.flag_zero = 1 if val == 0 else 0
        self.flag_neg = 1 if ((val >> 31) & 1) else 0
        return val

    def reg(self, idx):
        return read_reg(self.registers, idx & 0x1F)

    def decode_ir(self, ir):
        return {
            "ir": ir,
            "opcode": get_opcode(ir),
            "ra": get_ra(ir),
            "rb": get_rb(ir),
            "rc": get_rc(ir),
            "const_high": get_const16_high(ir),
            "const_low": get_const16_low(ir),
            "jump_addr": get_jump_address(ir),
            "valid": True
        }

    # IF stage
    def IF(self):
        if not (0 <= self.pc < MEMORY_SIZE_WORDS):
            self.halted = True
            return
        ir = self.memory[self.pc]
        self.ir = ir
        self.IF_ID = self.decode_ir(ir)
        self.IF_ID["pc"] = self.pc
        self.pc += 1

    # ID stage
    def ID(self):
        if not self.IF_ID.get("valid", False):
            self.ID_EX = bubble()
            return
        dec = {
            "ir": self.IF_ID["ir"],
            "opcode": self.IF_ID["opcode"],
            "ra": self.IF_ID["ra"],
            "rb": self.IF_ID["rb"],
            "rc": self.IF_ID["rc"],
            "const_high": self.IF_ID["const_high"],
            "const_low": self.IF_ID["const_low"],
            "jump_addr": self.IF_ID["jump_addr"],
            "pc": self.IF_ID.get("pc", 0),
            "valid": True
        }
        # read register file now (no forwarding)
        dec["reg_ra_val"] = self.reg(dec["ra"])
        dec["reg_rb_val"] = self.reg(dec["rb"])
        self.ID_EX = dec

    # EX stage (compute ALU result or prepare addresses)
    def EX(self):
        if not self.ID_EX.get("valid", False):
            self.EX_MEM = bubble()
            return

        opcode = self.ID_EX["opcode"]
        a_val = self.ID_EX.get("reg_ra_val", 0)
        b_val = self.ID_EX.get("reg_rb_val", 0)
        rc = self.ID_EX["rc"]
        const_high = self.ID_EX["const_high"]
        const_low = self.ID_EX["const_low"]
        jump_addr = self.ID_EX["jump_addr"]
        pc_of_inst = self.ID_EX.get("pc", 0)

        exec_result = None
        exec_rc = rc
        branch_taken = False
        branch_target = None

        # ALU ops
        if opcode == 1:  # ADD
            res = (a_val + b_val) & 0xFFFFFFFF
            self.flag_carry = 1 if (a_val + b_val) > 0xFFFFFFFF else 0
            sa, sb, sr = (a_val >> 31) & 1, (b_val >> 31) & 1, (res >> 31) & 1
            self.flag_overflow = 1 if (sa == sb and sa != sr) else 0
            exec_result = self.update_flags(res)
        elif opcode == 2:  # SUB
            res = (a_val - b_val) & 0xFFFFFFFF
            self.flag_carry = 1 if a_val >= b_val else 0
            sa, sb, sr = (a_val >> 31) & 1, (b_val >> 31) & 1, (res >> 31) & 1
            self.flag_overflow = 1 if (sa != sb and sa != sr) else 0
            exec_result = self.update_flags(res)
        elif opcode == 3:  # ZERO
            exec_result = self.update_flags(0)
            self.flag_zero = 1
        elif opcode == 4:  # XOR
            res = (a_val ^ b_val) & 0xFFFFFFFF
            exec_result = self.update_flags(res)
        elif opcode == 5:  # OR
            res = (a_val | b_val) & 0xFFFFFFFF
            exec_result = self.update_flags(res)
        elif opcode == 7:  # AND
            res = (a_val & b_val) & 0xFFFFFFFF
            exec_result = self.update_flags(res)

        # Shifts (if present)
        elif opcode == 16:  # ASL
            shift = b_val & 31
            wide = (a_val << shift) & 0xFFFFFFFFFFFFFFFF
            res = wide & 0xFFFFFFFF
            exec_result = self.update_flags(res)
            self.flag_carry = 1 if (wide >> 32) & 1 else 0
        elif opcode == 17:  # ASR
            shift = b_val & 31
            if a_val & 0x80000000:
                signed = a_val - (1 << 32)
                res = (signed >> shift) & 0xFFFFFFFF
            else:
                res = (a_val >> shift) & 0xFFFFFFFF
            exec_result = self.update_flags(res)
        elif opcode == 18:  # LSL
            shift = b_val & 31
            wide = (a_val << shift) & 0xFFFFFFFFFFFFFFFF
            res = wide & 0xFFFFFFFF
            exec_result = self.update_flags(res)
            self.flag_carry = 1 if (wide >> 32) & 1 else 0
        elif opcode == 19:  # LSR
            shift = b_val & 31
            res = (a_val >> shift) & 0xFFFFFFFF
            exec_result = self.update_flags(res)

        # CONSTS
        elif opcode == 20:  # LCLH
            high = (const_high & 0xFFFF) << 16
            low = self.reg(rc) & 0xFFFF
            res = (high | low) & 0xFFFFFFFF
            exec_result = self.update_flags(res)
        elif opcode == 21:  # LCLL
            high = (self.reg(rc) & 0xFFFF0000)
            low = const_high & 0xFFFF
            res = (high | low) & 0xFFFFFFFF
            exec_result = self.update_flags(res)

        # LOAD / STORE with immediate
        elif opcode == 22:  # LW rc = MEM[ra + imm16]
            addr = (a_val + (const_low & 0xFFFF))
            # we place address in EX_MEM and actual read in MEM
            self.EX_MEM = {
                "ir": self.ID_EX["ir"],
                "valid": True,
                "opcode": opcode,
                "ra": self.ID_EX["ra"],
                "rb": self.ID_EX["rb"],
                "rc": rc,
                "address": addr,
                "exec_rc": rc,
                "exec_result": None
            }
            return
        elif opcode == 23:  # SW MEM[ra+imm16] = rc_value
            addr = (a_val + (const_low & 0xFFFF))
            store_value = b_val
            self.EX_MEM = {
                "ir": self.ID_EX["ir"],
                "valid": True,
                "opcode": opcode,
                "ra": self.ID_EX["ra"],
                "rb": self.ID_EX["rb"],
                "rc": rc,
                "address": addr,
                "store_value": store_value
            }
            return

        # Branches / jumps
        elif opcode == 24:  # JAL
            ret = pc_of_inst + 1
            exec_result = ret
            exec_rc = 31
            dest = jump_addr & 0xFFFFFF
            # set PC immediately (simple behavior)
            if 0 <= dest < MEMORY_SIZE_WORDS:
                self.pc = dest
            else:
                self.halted = True
        elif opcode == 25:  # JR
            dest = a_val
            if 0 <= dest < MEMORY_SIZE_WORDS:
                self.pc = dest
            else:
                self.halted = True
        elif opcode == 26:  # BEQ
            if a_val == b_val:
                dest = jump_addr
                if 0 <= dest < MEMORY_SIZE_WORDS:
                    self.pc = dest
                else:
                    self.halted = True
        elif opcode == 27:  # BNE
            if a_val != b_val:
                dest = jump_addr
                if 0 <= dest < MEMORY_SIZE_WORDS:
                    self.pc = dest
                else:
                    self.halted = True
        elif opcode == 28:  # J
            dest = jump_addr
            if 0 <= dest < MEMORY_SIZE_WORDS:
                self.pc = dest
            else:
                self.halted = True

        # default: write EX/MEM
        self.EX_MEM = {
            "ir": self.ID_EX["ir"],
            "valid": True,
            "opcode": opcode,
            "ra": self.ID_EX["ra"],
            "rb": self.ID_EX["rb"],
            "rc": rc,
            "exec_result": exec_result,
            "exec_rc": exec_rc
        }

    # MEM stage
    def MEM(self):
        if not self.EX_MEM.get("valid", False):
            self.MEM_WB = bubble()
            return

        opcode = self.EX_MEM.get("opcode")
        memwb = {
            "ir": self.EX_MEM.get("ir"),
            "opcode": opcode,
            "valid": True,
            "exec_rc": self.EX_MEM.get("exec_rc"),
            "exec_result": None
        }

        if opcode == 22:  # LW
            addr = self.EX_MEM.get("address", 0)
            if not (0 <= addr < MEMORY_SIZE_WORDS):
                self.halted = True
                return
            value = self.memory[addr] & 0xFFFFFFFF
            memwb["exec_result"] = self.update_flags(value)
        elif opcode == 23:  # SW
            addr = self.EX_MEM.get("address", 0)
            if not (0 <= addr < MEMORY_SIZE_WORDS):
                self.halted = True
                return
            self.memory[addr] = self.EX_MEM.get("store_value", 0) & 0xFFFFFFFF
            memwb["exec_result"] = None
        else:
            memwb["exec_result"] = self.EX_MEM.get("exec_result")

        self.MEM_WB = memwb

    # WB stage
    def WB(self):
        if not self.MEM_WB.get("valid", False):
            return
        if self.MEM_WB.get("exec_result") is not None:
            dest = self.MEM_WB.get("exec_rc") & 0x1F
            write_reg(self.registers, dest, self.MEM_WB.get("exec_result"))
        # HALT detection
        ir = self.MEM_WB.get("ir")
        if ir == HALT_INSTRUCTION:
            self.halted = True

    # step: advance one clock (WB -> MEM -> EX -> ID -> IF)
    def step(self):
        if self.halted:
            return
        self.cycle += 1
        # advance stages in reverse order
        self.WB()
        self.MEM()
        self.EX()
        self.ID()
        self.IF()

    # utility: whether pipeline has any valid instruction left
    def any_pipeline_active(self):
        return (self.IF_ID.get("valid", False) or self.ID_EX.get("valid", False)
                or self.EX_MEM.get("valid", False) or self.MEM_WB.get("valid", False))
