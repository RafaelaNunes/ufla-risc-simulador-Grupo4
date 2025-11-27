# src/simulador/cpu.py

# Supondo que 'decode_instruction' e 'bin_to_int' vêm de 'instruction.py'
from .instruction import decode_instruction, bin_to_int 

# ==============================================================================
# FUNÇÕES DE IMPRESSÃO (Mantidas para compatibilidade com run())
# ==============================================================================

# OBS: Se as suas funções originais de impressão estiverem em outro lugar, mantenha-as lá.
# Estas são apenas versões mock para que o cpu.py seja um arquivo independente.

def print_registers(reg_file):
    """Função básica para imprimir registradores."""
    print("-----------------------------------------")
    for i in range(16): # Assumindo 16 registradores
        print(f"R{i:02} (0x{i:X}): \t{reg_file.registers[i]:<10} (0x{reg_file.registers[i] & 0xFFFFFFFF:08X})")
    print("-----------------------------------------")

def print_memory_data(data_memory, limit_words=4):
    """Função básica para imprimir a memória de dados (limitada)."""
    print("-----------------------------------------")
    # Acessa diretamente a lista interna (word-aligned)
    for i in range(min(limit_words, len(data_memory.memory))):
        address = i * 4
        print(f"0x{address:04X}: \t{data_memory.memory[i]:<10} (0x{data_memory.memory[i] & 0xFFFFFFFF:08X})")
    print("-----------------------------------------")


# ==============================================================================
# CLASSES AUXILIARES (DataMemory, RegisterFile, PipelineRegister) - ADAPTADAS
# ==============================================================================

class DataMemory:
    """Simula a memória de dados (32 bits words, endereçamento byte)."""
    # Agora aceita uma lista de dados iniciais do loader
    def __init__(self, initial_data_list: list = None):
        self.memory = initial_data_list if initial_data_list is not None else [0] * 1024
        # self.size = len(self.memory) * 4 # Tamanho total em bytes
        
    def read_word(self, address: int) -> int:
        if address % 4 != 0 or address < 0: return 0 
        word_index = address // 4
        if word_index >= len(self.memory): return 0
        return self.memory[word_index]

    def write_word(self, address: int, data: int):
        if address % 4 != 0 or address < 0: return
        word_index = address // 4
        if word_index < len(self.memory):
            self.memory[word_index] = data

class RegisterFile:
    """Simula o arquivo de registradores (16 registradores de 32 bits)."""
    # Agora aceita uma lista de registradores iniciais do loader
    def __init__(self, initial_reg_list: list = None):
        self.registers = initial_reg_list if initial_reg_list is not None else [0] * 16
        # Garante que o tamanho seja o esperado (16 ou 32, dependendo da sua arquitetura. Usando 16 como padrão UFLA-RISC).
        if len(self.registers) < 16:
             self.registers.extend([0] * (16 - len(self.registers)))


    def read(self, index: int) -> int:
        if index < 0 or index >= len(self.registers): return 0
        if index == 0: return 0
        return self.registers[index]

    def write(self, index: int, value: int):
        if index <= 0 or index >= len(self.registers): return
        self.registers[index] = bin_to_int(format(value & 0xFFFFFFFF, '032b'))

class PipelineRegister:
    """Classe base para os latches de pipeline."""
    # (Código idêntico ao anterior)
    def __init__(self):
        self.reset()
    # ... (métodos reset e copy) ...
    def reset(self):
        self.data = {
            'PC': 0, 'PC_Next': 0, 'Instruction': '00000000000000000000000000000000',
            'Ctrl': [0] * 10, 'Rs_Val': 0, 'Rt_Val': 0, 'Immediate': 0,
            'Rd': 0, 'Rt': 0, 'Rs': 0, 'Mnemonic': 'NOP',
            'ALU_Result': 0, 'Mem_Data': 0, 'Write_Reg_Addr': 0,
        }

    def copy(self, source_latch: 'PipelineRegister'):
        self.data.update(source_latch.data)

# ==============================================================================
# UNIDADE LÓGICA ARITMÉTICA (ALU) - Preservada
# ==============================================================================

