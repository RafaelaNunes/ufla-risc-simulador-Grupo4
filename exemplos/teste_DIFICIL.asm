# OBJETIVO: Quebrar o pipeline se houver qualquer erro de hazard.

ADDI R1, R0, 10
ADDI R2, R0, 2

ADD  R3, R1, R2      
MUL  R4, R3, R2      

ADDI R10, R0, 0
SW   R10, R4         
LW   R5, R10         
ADD  R6, R5, R1      

ADDI R7, R0, 5
BEQ  R7, R7, 52

ADDI R8, R0, 666    
SW   R10, R8        
J    56              

ANDI R9, R6, 10

ADDI R11, R0, 4
SW   R11, R9        

HALT