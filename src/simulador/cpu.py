# cpu.py

# Imports
from src.simulador.registers import read_reg, write_reg, print_registers
from src.simulador.memory import read_mem, write_mem, print_memory_data
from src.simulador.instruction import decode_instruction, OPCODE_MAP 
import operator

# --- UNIDADE DE CONTROLE E ULA (ALU) ---

class ALU:
    """Implementa as funções da Unidade Lógica Aritmética (ULA)."""
    
    R_TYPE_ALU_CODES = {
        'ADD': 0b0000, 'SUB': 0b0001, 'ZERO': 0b0010, 'XOR': 0b0011, 'OR': 0b0100, 
        'NOT': 0b0101, 'AND': 0b0110, 'SLA': 0b0111, 'SRA': 0b1000, 'SLL': 0b1001, 
        'SRL': 0b1010, 'COPY': 0b1011
    }

    @staticmethod
    def execute(operation_code: int, input_a: int, input_b: int) -> int:
        """Executa a operação da ULA e retorna o resultado (limitado a 32 bits)."""
        result = 0
        
        # A ULA é usada para todos os cálculos, incluindo endereço (ADD)
        if operation_code == 0b0000: # ADD (Load/Store, LUI/LLI, ADD R-Type)
            result = input_a + input_b
        elif operation_code == 0b0001: # SUB
            result = input_a - input_b
        elif operation_code == 0b0010: # ZERO
            result = 0
        elif operation_code == 0b0011: # XOR
            result = input_a ^ input_b
        elif operation_code == 0b0100: # OR
            result = input_a | input_b
        elif operation_code == 0b0101: # NOT (Apenas nega o primeiro operando)
            result = ~input_a 
        elif operation_code == 0b0110: # AND
            result = input_a & input_b
        elif operation_code == 0b0111: # SLA/SLL (Shift Left Arithmetic/Logical)
            result = input_a << input_b
        elif operation_code == 0b1000: # SRA (Shift Right Arithmetic)
            result = input_a >> input_b
        elif operation_code == 0b1010: # SRL (Shift Right Logical) - Necessário para SRL
            result = (input_a % 0x100000000) >> input_b
        elif operation_code == 0b1011: # COPY
            result = input_a
        else:
            result = 0 # NOP

        # Garante que o resultado é tratado como um inteiro de 32 bits (wrap-around)
        return result & 0xFFFFFFFF


