
from .instruction import decode_instruction, bin_to_int

# ----------------------- helpers de impressão -----------------------
def print_registers(reg_file):
    print("-----------------------------------------")
    # Ajustado para exibir 32 registradores (4 por linha para caber na tela)
    for i in range(0, 32, 4):
        line = ""
        for j in range(4):
            idx = i + j
            if idx < 32:
                val = reg_file.registers[idx]
                line += f"R{idx:02} (0x{idx:02X}): {val:<10} "
        print(line)
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
        # Simula endereçamento a byte alinhado (ignora 2 bits menos significativos)
        if address < 0: return 0
        idx = address // 4
        if idx >= len(self.memory): return 0
        return self.memory[idx]

    def write_word(self, address: int, data: int):
        if address < 0: return
        idx = address // 4
        if idx < len(self.memory):
            self.memory[idx] = data

class RegisterFile:
    def __init__(self, initial_reg_list: list = None):
        # CORREÇÃO: Inicializa 32 registradores (Requisito do PDF)
        self.registers = initial_reg_list if initial_reg_list is not None else [0] * 32
        if len(self.registers) < 32:
            self.registers.extend([0] * (32 - len(self.registers)))

    def read(self, index: int) -> int:
        if index <= 0 or index >= len(self.registers): return 0 # R0 é sempre 0
        return self.registers[index]

    def write(self, index: int, value: int):
        if index <= 0 or index >= len(self.registers): return # Protege R0
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
            'Flags': {'Z': 0, 'N': 0, 'C': 0, 'V': 0} # Novos flags
        }

    def copy(self, source: 'PipelineRegister'):
        self.data = source.data.copy() # Shallow copy do dict é suficiente aqui


# ----------------------- ALU -----------------------
class ALU:
    R_TYPE_ALU_CODES = {
        'ADD': 0b0000, 'SUB': 0b0001, 'ZERO': 0b0010, 'XOR': 0b0011, 'OR': 0b0100,
        'NOT': 0b0101, 'AND': 0b0110, 'SLA': 0b0111, 'SRA': 0b1000, 'SLL': 0b1001,
        'SRL': 0b1010, 'COPY': 0b1011, 'MUL': 0b1100, 'DIV': 0b1101, 'NOR': 0b1110, 'SLT': 0b1111
    }

    @staticmethod
    def execute(operation_code: int, input_a: int, input_b: int):
        """
        Retorna uma tupla: (resultado_inteiro, dicionario_flags)
        Flags: Zero (Z), Neg (N), Carry (C), Overflow (V)
        """
        res = 0
        # Simula aritmética de 32 bits assinada e não assinada para flags
        # Mas em Python, inteiros têm precisão arbitrária. Precisamos mascarar.
        
        # Operações
        if operation_code == ALU.R_TYPE_ALU_CODES['ADD']: res = input_a + input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['SUB']: res = input_a - input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['COPY']: res = input_a
        elif operation_code == ALU.R_TYPE_ALU_CODES['MUL']: res = input_a * input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['DIV']: res = int(input_a / input_b) if input_b != 0 else 0
        elif operation_code == ALU.R_TYPE_ALU_CODES['NOR']: res = ~(input_a | input_b)
        elif operation_code == ALU.R_TYPE_ALU_CODES['SLT']: res = 1 if input_a < input_b else 0
        elif operation_code == ALU.R_TYPE_ALU_CODES['AND']: res = input_a & input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['OR']: res = input_a | input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['XOR']: res = input_a ^ input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['NOT']: res = ~input_a
        elif operation_code == ALU.R_TYPE_ALU_CODES['SLL']: res = (input_a << (input_b & 0x1F))
        elif operation_code == ALU.R_TYPE_ALU_CODES['SRL']: res = ((input_a & 0xFFFFFFFF) >> (input_b & 0x1F))
        elif operation_code == ALU.R_TYPE_ALU_CODES['SRA']: res = (input_a >> (input_b & 0x1F)) # SRA em python precisa de cuidado com sinal, aqui simplificado
        
        # Truncar para 32 bits (com sinal) para o resultado final
        final_res = bin_to_int(format(res & 0xFFFFFFFF, '032b'))

        # --- Cálculo de Flags (Requisito PDF) ---
        flags = {'Z': 0, 'N': 0, 'C': 0, 'V': 0}
        
        # Zero Flag
        if final_res == 0: flags['Z'] = 1
        
        # Negative Flag
        if final_res < 0: flags['N'] = 1

        # Carry & Overflow (Simplificado para ADD/SUB)
        # Carry verifica se passou de 32 bits sem sinal
        if operation_code == ALU.R_TYPE_ALU_CODES['ADD']:
            unsigned_res = (input_a & 0xFFFFFFFF) + (input_b & 0xFFFFFFFF)
            if unsigned_res > 0xFFFFFFFF: flags['C'] = 1
            # Overflow (Signed): Pos+Pos=Neg ou Neg+Neg=Pos
            if (input_a > 0 and input_b > 0 and final_res < 0) or \
               (input_a < 0 and input_b < 0 and final_res > 0):
                flags['V'] = 1

        elif operation_code == ALU.R_TYPE_ALU_CODES['SUB']:
            # Subtração é Soma com complemento
            unsigned_res = (input_a & 0xFFFFFFFF) - (input_b & 0xFFFFFFFF)
            if unsigned_res < 0: flags['C'] = 1 # Borrow
            # Overflow: Pos-Neg=Neg ou Neg-Pos=Pos
            if (input_a > 0 and input_b < 0 and final_res < 0) or \
               (input_a < 0 and input_b > 0 and final_res > 0):
                flags['V'] = 1
        
        # Nas lógicas (AND, OR), zera V e C
        if operation_code in [ALU.R_TYPE_ALU_CODES['AND'], ALU.R_TYPE_ALU_CODES['OR'], ALU.R_TYPE_ALU_CODES['XOR']]:
            flags['C'] = 0
            flags['V'] = 0

        return final_res, flags