class ALU:
    
    R_TYPE_ALU_CODES = {
        'ADD': 0b0000, 'SUB': 0b0001, 'ZERO': 0b0010, 'XOR': 0b0011, 'OR': 0b0100, 
        'NOT': 0b0101, 'AND': 0b0110, 'SLA': 0b0111, 'SRA': 0b1000, 'SLL': 0b1001, 
        'SRL': 0b1010, 'COPY': 0b1011,
        'MUL': 0b1100, 'DIV': 0b1101, 'NOR': 0b1110, 'SLT': 0b1111,
    }

    @staticmethod
    def execute(operation_code: int, input_a: int, input_b: int) -> int:
        # ... (Lógica da ALU idêntica ao código anterior)
        result = 0
        if operation_code == ALU.R_TYPE_ALU_CODES['ADD']: result = input_a + input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['SUB']: result = input_a - input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['COPY']: result = input_a
        elif operation_code == ALU.R_TYPE_ALU_CODES['MUL']: result = input_a * input_b
        elif operation_code == ALU.R_TYPE_ALU_CODES['DIV']: 
            result = input_a // input_b if input_b != 0 else 0
        elif operation_code == ALU.R_TYPE_ALU_CODES['NOR']: result = ~(input_a | input_b)
        elif operation_code == ALU.R_TYPE_ALU_CODES['SLT']: 
            result = 1 if input_a < input_b else 0
        # ... (incluir outras operações lógicas e shift aqui se necessário)
        
        return bin_to_int(format(result & 0xFFFFFFFF, '032b'))

# ==============================================================================
# CLASSE PRINCIPAL DA CPU - CORRIGIDA
# ==============================================================================

