# Turma: DCA0130

#################
### DESCRIÇÃO ###
#################

#   A ideia principal do projeto é criar um sistema simples de automação residencial
# que adapte-se a depender do usuário presente na residência. O sistema, além do usuário,
# irá se modelar com base na temperatura do ambiente do
# horário momentâneo.
# Ideia original: Controle de refrigeração - Controle de janelas/cortinas 
# - irrigação automática - controle de iluminação

# Bibliotecas utilizadas
from pyModbusTCP.client import ModbusClient
import time
from time import sleep as delay

# Criando Cliente Modbus
client = ModbusClient(host = "127.0.0.1", port = 502, auto_open = True)

# Como aderimos a utilizar usuários distintos, acabou sendo melhor criar uma classe
# "Usuario" para facilitar a criação de cada objeto, já que as variáveis seriam as mesmas

class Usuario:
    # t = temperatura
    # h = horario
    # j = janela
    # l = luzes
    def __init__(self, nome, t_refrigeracao, t_chuveiro, h_j_aberta, h_j_semi, h_j_fechada, l_acesas, l_apagadas, ID):
        self.nome = nome
        self.t_refrigeracao = t_refrigeracao
        self.t_chuveiro = t_chuveiro
        self.h_j_aberta = h_j_aberta
        self.h_j_semi = h_j_semi
        self.h_j_fechada = h_j_fechada
        self.l_acesas = l_acesas
        self.l_apagadas = l_apagadas
        self.id = ID
    
    def t_limites (self):
        t_refrigeracao_max = self.t_refrigeracao +2
        t_refrigeracao_min = self.t_refrigeracao -2 

        return t_refrigeracao_max, t_refrigeracao_min
# Inicialmente iriamos utilizar algo para temperatura do chuveiro. NO entanto,
# com o desenvolver do projeto, julgamos não ser necessário

# Variaveis de checagem
status_usuario = 0 # 0 - Ana; 1 - Breno; 2 - Clove
usuario_datapoint = client.write_single_register(6, status_usuario)

status_refrigeracao = 0 # 0 - desligado; 1 - ligado
refrigeracao_datapoint = client.write_single_coil(1, status_refrigeracao)

status_janelas = 0 # 0 - fechadas; 1 - semi abertas; 2 - abertas
janelas_datapoint = client.write_single_register(2, status_janelas)

status_luzes = 0 # 0 - apagadas; 1 - acesas
luzes_datapoint = client.write_single_coil(3, status_luzes)

status_irrigacao = 0 # 0 - desligado; 1 - ligado
irrigacao_datapoint = client.write_single_coil(4, status_irrigacao)

temperatura_residencia = 25 # - Deve estar nos limites do sistema de refrigeração - 15°C <-> 30°C
temperatura_datapoint = client.write_single_register(5, temperatura_residencia)

# Criando usuários (nesse código é limitado aos já criados)
p1 = Usuario('Ana', 20, 35, 7, 13, 18, 18, 23, 0)   
p2 = Usuario('Breno', 17, 30, 9, 15, 20, 17, 22, 1)
p3 = Usuario('Clove', 19, 39, 6, 11, 18, 16, 22, 2)  

usuarios = [p1, p2, p3] # -> a ideia é que o usuario seja alternado a cada 24h || lembrar de adicionar um módulo 
                        # cliente de verificação do usuário no ScadaBR

hora_atual = int(0)

while True:
    client.open()
    for usuario in usuarios:

        print(f'\nAlternando usuário para {usuario.nome}\n')
        status_usuario = usuario.id  #aplicamos uma id para identificar o usuário pelos gráficos, já que não contamos em utilizar strings no ScadaBR
        client.write_single_register(6,status_usuario)
        
        delay(2)

        for hora_atual in range (25):
            
            if (hora_atual == 25):
                print("\nDia finalizado.")
                hora_atual = 0
                delay(1)
                

            if(hora_atual == 0):
                print ("\nIniciando o dia!")
                delay(1)
            
            t_max, t_min = usuario.t_limites() # - Obtendo as temperaturas minima e máxima do usuário
            
            print(f"\n--- Usuário atual: {usuario.nome} ({usuario.id}) || Horário: {hora_atual}h || Temperatura = {temperatura_residencia}°C ---")
            delay(0.5)

            # Sistema de irrigação - deixamos fora da classe porque não depende dos usuários

            if(6 <= hora_atual <= 8):
                status_irrigacao = 1
                print("Sistema de irrigação LIGADO")
            else:
                status_irrigacao = 0
                print("Sistema de irrigação DESLIGADO")
            client.write_single_coil(4, status_irrigacao)

            # Sistema de janelas -- h_j_aberta < h_j_semi < h_j_fechada
            if(usuario.h_j_aberta <= hora_atual < usuario.h_j_semi):
                status_janelas = 2
                print("As janelas estão ABERTAS")
            elif(usuario.h_j_semi <= hora_atual < usuario.h_j_fechada):
                status_janelas = 1
                print("As janelas estão SEMIABERTAS")
            else:
                status_janelas = 0
                print("As janelas estão FECHADAS")
            client.write_single_register(2,status_janelas)

            # Sistema de luzes - funcionam com horários minimos e máximos também
            if(usuario.l_acesas <= hora_atual < usuario.l_apagadas):
                status_luzes = 1
                print("As luzes estão ACESAS")
            else:
                status_luzes = 0
                print("As luzes estão APAGADAS")
            client.write_single_coil(3, status_luzes)

            # Sistema de refrigeração - funcionamento distinto: Se janelas abertas ou semiabertas = refrigeramento desligado
            #                           se janelas fechadas e temperatura acima da máxima - refrigeramento ligado
            #                           se janelas fechadas e temperatura abaixo da máxima - refrigeramento desligado 


            # Checagem se janelas abertas  

            temperatura_antiga = temperatura_residencia
            if(status_janelas == 1 or status_janelas == 2):
                status_refrigeracao = 0
                print("Sistema de refrigeração DESLIGADO")
            else:
                if(temperatura_residencia < t_min):
                    status_refrigeracao = 0
                    print ("Sistema de refrigeração DESLIGADO")
                elif(temperatura_residencia > t_max):
                    status_refrigeracao = 1
                    print ("Sistema de refrigeração LIGADO")
                elif(temperatura_antiga < temperatura_residencia):
                    status_refrigeracao = 0
                    print("Sistema de refrigeração DESLIGADO")
                else:
                    status_refrigeracao = 1
                    print("Sistema de refrigeração LIGADO")
            client.write_single_coil(1, status_refrigeracao)
                
            # Checagem da temperatura - se refrigeramento ligado = - 1°C/h 
            #                           se refrigeramento desligado = + 1°C/h
            # Também foi incluido limite de variação da temperatura
            
            if (status_refrigeracao == 1 and temperatura_residencia > 15):
                temperatura_residencia -= 2
            elif(status_refrigeracao == 0 and temperatura_residencia < 30):
                temperatura_residencia += 1
            client.write_single_register(5, temperatura_residencia)

            hora_atual += 1
            delay(0.2)
