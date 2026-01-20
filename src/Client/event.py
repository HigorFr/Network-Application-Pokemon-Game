from abc import ABC, abstractmethod
import time, queue, logging
import traceback
from game.battle import Battle

class Evento(ABC):

    @abstractmethod
    def start(self, context):      
        pass



class EventoMenu(Evento):

    def __init__(self, new):
        self.new = new

    def start(self, context):
        self.playerinfo = context.playerinfo
        self.challenge_manager = context.challenge_manager
        self.input_queue = context.input_queue
        self.server = context.server
        self.event_queue = context.event_queue

        
        # Loop principal com comandos atualizados: list, stats, ranking, etc.
        try:
            if self.new: print("\nDigite comando (list, stats, ranking, desafiar <nome>, aleatorio, aceitar <nome>, negar <nome>, sair): ", end="",flush=False)

            try:
                raw = self.input_queue.get(timeout=0.3)
            except queue.Empty:
                self.event_queue.put(EventoMenu(False))
                return
            
            cmd = raw.strip()

            if cmd:

                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:]

                #LIST
                if command == 'list':
                    self.server.list()

                #STATS
                elif command == 'stats':
                    self.server.stats()


                #RANKING
                elif command == 'ranking':
                    self.server.ranking()


                #DESAFIAR / ALEATORIO / ACEITAR 
                elif command in ['desafiar', 'aleatorio', 'aceitar']:
                    self.challenge_manager.handler(command, args[0])


                #NEGAR
                elif command == 'negar':
                    if not args:
                        logging.warning("Uso: negar <nome>")
                        
                    else: self.challenge_manager.reject(args[0])



                #SAIR
                elif command == 'sair':
                    logging.info("Saindo...")
                    self.server.close()
                    context.event_manager.can_run = False
                    return



                #Comando no terminal
                elif command == 'cmd_leave_menu':
                    return



                #INVÁLIDO
                else:
                    logging.info("Comando inválido")



        except:
            print("Erro de comunicação com o servidor, encerrando...")
            logging.debug("Erro ocorreu", exc_info=True)
            try:
                self.server.close()
                return
            except:
                return

            
class EventoBatalha(Evento):
    def __init__(self, oponent_client, my_pokemon, dial):
        self.oponent_client = oponent_client
        self.my_pokemon = my_pokemon
        self.dial = dial
        

    def start(self, context):
        self.playerinfo = context.playerinfo
        self.challenge_manager = context.challenge_manager
        self.input_queue = context.input_queue
        self.server = context.server

        context.battle_started.set()

        #Sair do menu do desafiante que está esparando
        

        batalha = Battle(self.oponent_client, context, self.my_pokemon, dial=self.dial)

        if batalha.prepare(): batalha.loop()
        context.battle_started.clear()
        
        #self.event_queue.put(self.EventoMenu())
