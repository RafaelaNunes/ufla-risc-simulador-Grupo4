# instruction.py
class Instruction:
    # Mapeamento dos Opcodes de 8 bits
    OPCODE_MAP = {
        # ... (Opcodes anteriores) ...
        '00000001': {'name': 'ADD', 'type': 'R'},
        '00001111': {'name': 'LLI', 'type': 'I_CONST'},
        '00010000': {'name': 'LW', 'type': 'I_MEM'},
        '00010001': {'name': 'SW', 'type': 'I_MEM'},
        
        # Novo Opcode de Parada
        '11111111': {'name': 'HALT', 'type': 'HALT'},
        
        # NOP/UNKNOWN
        '00000000': {'name': 'NOP', 'type': 'NOP'}
        # ... Outros Opcodes R/I/J
    }

    def __init__(self, binary_string: str):
        """Inicializa e decodifica a instrução a partir da string binária de 32 bits."""
        if len(binary_string.strip()) != 32:
            raise ValueError("A string binária deve ter exatamente 32 bits.")
        
        self.full_binary = binary_string.strip()
        
        # 1. Extrai os campos brutos
        self.opcode_bin = self.full_binary[0:8]
        self.field_rt_bin = self.full_binary[8:16]
        self.field_rs_bin = self.full_binary[16:24]
        self.field_extra_bin = self.full_binary[24:32]
        
        # 2. Obtém as informações do Opcode
        op_info = self.OPCODE_MAP.get(self.opcode_bin, {'name': 'UNKNOWN', 'type': 'UNKNOWN'})
        self.mnemonic = op_info['name']
        self.type = op_info['type']
        
        # 3. Decodifica os campos baseado no Tipo
        self.decode_fields()

    # ... (Métodos _bin_to_reg, _bin_to_imm permanecem os mesmos) ...
    def _bin_to_reg(self, bin_str: str) -> str:
        reg_index = int(bin_str[-5:], 2) 
        return f"R{reg_index}"

    def _bin_to_imm(self, bin_str: str) -> int:
        if bin_str[0] == '1':
            return int(bin_str, 2) - (1 << 8)
        else:
            return int(bin_str, 2)

    def decode_fields(self):
        """Define os campos de registrador/imediato baseados no tipo de instrução."""
        self.Rd, self.Rs, self.Rt, self.Offset, self.Immediate = None, None, None, None, None
        
        if self.type == 'R':
            # Formato R: [Opcode (8), Rd (8), Rs (8), Rt (8)]
            self.Rd = self._bin_to_reg(self.field_rt_bin)
            self.Rs = self._bin_to_reg(self.field_rs_bin)
            self.Rt = self._bin_to_reg(self.field_extra_bin)
            
        elif self.type == 'I_MEM':
            # Formato I (Memória): [Opcode (8), Rt (8), Rs (8), Offset (8)]
            self.Rt = self._bin_to_reg(self.field_rt_bin)
            self.Rs = self._bin_to_reg(self.field_rs_bin)
            self.Offset = self._bin_to_imm(self.field_extra_bin)
            
        elif self.type == 'I_CONST':
            # Formato I (Constante): [Opcode (8), Rt (8), Imediato (16 bits)]
            self.Rt = self._bin_to_reg(self.field_rt_bin)
            immediate_16_bin = self.field_rs_bin + self.field_extra_bin
            self.Immediate = int(immediate_16_bin, 2)
            
        elif self.type == 'HALT':
            # HALT não tem operandos relevantes, mas pode usar os 24 bits restantes
            pass

    def to_assembly(self) -> str:
        """Retorna a instrução em formato Assembly."""
        if self.type == 'R':
            return f"{self.mnemonic} {self.Rd}, {self.Rs}, {self.Rt}"
        elif self.type == 'I_MEM':
            return f"{self.mnemonic} {self.Rt}, {self.Offset}({self.Rs})"
        elif self.type == 'I_CONST':
            return f"{self.mnemonic} {self.Rt}, #{self.Immediate}"
        else:
            return self.mnemonic # Para NOP/HALT/UNKNOWN

    def __str__(self):
        """Representação detalhada para o terminal."""
        return f"  Opcode: {self.opcode_bin} ({self.type})\n  Assembly: {self.to_assembly()}"