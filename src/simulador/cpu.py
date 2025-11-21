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
    """Cria uma instrução bolha (NOP) para o pipeline."""
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

        # flags do processador
        self.flag_neg = 0
        self.flag_zero = 0
        self.flag_carry = 0
        self.flag_overflow = 0

        # Registradores de Pipeline (iniciam como bolhas)
        self.IF_ID = bubble()
        self.ID_EX = bubble()
        self.EX_MEM = bubble()
        self.MEM_WB = bubble()

        # Metadados de debug
        self.ir = 0
        self.cycle = 0

    # Funções auxiliares
    def update_flags(self, value):
        """Atualiza as flags Z e N com base no valor de 32 bits."""
        val = value & 0xFFFFFFFF
        self.flag_zero = 1 if val == 0 else 0
        self.flag_neg = 1 if ((val >> 31) & 1) else 0
        return val

    def reg(self, idx):
        """Lê um registrador, aplicando máscara no índice."""
        return read_reg(self.registers, idx & 0x1F)

    def decode_ir(self, ir):
        """Decodifica uma instrução (IR) em seus campos."""
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

    # Estágio IF (Instruction Fetch)
    def IF(self):
        if not (0 <= self.pc < MEMORY_SIZE_WORDS):
            self.halted = True
            return
        ir = self.memory[self.pc]
        self.ir = ir
        self.IF_ID = self.decode_ir(ir)
        self.IF_ID["pc"] = self.pc
        self.pc += 1
        
        # Detecção de HALT antecipada
        if ir == HALT_INSTRUCTION:
             self.halted = True

    # Estágio ID (Instruction Decode)
    def ID(self):
        if not self.IF_ID.get("valid", False):
            self.ID_EX = bubble()
            return
        
        # Cria o registrador de pipeline ID_EX
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
        
        # Leitura do Arquivo de Registradores
        dec["reg_ra_val"] = self.reg(dec["ra"])
        dec["reg_rb_val"] = self.reg(dec["rb"])
        self.ID_EX = dec

    # Estágio EX (Execute)
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
        exec_rc = rc # O registrador destino é, por padrão, RC
        
        # Lógica de Execução
        
        # 1. ALU (ADD, SUB, ZERO, XOR, OR, AND)
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

        # 2. Shifts
        elif opcode == 16:  # ASL
            shift = b_val & 31
            wide = (a_val << shift) & 0xFFFFFFFFFFFFFFFF
            res = wide & 0xFFFFFFFF
            exec_result = self.update_flags(res)
            self.flag_carry = 1 if (wide >> 32) & 1 else 0
        elif opcode == 17:  # ASR (Shift Aritmético para a Direita)
            shift = b_val & 31
            if a_val & 0x80000000:
                # Simula o comportamento de signed shift
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

        # 3. CONSTS
        elif opcode == 20:  # LCLH (Load Constant High)
            # LCLH: Carrega nos 16 bits altos
            high = (const_high & 0xFFFF) << 16
            low = self.reg(rc) & 0xFFFF # Mantém os 16 bits baixos
            res = (high | low) & 0xFFFFFFFF
            exec_result = self.update_flags(res)
        
        elif opcode == 21:  # LCLL (Load Constant Low)
            # LCLL: Carrega nos 16 bits baixos e zera os altos
            constant_16_val = (const_high << 8) | const_low # Usando high e low para formar os 16 bits
            res = constant_16_val
            exec_result = self.update_flags(res)

        # 4. LOAD / STORE
        elif opcode == 22:  # LW (Load Word - rc = MEM[ra + imm16])
            addr = (a_val + (const_low & 0xFFFF))
            # Prepara o registrador de pipeline para a fase MEM
            self.EX_MEM = {
                "ir": self.ID_EX["ir"],
                "valid": True,
                "opcode": opcode,
                "rc": rc,
                "address": addr, # Endereço calculado
                "exec_rc": rc,
                "exec_result": None # Resultado da memória será preenchido em MEM
            }
            return
            
        elif opcode == 23:  # SW (Store Word - MEM[ra+imm16] = rb_value)
            addr = (a_val + (const_low & 0xFFFF))
            store_value = b_val
            # Prepara o registrador de pipeline para a fase MEM
            self.EX_MEM = {
                "ir": self.ID_EX["ir"],
                "valid": True,
                "opcode": opcode,
                "rc": rc,
                "address": addr, # Endereço calculado
                "store_value": store_value # Valor a ser armazenado
            }
            return

        # 5. Branches / Jumps
        elif opcode == 24:  # JAL (Jump and Link)
            ret = pc_of_inst + 1 # Endereço de retorno (PC+1 da instrução atual)
            exec_result = ret
            exec_rc = 31 # Destino é R31 (Link Register)
            jump_addr_val = self.ID_EX["jump_addr"]
            dest = jump_addr_val & 0xFFFFFF
            
            # Atualiza o PC para o salto (Controle)
            if 0 <= dest < MEMORY_SIZE_WORDS:
                self.pc = dest
            else:
                self.halted = True
        elif opcode == 25:  # JR (Jump Register)
            dest = a_val
            # Atualiza o PC para o salto (Controle)
            if 0 <= dest < MEMORY_SIZE_WORDS:
                self.pc = dest
            else:
                self.halted = True
        elif opcode == 26:  # BEQ (Branch on Equal)
            jump_addr_val = self.ID_EX["jump_addr"]
            if a_val == b_val:
                dest = jump_addr_val
                # Atualiza o PC para o salto (Controle)
                if 0 <= dest < MEMORY_SIZE_WORDS:
                    self.pc = dest
                else:
                    self.halted = True
        elif opcode == 27:  # BNE (Branch on Not Equal)
            jump_addr_val = self.ID_EX["jump_addr"]
            if a_val != b_val:
                dest = jump_addr_val
                # Atualiza o PC para o salto (Controle)
                if 0 <= dest < MEMORY_SIZE_WORDS:
                    self.pc = dest
                else:
                    self.halted = True
        elif opcode == 28:  # J (Jump incondicional)
            jump_addr_val = self.ID_EX["jump_addr"]
            dest = jump_addr_val
            # Atualiza o PC para o salto (Controle)
            if 0 <= dest < MEMORY_SIZE_WORDS:
                self.pc = dest
            else:
                self.halted = True

        # Padrão: Escrita no EX/MEM para todas as instruções que não sejam LW/SW
        # (ALU, CONST, JAL)
        self.EX_MEM = {
            "ir": self.ID_EX["ir"],
            "valid": True,
            "opcode": opcode,
            "exec_result": exec_result, # Resultado da ALU/CONST/PC+1
            "exec_rc": exec_rc # Registrador destino
        }

    # Estágio MEM (Memory Access)
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
            "exec_result": self.EX_MEM.get("exec_result") # Resultado de EX (para ALU/CONST/JAL)
        }

        if opcode == 22:  # LW (Leitura da Memória)
            addr = self.EX_MEM.get("address", 0)
            if not (0 <= addr < MEMORY_SIZE_WORDS):
                self.halted = True
                return
            value = self.memory[addr] & 0xFFFFFFFF
            # O resultado para o WB é o valor lido da memória
            memwb["exec_result"] = self.update_flags(value) 
            
        elif opcode == 23:  # SW (Escrita na Memória)
            addr = self.EX_MEM.get("address", 0)
            if not (0 <= addr < MEMORY_SIZE_WORDS):
                self.halted = True
                return
            self.memory[addr] = self.EX_MEM.get("store_value", 0) & 0xFFFFFFFF
            # SW não escreve em registradores (resultado é None)
            memwb["exec_result"] = None
        
        self.MEM_WB = memwb

    # Estágio WB (Write Back)
    def WB(self):
        if not self.MEM_WB.get("valid", False):
            return
        
        # Só escreve no registrador se o resultado de execução não for None
        if self.MEM_WB.get("exec_result") is not None:
            dest = self.MEM_WB.get("exec_rc") & 0x1F
            # R0 (índice 0) não pode ser escrito.
            if dest != 0:
                write_reg(self.registers, dest, self.MEM_WB.get("exec_result"))
                
        # Detecção final de HALT (caso a instrução HALT tenha passado pelo pipeline)
        ir = self.MEM_WB.get("ir")
        if ir == HALT_INSTRUCTION:
            self.halted = True

    # step: avança um ciclo de clock (WB -> MEM -> EX -> ID -> IF)
    def step(self):
        if self.halted:
            return
        self.cycle += 1
        # Avança os estágios em ordem reversa para simular o clock
        self.WB()
        self.MEM()
        self.EX()
        self.ID()
        self.IF()

    # utilidade: verifica se o pipeline ainda tem instruções válidas
    def any_pipeline_active(self):
        return (self.IF_ID.get("valid", False) or self.ID_EX.get("valid", False)
                or self.EX_MEM.get("valid", False) or self.MEM_WB.get("valid", False))