# cpu.py

# Imports
from src.simulador.registers import read_reg, write_reg, print_registers
from src.simulador.memory import read_mem, write_mem, print_memory_data
from src.simulador.instruction import decode_instruction, OPCODE_MAP 

# --- UNIDADE DE CONTROLE E ULA (ALU) ---

class ALU:
    """Implementa as funções da Unidade Lógica Aritmética (ULA)."""
    
    R_TYPE_ALU_CODES = {
        'ADD': 0b0000, 'SUB': 0b0001, 'ZERO': 0b0010, 'XOR': 0b0011, 'OR': 0b0100, 
        'NOT': 0b0101, 'AND': 0b0110, 'SLA': 0b0111, 'SRA': 0b1000, 'SLL': 0b1001, 
        'SRL': 0b1010, 'COPY': 0b1011
    }

    @staticmethod
    def execute(operation_code: int, input_a, input_b) -> int:
        """Executa a operação da ULA, com segurança contra NoneType."""
        
        # Correção de segurança: Garante que os inputs são inteiros (0 se for None)
        input_a = int(input_a) if input_a is not None else 0
        input_b = int(input_b) if input_b is not None else 0
        
        result = 0
        
        if operation_code == 0b0000: # ADD
            result = input_a + input_b
        elif operation_code == 0b0001: # SUB
            result = input_a - input_b
        elif operation_code == 0b0110: # AND
            result = input_a & input_b
        # ... (Outras operações da ULA)
        else:
            result = 0 

        # Garante que o resultado é tratado como um inteiro de 32 bits
        return result & 0xFFFFFFFF


