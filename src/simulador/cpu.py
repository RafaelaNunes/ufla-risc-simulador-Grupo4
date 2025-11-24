# cpu.py
# cpu.py (Corrigido)

# Importações relativas corrigidas:
from src.simulador.registers import create_registers, read_reg, write_reg, print_registers
from src.simulador.memory import create_memory, read_mem, write_mem, load_instruction_mem, print_memory_data
from src.simulador.instruction import Instruction 
# ... (Resto da classe CPU)

class CPU:
    """
    Simulador da Unidade Central de Processamento (CPU) UFLA-RISC, 
    implementando um pipeline de 5 estágios.
    """
    def __init__(self, instruction_memory: dict, data_memory_list: list, initial_pc: int = 0):
        # ----------------------------------------
        # ESTADO PRINCIPAL
        # ----------------------------------------
        self.PC = initial_pc 
        self.registers = data_memory_list
        self.data_memory = data_memory_list
        # A memória de instruções é um dicionário Endereço -> Binário (carregado pelo driver)
        self.instruction_memory = instruction_memory 
        
        # ----------------------------------------
        # REGISTRADORES DE PIPELINE (LATCHeS)
        # Inicializados como NOPs (valores zerados)
        # Estrutura: Dicionários para carregar o conteúdo de cada latch
        # ----------------------------------------
        self.IF_ID = {'PC_Next': 0, 'Instruction': '0'*32}
        self.ID_EX = {'PC_Next': 0, 'Read_Data_1': 0, 'Read_Data_2': 0, 'Immediate': 0, 
                      'Rt': 0, 'Rd': 0, 'Control_Signals': {}}
        self.EX_MEM = {'ALU_Result': 0, 'Write_Data': 0, 'Mem_Address': 0, 
                       'Rd': 0, 'Control_Signals': {}}
        self.MEM_WB = {'ALU_Result': 0, 'Mem_Read_Data': 0, 
                       'Rd': 0, 'Control_Signals': {}}

        # ----------------------------------------
        # CONTADORES E CONTROLE
        # ----------------------------------------
        self.clock_cycle = 0
        self.running = True

    # ----------------------------------------
    # ESTÁGIOS DO PIPELINE
    # ----------------------------------------

    def fetch(self):
        """Estágio IF: Busca a Instrução."""
        if not self.running: return

        # 1. Lê a string binária da memória de instruções (ou retorna NOP)
        instruction_binary = self.instruction_memory.get(self.PC, '0'*32)
        
        # 2. Atualiza o registrador IF/ID
        self.IF_ID['PC_Next'] = self.PC + 4
        self.IF_ID['Instruction'] = instruction_binary
        
        # 3. Atualiza o PC para o ciclo seguinte (salto/branch será tratado na fase EX/MEM)
        # Se for um Branch ou Jump, o PC será sobrescrito em EX ou MEM
        self.PC += 4

    def decode(self):
        """Estágio ID: Decodifica a Instrução e Lê Registradores."""
        if not self.running: return

        # 1. Pega a instrução do latch IF/ID
        instruction_binary = self.IF_ID['Instruction']
        
        # Se for NOP, não faz nada (mantém os valores zero/NOP no ID_EX)
        if instruction_binary == '0'*32:
            return 
        
        # 2. Decodifica (usa a classe Instruction)
        try:
            inst = Instruction(instruction_binary)
        except:
            print(f"ERRO: Decodificação falhou para {instruction_binary}")
            return
            
        # [TODO: Hazard Detection deve inserir uma bolha/NOP aqui se houver Load-Use]

        # 3. Lê Registradores (Rs e Rt)
        # Esta parte requer a extração manual dos índices dos registradores do binário 
        # (para evitar a complexidade do objeto 'inst' passando pelo pipeline)
        
        # Rs e Rt (campos de 8 bits)
        rs_bin = instruction_binary[16:24]
        rt_bin = instruction_binary[8:16]
        
        # Conversão dos 5 bits inferiores para índice decimal
        rs_index = int(rs_bin[-5:], 2)
        rt_index = int(rt_bin[-5:], 2)

        read_data_1 = read_reg(self.registers, rs_index)
        read_data_2 = read_reg(self.registers, rt_index)
        
        # 4. Gera Sinais de Controle (Simplificado: Opcode)
        # [TODO: Lógica completa da Control Unit deve gerar os sinais 'Control_Signals']
        
        # 5. Atualiza o registrador ID/EX
        self.ID_EX['Read_Data_1'] = read_data_1
        self.ID_EX['Read_Data_2'] = read_data_2
        self.ID_EX['PC_Next'] = self.IF_ID['PC_Next']
        # [TODO: Implementar extração do Immediate e geração de sinais de controle]
        
    def execute(self):
        """Estágio EX: Executa a ULA e calcula endereços."""
        if not self.running: return

        # [TODO: Implementar Forwarding Unit (Bypass) aqui, usando EX_MEM e MEM_WB]

        # 1. Executa a ULA (Depende dos sinais de controle em ID_EX)
        # ... (Lógica da ULA) ...
        # self.EX_MEM['ALU_Result'] = ...

        # 2. Atualiza o registrador EX/MEM
        # self.EX_MEM['Write_Data'] = self.ID_EX['Read_Data_2'] # Dado para SW
        # self.EX_MEM['Rd'] = self.ID_EX['Rd'] 
        # ...
        
    def memory_access(self):
        """Estágio MEM: Acessa a Memória de Dados."""
        if not self.running: return

        # [TODO: Implementar Lógica de MemRead/MemWrite usando EX_MEM]

        # 1. Se MemRead (LW): Lê da memória de dados
        # self.MEM_WB['Mem_Read_Data'] = read_mem(self.data_memory, self.EX_MEM['ALU_Result'])
        
        # 2. Se MemWrite (SW): Escreve na memória de dados
        # write_mem(self.data_memory, self.EX_MEM['ALU_Result'], self.EX_MEM['Write_Data'])
        
        # 3. Atualiza o registrador MEM/WB
        # self.MEM_WB['Rd'] = self.EX_MEM['Rd'] 
        # ...

    def write_back(self):
        """Estágio WB: Escreve o Resultado no Banco de Registradores."""
        if not self.running: return

        # [TODO: Implementar Lógica de RegWrite usando MEM_WB]

        # 1. Se RegWrite (ADD, LW, etc.): 
        # write_reg(self.registers, self.MEM_WB['Rd'], self.MEM_WB['ALU_Result'] ou self.MEM_WB['Mem_Read_Data'])
        # 2. Checa HALT (Se a instrução no MEM_WB for HALT, set self.running = False)
        # ...
        
    def step(self):
        """Executa um ciclo de relógio, movendo todas as instruções um estágio."""
        self.write_back()
        self.memory_access()
        self.execute()
        self.decode()
        self.fetch()
        
        self.clock_cycle += 1

    def run(self):
        """Roda a simulação até encontrar um HALT."""
        print("\n--- INÍCIO DA SIMULAÇÃO ---")
        while self.running and self.clock_cycle < 100: # Limite de ciclos para evitar loop infinito
            self.step()
            print(f"Ciclo {self.clock_cycle:03}: PC=0x{self.PC:04X}")
            # [TODO: Implementar um print detalhado dos estágios aqui]
            
        print("\n--- FIM DA SIMULAÇÃO ---")
        print(f"Total de Ciclos: {self.clock_cycle}")
        print_registers(self.registers)
        print_memory_data(self.data_memory)