# src/simulador/cpu.py

from .instruction import decode_instruction, bin_to_int

# ----------------------- helpers de impressão -----------------------
def print_registers(reg_file):
    print("-----------------------------------------")
    for i in range(16):
        print(f"R{i:02} (0x{i:X}): \t{reg_file.registers[i]:<10} (0x{reg_file.registers[i] & 0xFFFFFFFF:08X})")
    print("-----------------------------------------")

def print_memory_data(data_memory, limit_words=4):
    print("-----------------------------------------")
    for i in range(min(limit_words, len(data_memory.memory))):
        address = i * 4
        print(f"0x{address:04X}: \t{data_memory.memory[i]:<10} (0x{data_memory.memory[i] & 0xFFFFFFFF:08X})")
    print("-----------------------------------------")


# ----------------------- estruturas -----------------------
class DataMemory:
    def __init__(self, initial_data_list: list = None):
        self.memory = initial_data_list if initial_data_list is not None else [0] * 1024

    def read_word(self, address: int) -> int:
        if address % 4 != 0 or address < 0: return 0
        idx = address // 4
        if idx >= len(self.memory): return 0
        return self.memory[idx]

    def write_word(self, address: int, data: int):
        if address % 4 != 0 or address < 0: return
        idx = address // 4
        if idx < len(self.memory):
            self.memory[idx] = data

class RegisterFile:
    def __init__(self, initial_reg_list: list = None):
        self.registers = initial_reg_list if initial_reg_list is not None else [0] * 16
        if len(self.registers) < 16:
            self.registers.extend([0] * (16 - len(self.registers)))

    def read(self, index: int) -> int:
        if index < 0 or index >= len(self.registers): return 0
        if index == 0: return 0
        return self.registers[index]

    def write(self, index: int, value: int):
        if index <= 0 or index >= len(self.registers): return
        self.registers[index] = value

class PipelineRegister:
    def __init__(self):
        self.reset()

    def reset(self):
        self.data = {
            'PC': 0, 'PC_Next': 0, 'Instruction': '0' * 32,
            'Ctrl': [0] * 10, 'Rs_Val': 0, 'Rt_Val': 0, 'Immediate': 0,
            'Rd': 0, 'Rt': 0, 'Rs': 0, 'Mnemonic': 'NOP',
            'ALU_Result': 0, 'Mem_Data': 0, 'Write_Reg_Addr': 0,
        }

    def copy(self, source: 'PipelineRegister'):
        self.data.update(source.data)


# ----------------------- ALU -----------------------
class ALU:
    R_TYPE_ALU_CODES = {
        'ADD': 0b0000, 'SUB': 0b0001, 'ZERO': 0b0010, 'XOR': 0b0011, 'OR': 0b0100,
        'NOT': 0b0101, 'AND': 0b0110, 'SLA': 0b0111, 'SRA': 0b1000, 'SLL': 0b1001,
        'SRL': 0b1010, 'COPY': 0b1011, 'MUL': 0b1100, 'DIV': 0b1101, 'NOR': 0b1110, 'SLT': 0b1111
    }

    @staticmethod
    def execute(operation_code: int, input_a: int, input_b: int) -> int:
        res = 0
        if operation_code == ALU.R_TYPE_ALU_CODES['ADD']: res = input_a + input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['SUB']: res = input_a - input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['COPY']: res = input_a
        elif operation_code == ALU.R_TYPE_ALU_CODES['MUL']: res = input_a * input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['DIV']: res = input_a // input_b if input_b != 0 else 0
        elif operation_code == ALU.R_TYPE_ALU_CODES['NOR']: res = ~(input_a | input_b)
        elif operation_code == ALU.R_TYPE_ALU_CODES['SLT']: res = 1 if input_a < input_b else 0
        elif operation_code == ALU.R_TYPE_ALU_CODES['AND']: res = input_a & input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['OR']: res = input_a | input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['XOR']: res = input_a ^ input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['NOT']: res = ~input_a
        elif operation_code == ALU.R_TYPE_ALU_CODES['SLL']: res = (input_a << (input_b & 0x1F))
        elif operation_code == ALU.R_TYPE_ALU_CODES['SRL']: res = ((input_a & 0xFFFFFFFF) >> (input_b & 0x1F))
        elif operation_code == ALU.R_TYPE_ALU_CODES['SRA']: res = (input_a >> (input_b & 0x1F))
        return bin_to_int(format(res & 0xFFFFFFFF, '032b'))


