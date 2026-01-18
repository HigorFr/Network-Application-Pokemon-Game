from abc import ABC, abstractmethod
import time, queue, logging
from game.battle import Battle

class Evento(ABC):

    @abstractmethod
    def start(self, context):      
        pass



class EventoMenu(Evento):    
    def start(self, context):
        self.playerinfo = context.playerinfo
        self.challenge_queue = context.challenge_queue
        self.input_queue = context.input_queue
        self.server = context.server
        self.event_queue = context.event_queue

        
        # Loop principal com comandos atualizados: list, stats, ranking, etc.
        try:
            while True:

                print(
                    "\nDigite comando (list, stats, ranking, desafiar <nome>, aleatorio, aceitar <nome>, negar <nome>, sair): ",
                    end="",
                    flush=False
                )

                try:
                    raw = self.input_queue.get()
                except (queue.Empty, KeyboardInterrupt):
                    continue


                cmd = raw.strip()
                if not cmd:
                    continue

                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:]

                # ======== LIST ========
                if command == 'list':
                    if(self.server.list() == 0): continue

                # ======== STATS ========
                elif command == 'stats':
                    self.server.stats()


                # ======== RANKING ========
                elif command == 'ranking':
                    self.server.ranking()


                # ======== DESAFIAR / ALEATORIO / ACEITAR ========
                elif command in ['desafiar', 'aleatorio', 'aceitar']:
                    self.challenge_queue.handler(command, args[0])


                # ======== NEGAR ========
                elif command == 'negar':
                    if not args:
                        logging.warning("Uso: negar <nome>")
                        continue
                    self.challenge_queue.reject(args[0])



                # ======== SAIR ========
                elif command == 'sair':
                    logging.info("Saindo...")
                    break




                # ======== INVÁLIDO ========
                else:
                    logging.info("Comando inválido")

            if not self.challenge_queue.get_battle_started(): self.event_queue.put(self.EventoMenu())

        except:
            print("Erro de comunicação com o servidor, encerrando...")

        finally:
            try:
                self.server.close()
                return
            except:
                return

            
class EventoBatalha(Evento):
    def __init__(self, oponent_client, my_pokemon):
        self.oponent_client = oponent_client
        self.my_pokemon = my_pokemon

    def start(self, context):
        self.playerinfo = context.playerinfo
        self.challenge_queue = context.challenge_queue
        self.input_queue = context.input_queue
        self.server = context.server

        context.battle_started.set()
        batalha = Battle(self.oponent_client, context, self.my_pokemon, dial=True)
        if batalha.prepare(): batalha.loop()
        self.battle_started.clear()
        
        self.event_queue.put(self.EventoMenu())