class CPU:
    """Simulador da Unidade Central de Processamento (CPU) UFLA-RISC com Pipeline de 5 estágios."""

    # [RegDst, ALUSrc, MemToReg, RegWrite, MemRead, MemWrite, Branch, ALUOp1, ALUOp0, ALUCode]
    CONTROL_TABLE = {
        # R-Type: [Rd, Rt, 0, 1, 0, 0, 0, 1, 0, ALU_R_Code]
        '00000001': [1, 0, 0, 1, 0, 0, 0, 1, 0, ALU.R_TYPE_ALU_CODES['ADD']], 
        '00000010': [1, 0, 0, 1, 0, 0, 0, 1, 0, ALU.R_TYPE_ALU_CODES['SUB']], 
        '00000111': [1, 0, 0, 1, 0, 0, 0, 1, 0, ALU.R_TYPE_ALU_CODES['AND']], 
        '00001100': [1, 0, 0, 1, 0, 0, 0, 1, 0, ALU.R_TYPE_ALU_CODES['COPY']], 
        # ... (Outros R-Types omitidos para brevidade, mas devem seguir o padrão)
        
        # I-CONST (LUI/LLI): [Rt, Imediato, 0, 1, 0, 0, 0, 0, 0, 0000(ADD)]
        '00001110': [0, 1, 0, 1, 0, 0, 0, 0, 0, 0b0000],  # LUI (Usa ALU ADD)
        '00001111': [0, 1, 0, 1, 0, 0, 0, 0, 0, 0b0000],  # LLI (Usa ALU ADD)
        
        # I-MEM (LW/SW)
        '00010000': [0, 1, 1, 1, 1, 0, 0, 0, 0, 0b0000],  # LW: [Rt, Imediato, MemToReg, RegWrite, MemRead, NoMemWrite, NoBranch, Add, 0000]
        '00010001': [0, 1, 0, 0, 0, 1, 0, 0, 0, 0b0000],  # SW: [Rt, Imediato, NoMem, NoWriteReg, NoReadMem, WriteMem, NoBranch, Add, 0000]
        
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
        self.ID_EX = self._get_nop_latch('ID_EX')
        self.EX_MEM = self._get_nop_latch('EX_MEM')
        self.MEM_WB = self._get_nop_latch('MEM_WB')

        self.clock_cycle = 0
        self.running = True

    def _get_nop_latch(self, stage: str) -> dict:
        """Retorna um dicionário representando um latch vazio (NOP) com Mnemonic."""
        # Sinais de controle base para um NOP
        base_ctrl = {'RegDst': 0, 'ALUSrc': 0, 'MemToReg': 0, 'RegWrite': 0, 
                     'MemRead': 0, 'MemWrite': 0, 'Branch': 0, 'ALUOp': (0, 0), 
                     'ALUCode': 0, 'Mnemonic': 'NOP'} 
        
        if stage == 'ID_EX':
            return {'PC_Next': 0, 'Read_Data_1': 0, 'Read_Data_2': 0, 'Immediate': 0, 
                    'Rt': 0, 'Rd': 0, 'Control_Signals': base_ctrl}
        elif stage == 'EX_MEM':
            ctrl_ex_mem = {k: base_ctrl[k] for k in ['MemToReg', 'RegWrite', 'MemRead', 'MemWrite', 'Mnemonic']}
            return {'ALU_Result': 0, 'Write_Data': 0, 'Mem_Address': 0, 'Rd': 0, 
                    'Control_Signals': ctrl_ex_mem}
        elif stage == 'MEM_WB':
            ctrl_mem_wb = {k: base_ctrl[k] for k in ['MemToReg', 'RegWrite', 'Mnemonic']}
            return {'ALU_Result': 0, 'Mem_Read_Data': 0, 'Rd': 0, 
                    'Control_Signals': ctrl_mem_wb}
        return {}
    
    def _get_instruction_name(self, instruction_binary: str) -> str:
        """Retorna o nome da instrução (Mnemonic) a partir do binário."""
        if instruction_binary == '0'*32:
            return 'NOP'
        opcode_bin = instruction_binary[0:8]
        op_info = OPCODE_MAP.get(opcode_bin, {'name': 'UNKNOWN'})
        return op_info['name']

    def _print_pipeline_state(self):
        """Imprime o estado atual de cada estágio do pipeline."""
        
        # Rastreia os Mnemonic nos latches
        name_if_id = self._get_instruction_name(self.IF_ID['Instruction'])
        name_id_ex = self.ID_EX['Control_Signals']['Mnemonic']
        name_ex_mem = self.EX_MEM['Control_Signals']['Mnemonic']
        name_mem_wb = self.MEM_WB['Control_Signals']['Mnemonic']
        
        # A instrução no WB é aquela que acabou de sair do MEM/WB
        name_wb = name_mem_wb if name_mem_wb != 'NOP' else '---'

        print(f"| Instrução: | {name_if_id:<8} | {name_id_ex:<8} | {name_ex_mem:<8} | {name_mem_wb:<8} | {name_wb:<8} |")


    # --- ESTÁGIOS DO PIPELINE ---

    def fetch(self):
        """Estágio IF: Busca a Instrução."""
        if not self.running: return

        instruction_binary = self.instruction_memory.get(self.PC, '0'*32)
        
        self.IF_ID['PC_Next'] = self.PC + 4
        self.IF_ID['Instruction'] = instruction_binary
        
        # O PC é incrementado para o próximo ciclo (Branch/Jump será tratado em EX/MEM)
        self.PC += 4

    def decode(self):
        """Estágio ID: Decodifica a Instrução, Lê Registradores e Gera Sinais de Controle."""
        
        instruction_binary = self.IF_ID['Instruction']
        
        if not self.running or instruction_binary == '0'*32:
            self.ID_EX = self._get_nop_latch('ID_EX')
            return 

        # 1. Decodifica campos
        try:
            decoded_fields = decode_instruction(instruction_binary)
        except ValueError:
            print(f"ERRO: Decodificação falhou para {instruction_binary}. Injetando NOP.")
            self.ID_EX = self._get_nop_latch('ID_EX')
            return
            
        opcode_bin = decoded_fields['opcode_bin']
        
        # 2. Geração dos Sinais de Controle
        control_signals = self.CONTROL_TABLE.get(opcode_bin, [0]*10)
        
        (reg_dst, alu_src, mem_to_reg, reg_write, mem_read, 
         mem_write, branch, alu_op1, alu_op0, alu_code) = control_signals
        
        # 3. Leitura dos Registradores
        rs_index = decoded_fields.get('Rs', 0) 
        rt_index = decoded_fields.get('Rt', 0)
    
        read_data_1 = read_reg(self.registers, rs_index)
        read_data_2 = read_reg(self.registers, rt_index)
        
        # 4. Atualiza o latch ID/EX
        self.ID_EX = {
            'PC_Next': self.IF_ID['PC_Next'],
            'Read_Data_1': read_data_1,
            'Read_Data_2': read_data_2,
            'Immediate': decoded_fields.get('Immediate', 0),
            'Rt': rt_index,
            # Rd é usado para R-Type, senão o destino é Rt (I-Type)
            'Rd': decoded_fields.get('Rd', rt_index), 
            'Control_Signals': {
                'RegDst': reg_dst, 'ALUSrc': alu_src, 'MemToReg': mem_to_reg, 
                'RegWrite': reg_write, 'MemRead': mem_read, 'MemWrite': mem_write, 
                'Branch': branch, 'ALUOp': (alu_op1, alu_op0), 'ALUCode': alu_code,
                'Mnemonic': decoded_fields['mnemonic']
            }
        }

    def execute(self):
        """Estágio EX: Executa a ULA e calcula endereços."""
        if not self.running: return

        ctrl = self.ID_EX['Control_Signals']
        
        if ctrl['Mnemonic'] == 'NOP':
            self.EX_MEM = self._get_nop_latch('EX_MEM')
            return

        # 1. ALU Inputs (ALUSrc MUX)
        alu_input_a = self.ID_EX['Read_Data_1']
        
        # Se ALUSrc=1, usa o Immediate; senão, usa Read_Data_2 (Rt)
        if ctrl['ALUSrc'] == 1:
            alu_input_b = self.ID_EX['Immediate']
            # Para LUI, o imediato de 16 bits precisa ser shiftado em 16
            if ctrl['Mnemonic'] == 'LUI':
                alu_input_b = self.ID_EX['Immediate'] << 16 
        else:
            alu_input_b = self.ID_EX['Read_Data_2']
            
        # 2. Execução da ULA
        alu_code = ctrl['ALUCode']
        alu_result = ALU.execute(alu_code, alu_input_a, alu_input_b)
        
        # 3. MUX de Destino do Registrador (Rd ou Rt)
        write_reg_index = self.ID_EX['Rd'] if ctrl['RegDst'] == 1 else self.ID_EX['Rt'] 

        # 4. Atualiza o latch EX/MEM
        self.EX_MEM = {
            'ALU_Result': alu_result,
            'Write_Data': self.ID_EX['Read_Data_2'], # Dado para SW (sempre Rt)
            'Mem_Address': alu_result, # Endereço para L/S (Rs + Offset)
            'Rd': write_reg_index,
            'Control_Signals': {
                'MemToReg': ctrl['MemToReg'], 
                'RegWrite': ctrl['RegWrite'], 
                'MemRead': ctrl['MemRead'], 
                'MemWrite': ctrl['MemWrite'],
                'Mnemonic': ctrl['Mnemonic']
            }
        }
        
    def memory_access(self):
        """Estágio MEM: Acessa a Memória de Dados."""
        if not self.running: return

        ctrl = self.EX_MEM['Control_Signals']
        mem_read_data = 0
        mem_address = self.EX_MEM['Mem_Address']
        
        if ctrl['Mnemonic'] == 'NOP':
            self.MEM_WB = self._get_nop_latch('MEM_WB')
            return

        # *** CORREÇÃO: VERIFICAÇÃO DE ALINHAMENTO DE MEMÓRIA ***
        if ctrl['MemRead'] == 1 or ctrl['MemWrite'] == 1:
            if mem_address % 4 != 0:
                print(f"\nERRO FATAL: Endereço de memória não alinhado: {mem_address}")
                self.running = False
                self.MEM_WB = self._get_nop_latch('MEM_WB') # Bolha/NOP no resto do pipeline
                return 

        # 1. MemWrite (SW)
        if ctrl['MemWrite'] == 1:
            write_mem(self.data_memory, mem_address, self.EX_MEM['Write_Data'])
            
        # 2. MemRead (LW)
        if ctrl['MemRead'] == 1:
            mem_read_data = read_mem(self.data_memory, mem_address)

        # 3. Atualiza o latch MEM/WB
        self.MEM_WB = {
            'ALU_Result': self.EX_MEM['ALU_Result'],
            'Mem_Read_Data': mem_read_data,
            'Rd': self.EX_MEM['Rd'],
            'Control_Signals': {
                'MemToReg': ctrl['MemToReg'], 
                'RegWrite': ctrl['RegWrite'],
                'Mnemonic': ctrl['Mnemonic']
            }
        }

    def write_back(self):
        """Estágio WB: Escreve o Resultado no Banco de Registradores e Checa HALT."""
        if not self.running: return

        ctrl = self.MEM_WB['Control_Signals']
        
        # 0. HALT Check
        if ctrl['Mnemonic'] == 'HALT':
             self.running = False
             return
        
        if ctrl['Mnemonic'] == 'NOP':
            return

        # 1. MUX MemToReg
        if ctrl['MemToReg'] == 1:
            write_data = self.MEM_WB['Mem_Read_Data'] # Resultado de LW
        else:
            write_data = self.MEM_WB['ALU_Result'] # Resultado da ULA (R-Type, LUI/LLI)

        # 2. RegWrite
        if ctrl['RegWrite'] == 1:
            write_reg(self.registers, self.MEM_WB['Rd'], write_data)
            
        
    def step(self):
        """Executa um ciclo de relógio, movendo todas as instruções um estágio."""
        self.write_back()
        self.memory_access()
        self.execute()
        self.decode()
        self.fetch()
        
        self.clock_cycle += 1

    def run(self):
        """Roda a simulação até encontrar um HALT ou atingir o limite de ciclos."""
        print("\n--- INÍCIO DA SIMULAÇÃO ---")
        print("| Estágio:     | IF       | ID       | EX       | MEM      | WB       |")
        print("| Instrução: | IF/ID    | ID/EX    | EX/MEM   | MEM/WB   | WB       |")
        print("+" + "-"*75 + "+")

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