# ----------------------- CPU -----------------------
class CPU:
    CONTROL_TABLE = {
        # R-Type
        '00000001': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], 
        '00001100': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['COPY']], 
        '00010100': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['MUL']],
        '00010101': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['DIV']],
        '00011011': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['NOR']],
        '00001101': [0,0,0,0,0,0,0,0,0, 0],  # JR - handled specially

        # I-ARITH
        '00011000': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], # ADDI
        '00011001': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['SUB']], # SUBI
        '00010110': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['MUL']], # MULI
        '00010111': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['AND']], # ANDI
        '00011100': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['SLT']], # SLTI

        '00000100': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['XOR']],
        '00000101': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['OR']],
        '00000111': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['AND']],

        # I-CONST / I-MEM
        '00001110': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['COPY']],
        '00011010': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['COPY']],
        '00010000': [0,1,1,1,1,0,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], # LW
        '00010001': [0,1,0,0,0,1,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], # SW

        # Control-flow opcodes (JEQ,JNE,J,JAL)
        '00011101': [0,0,0,0,0,0,1,0,0,0],  # JEQ (Branch)
        '00011110': [0,0,0,0,0,0,1,0,0,0],  # JNE
        '00011111': [0,0,0,0,0,0,0,0,0,0],  # J (handled specially)
        '00100000': [0,0,0,1,0,0,0,0,0,0],  # JAL -> RegWrite set (link in R15)

        # HALT / NOP
        '11111111': [0,0,0,0,0,0,0,0,0,0],
        '00000000': [0,0,0,0,0,0,0,0,0,0]
    }

    def __init__(self, instruction_mem_dict: dict, registers_list: list, data_memory_list: list):
        self.reg_file = RegisterFile(initial_reg_list=registers_list)
        self.data_memory = DataMemory(initial_data_list=data_memory_list)

        max_pc = max(instruction_mem_dict.keys()) if instruction_mem_dict else 0
        instr_mem_size = (max_pc // 4) + 1
        self.instruction_memory = ['0' * 32] * instr_mem_size
        for pc, instr in instruction_mem_dict.items():
            if pc % 4 == 0 and (pc // 4) < instr_mem_size:
                self.instruction_memory[pc // 4] = instr

        self.PC = 0
        self.running = True
        self.clock_cycle = 0

        self.registers = self.reg_file

        self.if_id_latch = PipelineRegister()
        self.id_ex_latch = PipelineRegister()
        self.ex_mem_latch = PipelineRegister()
        self.mem_wb_latch = PipelineRegister()

    # IF stage
    def fetch(self):
        if not self.running:
            self.if_id_latch.reset()
            return
        idx = self.PC // 4
        if idx < len(self.instruction_memory):
            ins = self.instruction_memory[idx]
            # store the fetched instruction into IF/ID (these are tentative; step() will commit them)
            self.if_id_latch.data['Instruction'] = ins
            self.if_id_latch.data['PC'] = self.PC
            self.if_id_latch.data['PC_Next'] = self.PC + 4
            # advance PC for future fetches (may be overridden if branch taken)
            self.PC += 4
        else:
            self.if_id_latch.reset()
            self.running = False

    # ID stage
    def decode(self, if_id_latch: dict):
        instr_bin = if_id_latch.get('Instruction', '0'*32)
        try:
            decoded = decode_instruction(instr_bin)
        except Exception:
            self.id_ex_latch.reset()
            return self.id_ex_latch.data

        opcode_bin = decoded['Opcode']
        ctrl = self.CONTROL_TABLE.get(opcode_bin, [0]*10)
        if decoded.get('Mnemonic') == 'HALT':
            self.running = False

        rs_val = self.reg_file.read(decoded.get('Rs', 0))
        rt_val = self.reg_file.read(decoded.get('Rt', 0))

        # Save PC_Next so EX can use it for JAL link value
        self.id_ex_latch.data.update({
            'PC_Next': if_id_latch.get('PC_Next', 0),
            'Mnemonic': decoded.get('Mnemonic'),
            'Ctrl': ctrl,
            'Rs_Val': rs_val,
            'Rt_Val': rt_val,
            'Immediate': decoded.get('Immediate', 0),
            'Rs': decoded.get('Rs', 0),
            'Rt': decoded.get('Rt', 0),
            'Rd': decoded.get('Rd', 0),
        })
        return self.id_ex_latch.data

    # EX/MEM stage implemented as pure function returning a dict
    def execute_and_memory_access(self, id_ex_latch: dict) -> dict:
        if not id_ex_latch or id_ex_latch.get('Mnemonic') in (None, 'NOP'):
            return {
                'Ctrl': [0]*10, 'ALU_Result': 0, 'Mem_Data': 0,
                'Write_Reg_Addr': 0, 'Mnemonic': 'NOP', 'JumpTaken': False, 'NextPC': None
            }

        ctrl = id_ex_latch.get('Ctrl', [0]*10)
        mnemonic = id_ex_latch.get('Mnemonic', 'NOP')

        # decide write register (normal)
        write_reg_addr = id_ex_latch.get('Rd') if ctrl[0] == 1 else id_ex_latch.get('Rt')

        # prepare ALU inputs with forwarding from mem_wb and ex_mem (read-only)
        rs = id_ex_latch.get('Rs', 0)
        rt = id_ex_latch.get('Rt', 0)
        alu_a = id_ex_latch.get('Rs_Val', 0)
        alu_b = id_ex_latch.get('Rt_Val', 0)

        # forwarding from MEM/WB
        wb_wr = self.mem_wb_latch.data.get('Write_Reg_Addr', 0)
        wb_reg_write = self.mem_wb_latch.data.get('Ctrl', [0]*10)[3]
        if wb_reg_write and wb_wr != 0:
            data_wb = self.mem_wb_latch.data['Mem_Data'] if self.mem_wb_latch.data['Ctrl'][2] == 1 else self.mem_wb_latch.data['ALU_Result']
            if rs == wb_wr:
                alu_a = data_wb
            if rt == wb_wr and ctrl[1] == 0:
                alu_b = data_wb

        # forwarding from EX/MEM (previous cycle)
        ex_wr = self.ex_mem_latch.data.get('Write_Reg_Addr', 0)
        ex_reg_write = self.ex_mem_latch.data.get('Ctrl', [0]*10)[3]
        if ex_reg_write and ex_wr != 0:
            data_ex = self.ex_mem_latch.data.get('ALU_Result', 0)
            if rs == ex_wr:
                alu_a = data_ex
            if rt == ex_wr and ctrl[1] == 0:
                alu_b = data_ex

        # ALUSrc immediato
        if ctrl[1] == 1:
            alu_b = id_ex_latch.get('Immediate', 0)

        # treat LUI/LLI specially
        if mnemonic == 'LUI':
            alu_result = (id_ex_latch.get('Immediate', 0) << 16) & 0xFFFFFFFF
        elif mnemonic == 'LLI':
            alu_result = id_ex_latch.get('Immediate', 0) & 0xFFFFFFFF
        else:
            alu_result = ALU.execute(ctrl[9], alu_a, alu_b)

        mem_data = 0
        if ctrl[4] == 1:  # LW
            mem_data = self.data_memory.read_word(alu_result)
        elif ctrl[5] == 1:  # SW
            self.data_memory.write_word(alu_result, id_ex_latch.get('Rt_Val', 0))

        # Control-flow handling: JEQ, JNE, J, JAL, JR
        jump_taken = False
        next_pc = None

        if mnemonic == 'JEQ':
            if alu_a == alu_b:
                jump_taken = True
                next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'JNE':
            if alu_a != alu_b:
                jump_taken = True
                next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'J':
            jump_taken = True
            next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'JAL':
            # link_value must be PC_word + 1 -> id_ex_latch.PC_Next // 4
            link_value = (id_ex_latch.get('PC_Next', 0) // 4)
            write_reg_addr = 15  # last register (R15)
            alu_result = link_value
            jump_taken = True
            next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'JR':
            # JR -> use Rs value (alu_a) as the target absolute address
            jump_taken = True
            next_pc = alu_a

        result = {
            'Ctrl': ctrl,
            'ALU_Result': alu_result,
            'Mem_Data': mem_data,
            'Write_Reg_Addr': write_reg_addr,
            'Mnemonic': mnemonic,
            'JumpTaken': jump_taken,
            'NextPC': next_pc
        }
        return result

    # WB stage (only uses mem_wb_latch content)
    def write_back(self, mem_wb_latch: dict):
        if not mem_wb_latch:
            return
        ctrl = mem_wb_latch.get('Ctrl', [0]*10)
        if ctrl[3] == 1:
            data_to_write = mem_wb_latch.get('Mem_Data') if ctrl[2] == 1 else mem_wb_latch.get('ALU_Result')
            self.reg_file.write(mem_wb_latch.get('Write_Reg_Addr', 0), data_to_write)

    def _print_pipeline_state(self):
        try:
            if_id_mnem = decode_instruction(self.if_id_latch.data['Instruction']).get('Mnemonic', 'NOP')
        except Exception:
            if_id_mnem = 'NOP'
        id_ex_mnem = self.id_ex_latch.data.get('Mnemonic', 'NOP')
        ex_mem_mnem = self.ex_mem_latch.data.get('Mnemonic', 'NOP')
        wb_mnem = self.mem_wb_latch.data.get('Mnemonic', 'NOP')
        print(f"| Instrução:  | {if_id_mnem:<8} | {id_ex_mnem:<8} | {ex_mem_mnem:<8} | {wb_mnem:<8} |")
        print("+" + "-"*56 + "+")

    def check_for_data_hazard(self) -> bool:
        # Detect EX (load) -> ID use hazard
        try:
            decoded_if = decode_instruction(self.if_id_latch.data.get('Instruction', '0'*32))
        except Exception:
            return False
        id_rs = decoded_if.get('Rs', -1)
        id_rt = decoded_if.get('Rt', -1)
        ex_ctrl = self.id_ex_latch.data.get('Ctrl', [0]*10)
        ex_write_reg = self.id_ex_latch.data.get('Rd') if ex_ctrl[0] == 1 else self.id_ex_latch.data.get('Rt')
        ex_reg_write = ex_ctrl[3]
        ex_mem_read = ex_ctrl[4]  # LW
        if ex_mem_read and ex_write_reg > 0:
            if ex_write_reg == id_rs or ex_write_reg == id_rt:
                return True
        return False

    def step(self):
        # Prepare next latch containers
        next_if_id = PipelineRegister()
        next_id_ex = PipelineRegister()
        next_ex_mem = PipelineRegister()
        next_mem_wb = PipelineRegister()

        # 1) WRITE BACK uses current mem_wb_latch
        self.write_back(self.mem_wb_latch.data)

        # 2) EX compute (from current id_ex_latch) - produces the new EX/MEM contents
        ex_result = self.execute_and_memory_access(self.id_ex_latch.data)
        next_ex_mem.data.update(ex_result)

        # 3) MEM/WB for next cycle should receive the CURRENT ex_mem (not next_ex_mem).
        #    This guarantees EX and WB are different instructions in the same cycle.
        next_mem_wb.data.update(self.ex_mem_latch.data)

        # 4) detect hazard (based on the id_ex_latch before any update)
        stall = self.check_for_data_hazard()

        # 5) ID and IF behavior (if stall -> bubble; if not -> decode+fetch)
        if stall:
            # Insert bubble into ID/EX (NOP) and hold IF/ID (do not fetch new instruction)
            next_id_ex.reset()
            # keep the same IF/ID contents (stall IF stage)
            next_if_id.data.update(self.if_id_latch.data)
            # Important: do NOT call fetch() when stalling here
        else:
            # Normal: decode current IF/ID into next ID/EX
            id_out = self.decode(self.if_id_latch.data)
            next_id_ex.data.update(id_out)
            # Fetch new instruction into IF/ID (tentative)
            # NOTE: fetch() writes directly into self.if_id_latch (we'll copy its content to next_if_id)
            #       We advance PC here; if branch_taken below we'll override PC and flush next_if_id/next_id_ex
            self.fetch()
            next_if_id.data.update(self.if_id_latch.data)

        # 6) BRANCH/JUMP handling: if EX decided a jump, apply branch actions (flush & set PC)
        jump_taken = ex_result.get('JumpTaken', False)
        if jump_taken:
            next_pc = ex_result.get('NextPC')
            if next_pc is not None:
                # set PC for next fetch (absolute byte address)
                self.PC = next_pc
            # flush IF and ID (instructions fetched/speculated after branch)
            next_if_id.reset()
            next_id_ex.reset()

        # 7) Commit the new EX/MEM and MEM/WB latches
        self.ex_mem_latch.data.update(next_ex_mem.data)
        self.mem_wb_latch.data.update(next_mem_wb.data)

        # 8) Commit IF/ID and ID/EX (these may have been reset or updated)
        self.if_id_latch.data.update(next_if_id.data)
        self.id_ex_latch.data.update(next_id_ex.data)

        # advance clock
        self.clock_cycle += 1

    def run(self):
        print("\n--- INÍCIO DA EXECUÇÃO DO PIPELINE ---")
        print("| Estágio:     | IF       | ID       | EX/MEM   | WB       |")
        print("| Latch:       | IF/ID    | ID/EX    | EXMEM/WB | WB       |")
        print("+" + "-"*56 + "+")

        # initial fetch
        self.fetch()

        cycles_after_stop = 0
        while (self.running or cycles_after_stop < 4) and self.clock_cycle < 1000:
            if self.clock_cycle > 0:
                pc_current_if = self.if_id_latch.data.get('PC', self.PC)
                print(f"Ciclo {self.clock_cycle:03} (PC=0x{pc_current_if:04X}):")
                self._print_pipeline_state()
            self.step()
            if not self.running:
                cycles_after_stop += 1

        final_cycle = self.clock_cycle - 1
        print("\n--- FIM DA SIMULAÇÃO ---")
        print(f"Total de Ciclos: {final_cycle}")
        print("\nREGISTRADORES FINAIS:")
        print_registers(self.reg_file)
        print("\nMEMÓRIA DE DADOS FINAIS (Apenas os primeiros 16 bytes):")
        print_memory_data(self.data_memory, limit_words=4)