class CPU:
    """Simulador da CPU UFLA-RISC com Pipeline de 4 estágios (EX e MEM fundidos)."""

    # [RegDst, ALUSrc, MemToReg, RegWrite, MemRead, MemWrite, Branch, ALUOp1, ALUOp0, ALUCode]
    CONTROL_TABLE = {
        # R-Type
        '00000001': [1, 0, 0, 1, 0, 0, 0, 1, 0, ALU.R_TYPE_ALU_CODES['ADD']], 
        '00011000': [0, 1, 0, 1, 0, 0, 0, 0, 0, 0b0000],  # ADDI (ALUCode: ADD) 
        
        # Tipo I-ARITMÉTICO (SUBI: R[Rd] = R[Rs] - Imm)
        # Opcode 19 (00011001)
        '00011001': [0, 1, 0, 1, 0, 0, 0, 0, 0, 0b0001],  # SUBI (ALUCode: SUB)
        # I-MEM (LW/SW)
        '00010000': [0, 1, 1, 1, 1, 0, 0, 0, 0, 0b0000],  # LW
        '00010001': [0, 1, 0, 0, 0, 1, 0, 0, 0, 0b0000],  # SW
        # Controle
        '11111111': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0b0000],  # HALT
        '00000000': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0b0000]   # NOP
    }

    def __init__(self, instruction_memory: dict, data_memory_list: list, initial_pc: int = 0):
        self.PC = initial_pc 
        self.registers = data_memory_list
        self.data_memory = data_memory_list
        self.instruction_memory = instruction_memory 
        
        # --- REGISTRADORES DE PIPELINE (LATCHeS) ---
        self.IF_ID = {'PC_Next': 0, 'Instruction': '0'*32}
        self.ID_EX = self._get_nop_latch('ID_EX')      # Latch IF/ID -> EX/MEM
        self.EXMEM_WB = self._get_nop_latch('EXMEM_WB') # Latch EX/MEM -> WB (Novo nome)

        self.clock_cycle = 0
        self.running = True

    def _get_nop_latch(self, stage: str) -> dict:
        """Retorna um dicionário representando um latch vazio (NOP) com Mnemonic."""
        base_ctrl = {'RegDst': 0, 'ALUSrc': 0, 'MemToReg': 0, 'RegWrite': 0, 
                     'MemRead': 0, 'MemWrite': 0, 'Branch': 0, 'ALUOp': (0, 0), 
                     'ALUCode': 0, 'Mnemonic': 'NOP'} 
        
        if stage == 'ID_EX':
            return {'PC_Next': 0, 'Read_Data_1': 0, 'Read_Data_2': 0, 'Immediate': 0, 
                    'Rt': 0, 'Rd': 0, 'Control_Signals': base_ctrl}
        elif stage == 'EXMEM_WB': # Novo latch entre EX/MEM e WB
            ctrl_exmem_wb = {k: base_ctrl[k] for k in ['MemToReg', 'RegWrite', 'Mnemonic']}
            return {'ALU_Result': 0, 'Mem_Read_Data': 0, 'Rd': 0, 
                    'Control_Signals': ctrl_exmem_wb}
        return {}
    
    def _get_instruction_name(self, instruction_binary: str) -> str:
        """Retorna o nome da instrução (Mnemonic) a partir do binário."""
        if instruction_binary == '0'*32:
            return 'NOP'
        opcode_bin = instruction_binary[0:8]
        op_info = OPCODE_MAP.get(opcode_bin, {'name': 'UNKNOWN'})
        return op_info['name']

    def _print_pipeline_state(self):
        """Imprime o estado atual de cada estágio do pipeline (4 estágios)."""
        
        # Rastreia os Mnemonic nos latches
        name_if_id = self._get_instruction_name(self.IF_ID['Instruction'])
        name_id_ex = self.ID_EX['Control_Signals']['Mnemonic']
        name_exmem_wb = self.EXMEM_WB['Control_Signals']['Mnemonic']
        
        # A instrução no WB é aquela que acabou de sair do EXMEM_WB
        name_wb = name_exmem_wb if name_exmem_wb != 'NOP' else '---'

        # Novo formato de impressão com EX/MEM
        print(f"| Instrução: | {name_if_id:<8} | {name_id_ex:<8} | {name_exmem_wb:<8} | {name_wb:<8} |")


    # --- ESTÁGIOS DO PIPELINE ---

    def fetch(self):
        """Estágio IF: Busca a Instrução."""
        if not self.running: return

        instruction_binary = self.instruction_memory.get(self.PC, '0'*32)
        
        self.IF_ID['PC_Next'] = self.PC + 4
        self.IF_ID['Instruction'] = instruction_binary
        
        # O PC é incrementado para o próximo ciclo
        self.PC += 4

    def decode(self):
        """Estágio ID: Decodifica a Instrução, Lê Registradores e Gera Sinais de Controle."""
        
        instruction_binary = self.IF_ID['Instruction']
        
        if not self.running or instruction_binary == '0'*32:
            self.ID_EX = self._get_nop_latch('ID_EX')
            return 

        try:
            decoded_fields = decode_instruction(instruction_binary)
        except ValueError:
            self.ID_EX = self._get_nop_latch('ID_EX')
            return
            
        opcode_bin = decoded_fields['opcode_bin']
        control_signals = self.CONTROL_TABLE.get(opcode_bin, [0]*10)
        
        (reg_dst, alu_src, mem_to_reg, reg_write, mem_read, 
         mem_write, branch, alu_op1, alu_op0, alu_code) = control_signals
        
        rs_index = decoded_fields.get('Rs', 0)
        rt_index = decoded_fields.get('Rt', 0)

        mnemonic = decoded_fields['mnemonic']
        
        if mnemonic in ['ADD', 'SUB'] and decoded_fields.get('type') == 'R':
            # R-Type: Destino é Rd
            write_reg_index = decoded_fields.get('Rd', 0)
        elif mnemonic in ['LW', 'ADDI', 'SUBI']:
            # I-Type (Aritmético/Load): Destino é Rt
            write_reg_index = rt_index
        else:
            # SW, HALT, NOP: Não escrevem ou usam Rt/Rd de forma diferente
            write_reg_index = 0
        
        # Segurança contra HALT: se for HALT, forçamos R0, pois ele não deve usar dados.
        if decoded_fields['mnemonic'] == 'HALT':
            read_data_1 = 0 
            read_data_2 = 0 
        else:
            read_data_1 = read_reg(self.registers, rs_index)
            read_data_2 = read_reg(self.registers, rt_index) 
        
        # Atualiza o latch ID/EX
        self.ID_EX = {
            'PC_Next': self.IF_ID['PC_Next'],
            'Read_Data_1': read_data_1,
            'Read_Data_2': read_data_2,
            'Immediate': decoded_fields.get('Immediate', 0),
            'Rt': rt_index,
            'Rd': decoded_fields.get('Rd', rt_index), 
            'Control_Signals': {
                'RegDst': reg_dst, 'ALUSrc': alu_src, 'MemToReg': mem_to_reg, 
                'RegWrite': reg_write, 'MemRead': mem_read, 'MemWrite': mem_write, 
                'Branch': branch, 'ALUOp': (alu_op1, alu_op0), 'ALUCode': alu_code,
                'Mnemonic': decoded_fields['mnemonic']
            }
        }

    def execute_and_memory_access(self):
        """Estágio EX/MEM: Executa a ULA e Acessa a Memória de Dados (Estágios Fundidos)."""
        if not self.running: return

        ctrl = self.ID_EX['Control_Signals']
        
        if ctrl['Mnemonic'] == 'NOP':
            self.EXMEM_WB = self._get_nop_latch('EXMEM_WB')
            return

        # --- PARTE 1: EXECUTE (EX) ---
        
        # ALU Inputs
        alu_input_a = self.ID_EX['Read_Data_1']
        alu_input_b = self.ID_EX['Immediate'] if ctrl['ALUSrc'] == 1 else self.ID_EX['Read_Data_2']
        
        # Execução da ULA
        alu_code = ctrl['ALUCode']
        alu_result = ALU.execute(alu_code, alu_input_a, alu_input_b)
        
        # MUX de Destino do Registrador
        write_reg_index = self.ID_EX['Rd'] if ctrl['RegDst'] == 1 else self.ID_EX['Rt'] 
        
        # --- PARTE 2: MEMORY ACCESS (MEM) ---
        
        mem_read_data = 0
        mem_address = alu_result # O resultado da ULA é o endereço
        write_data = self.ID_EX['Read_Data_2'] # Dado para SW
        
        # Verificação de Alinhamento de Memória
        if ctrl['MemRead'] == 1 or ctrl['MemWrite'] == 1:
            if mem_address % 4 != 0:
                print(f"\nERRO FATAL: Endereço de memória não alinhado: {mem_address}")
                self.running = False
                self.EXMEM_WB = self._get_nop_latch('EXMEM_WB')
                return 

        # 1. MemWrite (SW)
        if ctrl['MemWrite'] == 1:
            write_mem(self.data_memory, mem_address, write_data)
            
        # 2. MemRead (LW)
        if ctrl['MemRead'] == 1:
            mem_read_data = read_mem(self.data_memory, mem_address)

        # --- PARTE 3: ATUALIZA O LATCH EXMEM_WB ---
        self.EXMEM_WB = {
            'ALU_Result': alu_result,
            'Mem_Read_Data': mem_read_data,
            'Rd': write_reg_index,
            'Control_Signals': {
                'MemToReg': ctrl['MemToReg'], 
                'RegWrite': ctrl['RegWrite'],
                'Mnemonic': ctrl['Mnemonic']
            }
        }

    def write_back(self):
        """Estágio WB: Escreve o Resultado no Banco de Registradores e Checa HALT."""
        if not self.running: return

        ctrl = self.EXMEM_WB['Control_Signals']
        
        # 0. HALT Check: Desliga a simulação
        if ctrl['Mnemonic'] == 'HALT':
             self.running = False
             return
        
        if ctrl['Mnemonic'] == 'NOP':
            return

        # 1. MUX MemToReg
        write_data = self.EXMEM_WB['Mem_Read_Data'] if ctrl['MemToReg'] == 1 else self.EXMEM_WB['ALU_Result']

        # 2. RegWrite
        if ctrl['RegWrite'] == 1:
            write_reg(self.registers, self.EXMEM_WB['Rd'], write_data)
            
        
    def step(self):
        """Executa um ciclo de relógio, movendo todas as instruções um estágio (4 estágios)."""
        self.write_back()
        self.execute_and_memory_access()
        self.decode()
        self.fetch()
        
        self.clock_cycle += 1

    def run(self):
        """Roda a simulação."""
        print("\n--- INÍCIO DA SIMULAÇÃO ---")
        # Nomes das colunas ajustados para 4 estágios
        print("| Estágio:     | IF       | ID       | EX/MEM   | WB       |")
        print("| Instrução:   | IF/ID    | ID/EX    | EXMEM/WB | WB       |")
        print("+" + "-"*56 + "+")

        while self.running and self.clock_cycle < 100: 
            self.step()
            
            print(f"Ciclo {self.clock_cycle:03} (PC=0x{self.PC:04X}):")
            self._print_pipeline_state()
            
        print("\n--- FIM DA SIMULAÇÃO ---")
        print(f"Total de Ciclos: {self.clock_cycle}")
        print("\nREGISTRADORES FINAIS:")
        print_registers(self.registers)
        print("\nMEMÓRIA DE DADOS FINAIS (Apenas os primeiros 16):")
        print_memory_data(self.data_memory)