class CPU:
    
    # Tabela de Controle (Preservada e Completa)
    # [RegDst, ALUSrc, MemToReg, RegWrite, MemRead, MemWrite, Branch, ALUOp1, ALUOp0, ALUCode]
    CONTROL_TABLE = {
        # R-Type
        '00000001': [1, 0, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['ADD']], 
        '00001100': [1, 0, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['COPY']], 
        '00010100': [1, 0, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['MUL']],  # MUL (20)
        '00010101': [1, 0, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['DIV']],  # DIV (21)
        '00011011': [1, 0, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['NOR']],  # NOR (27)

        # I-ARITH
        '00011000': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['ADD']], # ADDI (24)
        '00011001': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['SUB']], # SUBI (25)
        '00010110': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['MUL']],  # MULI (22)
        '00010111': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['AND']],  # ANDI (23)
        '00011100': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['SLT']],  # SLTI (28)
        
        # I-CONST/I-MEM
        '00001110': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['COPY']], # LUI (14)
        '00011010': [0, 1, 0, 1, 0, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['COPY']], # LLI (26)
        '00010000': [0, 1, 1, 1, 1, 0, 0, 0, 0, ALU.R_TYPE_ALU_CODES['ADD']],# LW (16)
        '00010001': [0, 1, 0, 0, 0, 1, 0, 0, 0, ALU.R_TYPE_ALU_CODES['ADD']], # SW (17)

        # Controle
        '11111111': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0b0000],# HALT
        '00000000': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0b0000] # NOP
    }
    
    # CONSTRUTOR CORRIGIDO PARA ACEITAR OS ARGUMENTOS DO main.py
    def __init__(self, instruction_mem_dict: dict, registers_list: list, data_memory_list: list):
        
        # 1. Inicializa Registradores e Memória de Dados com as listas passadas
        self.reg_file = RegisterFile(initial_reg_list=registers_list)
        self.data_memory = DataMemory(initial_data_list=data_memory_list)

        # 2. Converte o dicionário de instruções (PC -> binário) em uma lista indexada
        # Encontra o índice máximo para dimensionar a memória de instruções
        max_pc = max(instruction_mem_dict.keys()) if instruction_mem_dict else 0
        instruction_memory_size = (max_pc // 4) + 1
        self.instruction_memory = ['0' * 32] * instruction_memory_size
        
        for pc, instruction_bin in instruction_mem_dict.items():
            if pc % 4 == 0 and (pc // 4) < instruction_memory_size:
                 self.instruction_memory[pc // 4] = instruction_bin
        
        # 3. Inicialização do Pipeline e Controle
        self.PC = 0
        self.running = True 
        self.clock_cycle = 0

        # Alias para compatibilidade com as funções de impressão
        self.registers = self.reg_file 
        
        # Latches do Pipeline
        self.if_id_latch = PipelineRegister()
        self.id_ex_latch = PipelineRegister()
        self.ex_mem_latch = PipelineRegister() 
        self.mem_wb_latch = PipelineRegister()
        
    # O método load_program é removido ou esvaziado, pois os dados já foram carregados no __init__
    
    def fetch(self):
        """Estágio 1: Busca (Fetch) - Versão CORRIGIDA"""
        if not self.running:
            self.if_id_latch.reset()
            return
        
        instruction_index = self.PC // 4
        
        if instruction_index < len(self.instruction_memory):
            instruction_binary = self.instruction_memory[instruction_index]
            
            self.if_id_latch.data['Instruction'] = instruction_binary
            self.if_id_latch.data['PC'] = self.PC
            self.if_id_latch.data['PC_Next'] = self.PC + 4
            
            self.PC += 4
        else:
            # O PC está FORA dos limites, finaliza o programa
            self.if_id_latch.reset()
            self.running = False


    def decode(self, if_id_latch: dict) -> dict:
        """Estágio 2: Decodificação e Busca de Registradores (Decode/Read)"""
        # ... (código decode idêntico ao anterior)
        instruction = if_id_latch['Instruction']
       

        try:
            decoded = decode_instruction(instruction)
        except ValueError:
            # Se a instrução for inválida, trata como NOP
            self.id_ex_latch.reset()
            return self.id_ex_latch.data

        opcode_bin = decoded['Opcode']
        ctrl = self.CONTROL_TABLE.get(opcode_bin, [0]*10)
        
        if decoded['Mnemonic'] == 'HALT':
            self.running = False

        rs_val = self.reg_file.read(decoded.get('Rs', 0))
        rt_val = self.reg_file.read(decoded.get('Rt', 0))
        
        self.id_ex_latch.data.update({
            'PC_Next': if_id_latch['PC_Next'], 'Mnemonic': decoded['Mnemonic'],
            'Ctrl': ctrl, 'Rs_Val': rs_val, 'Rt_Val': rt_val,
            'Immediate': decoded.get('Immediate', 0), 
            'Rs': decoded.get('Rs', 0), 'Rt': decoded.get('Rt', 0), 
            'Rd': decoded.get('Rd', 0)
        })
        
        return self.id_ex_latch.data

    def execute_and_memory_access(self, id_ex_latch: dict) -> dict:
        """Estágio 3: Execução e Acesso à Memória (EX/MEM)"""
        # ... (código execute_and_memory_access idêntico ao anterior)
        ctrl = id_ex_latch['Ctrl']
        
       # if id_ex_latch['Mnemonic'] in ['HALT', 'NOP']:
        #    self.ex_mem_latch.reset()
         #   return self.ex_mem_latch.data

        write_reg_addr = id_ex_latch['Rd'] if ctrl[0] == 1 else id_ex_latch['Rt']
        alu_input_a = id_ex_latch['Rs_Val']
        alu_input_b = id_ex_latch['Immediate'] if ctrl[1] == 1 else id_ex_latch['Rt_Val']
        
        if id_ex_latch['Mnemonic'] == 'LUI':
            alu_result = id_ex_latch['Immediate'] << 16
        elif id_ex_latch['Mnemonic'] == 'LLI':
             alu_result = id_ex_latch['Immediate']
        else:
            alu_result = ALU.execute(ctrl[9], alu_input_a, alu_input_b)
        
        mem_data = 0
        if ctrl[4] == 1: # MemRead = 1 (LW)
            mem_data = self.data_memory.read_word(alu_result)
        elif ctrl[5] == 1: # MemWrite = 1 (SW)
            self.data_memory.write_word(alu_result, id_ex_latch['Rt_Val'])
            
        self.ex_mem_latch.data.update({
            'Ctrl': ctrl, 'ALU_Result': alu_result, 'Mem_Data': mem_data,
            'Write_Reg_Addr': write_reg_addr
        })
        
        return self.ex_mem_latch.data

    def write_back(self, ex_mem_latch: dict):
        """Estágio 4: Escrita de Volta (Write Back)"""
        # ... (código write_back idêntico ao anterior)
        ctrl = ex_mem_latch['Ctrl']
        
        if ctrl[3] == 1: 
            data_to_write = ex_mem_latch['Mem_Data'] if ctrl[2] == 1 else ex_mem_latch['ALU_Result']
            self.reg_file.write(ex_mem_latch['Write_Reg_Addr'], data_to_write)
        
        self.mem_wb_latch.copy(self.ex_mem_latch)


    def _print_pipeline_state(self):
        """Imprime o estado atual dos latches do pipeline."""
        
        if_id_mnem = decode_instruction(self.if_id_latch.data['Instruction']).get('Mnemonic', 'NOP')
        id_ex_mnem = self.id_ex_latch.data['Mnemonic']
        ex_mem_mnem = self.ex_mem_latch.data['Mnemonic']
        wb_mnem = self.mem_wb_latch.data['Mnemonic']

        print(f"| Instrução:  | {if_id_mnem:<8} | {id_ex_mnem:<8} | {ex_mem_mnem:<8} | {wb_mnem:<8} |")
        print("+" + "-"*56 + "+")
        
        
    # src/simulador/cpu.py (NOVO MÉTODO)
    def check_for_data_hazard(self):
        """
        Verifica se a instrução no ID precisa do resultado da instrução 
        que está atualmente no EX ou WB (apenas para stalls).
        """
        # Exemplo: Hazard entre ID (Lw/Sw/R-type) e EX (R-type/Lw)
        
        # 1. Obter registradores Rs/Rt da instrução em ID
        id_rs = self.if_id_latch.data.get('Rs', -1)
        id_rt = self.if_id_latch.data.get('Rt', -1)

        # 2. Obter endereço de escrita da instrução no EX
        ex_write_reg = self.ex_mem_latch.data.get('Write_Reg_Addr', -2)
        ex_reg_write = self.ex_mem_latch.data.get('Ctrl', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])[3]
        
        # 3. Condição de Stall CRÍTICA (RAW Hazard)
        # A instrução em ID precisa de um registrador que será escrito pela instrução em EX.
        if ex_reg_write and ex_write_reg > 0:
            if ex_write_reg == id_rs or ex_write_reg == id_rt:
                return True  # STALL NECESSÁRIO
        
        return False

    def step(self):
            """Executa um ciclo de clock completo do pipeline."""
            self.write_back(self.ex_mem_latch.data) 
            self.execute_and_memory_access(self.id_ex_latch.data)
            
            # --- NOVO BLOCO DE CONTROLE DE HAZARD ---
            stall_needed = self.check_for_data_hazard()
            
            if stall_needed:
                # Inserir NOP (Bubble) no ID/EX Latch (Stall)
                # O IF/ID (que contem a instrução perigosa) deve ser re-executado.
                self.id_ex_latch.reset()  # Insere NOP no próximo estágio
                self.PC -= 4              # Reverte o PC (Para buscar a mesma instrução novamente)
                # O fetch não será chamado para que a instrução ADDI permaneça no IF/ID
                # e o PC não avance.
                
            else:
                # Avanço normal
                self.decode(self.if_id_latch.data)
                self.fetch()
                
            self.clock_cycle += 1
            
        
    def run(self):
            """Roda a simulação (Preservado do seu código)."""
            
            print("\n--- INÍCIO DA EXECUÇÃO DO PIPELINE ---")
            print("| Estágio:     | IF       | ID       | EX/MEM   | WB       |")
            print("| Latch:       | IF/ID    | ID/EX    | EXMEM/WB | WB       |")
            print("+" + "-"*56 + "+")

            cycles_after_stop = 0
            
            # Limite de 100 ciclos para evitar loop
            while (self.running or cycles_after_stop < 4) and self.clock_cycle < 100: 
                
                if self.clock_cycle > 0:
                    # O PC que será impresso é o PC da instrução atual no IF
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
            # Passamos o objeto RegisterFile
            print_registers(self.reg_file) 
            print("\nMEMÓRIA DE DADOS FINAIS (Apenas os primeiros 16 bytes):")
            print_memory_data(self.data_memory, limit_words=4) # Limita a 4 words (16 bytes)