# ----------------------- CPU -----------------------
class CPU:
    CONTROL_TABLE = {
        # R-Type
        '00000001': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], 
        '00001100': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['COPY']], 
        '00010100': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['MUL']],
        '00010101': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['DIV']],
        '00011011': [1,0,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['NOR']],
        '00001101': [0,0,0,0,0,0,0,0,0, 0],  # JR
        '00010011': [0,0,0,0,0,0,0,0,0, 0],  # JR (Pelo instruction.py novo)

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
        '00001110': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['COPY']], # LUI
        '00001111': [0,1,0,1,0,0,0,0,0, ALU.R_TYPE_ALU_CODES['COPY']], # LLI
        '00010000': [0,1,1,1,1,0,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], # LW
        '00010001': [0,1,0,0,0,1,0,0,0, ALU.R_TYPE_ALU_CODES['ADD']], # SW

        # Control-flow opcodes (JEQ,JNE,J,JAL)
        '00010100': [0,0,0,0,0,0,1,0,0,0],  # BEQ (Branch)
        '00010101': [0,0,0,0,0,0,1,0,0,0],  # BNE
        '00010110': [0,0,0,0,0,0,0,0,0,0],  # J
        '00010010': [0,0,0,1,0,0,0,0,0,0],  # JAL -> RegWrite set (link in R31)

        # HALT / NOP
        '11111111': [0,0,0,0,0,0,0,0,0,0],
        '00000000': [0,0,0,0,0,0,0,0,0,0]
    }

    def __init__(self, instruction_mem_dict: dict, registers_list: list, data_memory_list: list):
        self.reg_file = RegisterFile(initial_reg_list=registers_list)
        self.data_memory = DataMemory(initial_data_list=data_memory_list)

        max_pc = max(instruction_mem_dict.keys()) if instruction_mem_dict else 0
        instr_mem_size = (max_pc // 4) + 1
        self.instruction_memory = ['0' * 32] * (instr_mem_size + 100) # Buffer extra
        for pc, instr in instruction_mem_dict.items():
            idx = pc // 4
            if idx < len(self.instruction_memory):
                self.instruction_memory[idx] = instr

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
            self.if_id_latch.data['Instruction'] = ins
            self.if_id_latch.data['PC'] = self.PC
            self.if_id_latch.data['PC_Next'] = self.PC + 4
            self.PC += 4
        else:
            self.if_id_latch.reset()
            self.running = False

    # ID stage
    def decode(self, if_id_latch: dict):
        instr_bin = if_id_latch.get('Instruction', '0'*32)
        try:
            # Chama a função corrigida do instruction.py
            decoded = decode_instruction(instr_bin)
        except Exception:
            self.id_ex_latch.reset()
            return self.id_ex_latch.data

        opcode_bin = decoded['Opcode']
        # Tenta pegar controle ou retorna NOP se falhar
        ctrl = self.CONTROL_TABLE.get(opcode_bin, [0]*10)
        
        if decoded.get('Mnemonic') == 'HALT':
            self.running = False

        # Leitura dos registradores
        rs_idx = decoded.get('Rs', 0)
        rt_idx = decoded.get('Rt', 0)
        
        rs_val = self.reg_file.read(rs_idx)
        rt_val = self.reg_file.read(rt_idx)

        self.id_ex_latch.data.update({
            'PC_Next': if_id_latch.get('PC_Next', 0),
            'Mnemonic': decoded.get('Mnemonic'),
            'Ctrl': ctrl,
            'Rs_Val': rs_val,
            'Rt_Val': rt_val,
            'Immediate': decoded.get('Immediate', 0),
            'Rs': rs_idx,
            'Rt': rt_idx,
            'Rd': decoded.get('Rd', 0),
        })
        return self.id_ex_latch.data

    # EX/MEM stage
    def execute_and_memory_access(self, id_ex_latch: dict) -> dict:
        if not id_ex_latch or id_ex_latch.get('Mnemonic') in (None, 'NOP'):
            return {
                'Ctrl': [0]*10, 'ALU_Result': 0, 'Mem_Data': 0,
                'Write_Reg_Addr': 0, 'Mnemonic': 'NOP', 'JumpTaken': False,
                'Flags': {'Z':0,'N':0,'C':0,'V':0}
            }

        ctrl = id_ex_latch.get('Ctrl', [0]*10)
        mnemonic = id_ex_latch.get('Mnemonic', 'NOP')

        # Destino de escrita (Rd para R-Type, Rt para I-Type)
        write_reg_addr = id_ex_latch.get('Rd') if ctrl[0] == 1 else id_ex_latch.get('Rt')

        # Forwarding Logic
        rs = id_ex_latch.get('Rs', 0)
        rt = id_ex_latch.get('Rt', 0)
        alu_a = id_ex_latch.get('Rs_Val', 0)
        alu_b = id_ex_latch.get('Rt_Val', 0)

        # Forwarding MEM/WB
        wb_wr = self.mem_wb_latch.data.get('Write_Reg_Addr', 0)
        wb_reg_write = self.mem_wb_latch.data.get('Ctrl', [0]*10)[3]
        if wb_reg_write and wb_wr != 0:
            data_wb = self.mem_wb_latch.data['Mem_Data'] if self.mem_wb_latch.data['Ctrl'][2] == 1 else self.mem_wb_latch.data['ALU_Result']
            if rs == wb_wr: alu_a = data_wb
            if rt == wb_wr and ctrl[1] == 0: alu_b = data_wb # Se ALUOp b não for imediato

        # Forwarding EX/MEM
        ex_wr = self.ex_mem_latch.data.get('Write_Reg_Addr', 0)
        ex_reg_write = self.ex_mem_latch.data.get('Ctrl', [0]*10)[3]
        if ex_reg_write and ex_wr != 0:
            data_ex = self.ex_mem_latch.data.get('ALU_Result', 0)
            if rs == ex_wr: alu_a = data_ex
            if rt == ex_wr and ctrl[1] == 0: alu_b = data_ex

        # ALUSrc (Imediato)
        val_op_b = alu_b
        if ctrl[1] == 1:
            val_op_b = id_ex_latch.get('Immediate', 0)

        # Execução ALU
        alu_flags = {'Z':0, 'N':0, 'C':0, 'V':0}
        
        if mnemonic == 'LUI':
            alu_result = (id_ex_latch.get('Immediate', 0) << 16) & 0xFFFFFFFF
        elif mnemonic == 'LLI':
            # LLI carrega nos bits baixos. Mantém os altos? O PDF diz "carrega constante".
            # Assume-se replace ou OR. Aqui replace simples do byte baixo.
            alu_result = id_ex_latch.get('Immediate', 0) & 0xFFFF
        else:
            # Chama ALU nova com Flags
            alu_result, alu_flags = ALU.execute(ctrl[9], alu_a, val_op_b)

        # Acesso à Memória
        mem_data = 0
        if ctrl[4] == 1:  # LW
            mem_data = self.data_memory.read_word(alu_result)
        elif ctrl[5] == 1:  # SW
            # Dado a escrever é Rt (alu_b original antes do mux imediato)
            # Mas precisa aplicar forwarding no dado de store se necessário
            store_val = alu_b
            if wb_reg_write and wb_wr == rt: 
                 store_val = self.mem_wb_latch.data['Mem_Data'] if self.mem_wb_latch.data['Ctrl'][2] == 1 else self.mem_wb_latch.data['ALU_Result']
            if ex_reg_write and ex_wr == rt:
                 store_val = self.ex_mem_latch.data.get('ALU_Result', 0)
            self.data_memory.write_word(alu_result, store_val)

        # Controle de Fluxo
        jump_taken = False
        next_pc = None
        
        if mnemonic == 'BEQ':
            if alu_a == alu_b:
                jump_taken = True
                next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'BNE':
            if alu_a != alu_b:
                jump_taken = True
                next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'J':
            jump_taken = True
            next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'JAL':
            link_value = id_ex_latch.get('PC_Next', 0)
            # CORREÇÃO: Salva em R31 (Requisito PDF)
            write_reg_addr = 31 
            alu_result = link_value
            jump_taken = True
            next_pc = id_ex_latch.get('Immediate', 0)
        elif mnemonic == 'JR':
            jump_taken = True
            next_pc = alu_a # Endereço está no registrador

        return {
            'Ctrl': ctrl,
            'ALU_Result': alu_result,
            'Mem_Data': mem_data,
            'Write_Reg_Addr': write_reg_addr,
            'Mnemonic': mnemonic,
            'JumpTaken': jump_taken,
            'NextPC': next_pc,
            'Flags': alu_flags
        }

    # WB stage
    def write_back(self, mem_wb_latch: dict):
        if not mem_wb_latch: return
        ctrl = mem_wb_latch.get('Ctrl', [0]*10)
        if ctrl[3] == 1:
            data_to_write = mem_wb_latch.get('Mem_Data') if ctrl[2] == 1 else mem_wb_latch.get('ALU_Result')
            self.reg_file.write(mem_wb_latch.get('Write_Reg_Addr', 0), data_to_write)

    def _print_pipeline_state(self):
        try:
            if_id_mnem = decode_instruction(self.if_id_latch.data['Instruction']).get('Mnemonic', 'NOP')
        except: if_id_mnem = 'NOP'
        id_ex_mnem = self.id_ex_latch.data.get('Mnemonic', 'NOP')
        ex_mem_mnem = self.ex_mem_latch.data.get('Mnemonic', 'NOP')
        wb_mnem = self.mem_wb_latch.data.get('Mnemonic', 'NOP')
        
        # Opcional: Mostrar Flags do estágio EX
        flags = self.ex_mem_latch.data.get('Flags', {})
        f_str = f"Z={flags.get('Z')} N={flags.get('N')}"
        
        print(f"| Instrução:   | {if_id_mnem:<8} | {id_ex_mnem:<8} | {ex_mem_mnem:<8} | {wb_mnem:<8} |")
        print(f"| Flags (EX):  | {'':<8} | {'':<8} | {f_str:<8} | {'':<8} |")
        print("+" + "-"*56 + "+")

    def check_for_data_hazard(self) -> bool:
        try:
            decoded_if = decode_instruction(self.if_id_latch.data.get('Instruction', '0'*32))
        except: return False
        
        id_rs = decoded_if.get('Rs', 0)
        id_rt = decoded_if.get('Rt', 0)
        
        ex_ctrl = self.id_ex_latch.data.get('Ctrl', [0]*10)
        ex_write_reg = self.id_ex_latch.data.get('Rd') if ex_ctrl[0] == 1 else self.id_ex_latch.data.get('Rt')
        ex_mem_read = ex_ctrl[4] # LW
        
        # Load-Use Hazard
        if ex_mem_read and ex_write_reg != 0:
            if ex_write_reg == id_rs or ex_write_reg == id_rt:
                return True
        return False

    def step(self):
        # 1. WB
        self.write_back(self.mem_wb_latch.data)

        # 2. EX (Calcula next state)
        ex_result = self.execute_and_memory_access(self.id_ex_latch.data)
        next_ex_mem = PipelineRegister()
        next_ex_mem.data.update(ex_result)

        # 3. Hazard Detection
        stall = self.check_for_data_hazard()

        next_if_id = PipelineRegister()
        next_id_ex = PipelineRegister()

        if stall:
            # Stall: Zera controle para EX, mantém IF e ID
            next_id_ex.reset() # Bubble
            next_if_id.data.update(self.if_id_latch.data) # Hold IF/ID
        else:
            # 4. ID
            id_out = self.decode(self.if_id_latch.data)
            next_id_ex.data.update(id_out)
            # 5. IF
            self.fetch()
            next_if_id.data.update(self.if_id_latch.data)

        # 6. Branch Handling
        if ex_result.get('JumpTaken', False):
            next_pc = ex_result.get('NextPC')
            if next_pc is not None:
                self.PC = next_pc
            # Flush pipeline (descarta instruções buscadas erroneamente)
            next_if_id.reset()
            next_id_ex.reset()

        # 7. Update Latches
        next_mem_wb = PipelineRegister()
        next_mem_wb.data.update(next_ex_mem.data)
        
        if not stall: # Se houve stall, fetch não rodou, PC não muda (já tratado acima)
             pass

        self.if_id_latch.data.update(next_if_id.data)
        self.id_ex_latch.data.update(next_id_ex.data)
        self.ex_mem_latch.data.update(next_ex_mem.data)
        self.mem_wb_latch.data.update(next_mem_wb.data)

        self.clock_cycle += 1

    def run(self):
        print("\n--- INÍCIO DA EXECUÇÃO DO PIPELINE ---")
        print("| Estágio:     | IF       | ID       | EX/MEM   | WB       |")
        print("+" + "-"*56 + "+")

        self.fetch()

        cycles_after_stop = 0
        while (self.running or cycles_after_stop < 4) and self.clock_cycle < 1000:
            if self.clock_cycle > 0:
                pc_show = self.if_id_latch.data.get('PC', self.PC)
                print(f"Ciclo {self.clock_cycle:03} (PC=0x{pc_show:04X}):")
                self._print_pipeline_state()
            
            self.step()
            
            if not self.running:
                cycles_after_stop += 1

        print("\n--- FIM DA SIMULAÇÃO ---")
        print(f"Total de Ciclos: {self.clock_cycle}")
        print("\nREGISTRADORES FINAIS:")
        print_registers(self.reg_file)
        print("\nMEMÓRIA DE DADOS (Primeiros 16 bytes):")
        print_memory_data(self.data_memory, limit_words=4)