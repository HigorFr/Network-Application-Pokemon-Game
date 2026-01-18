
import logging
import threading
import queue
import time
from comunicacaoPlayer import OpponentClient

#gerenciador da fila de aceitar ou enviar desafios
    #ela que vai chamaro processo que faz toda preparação da batalha

class ChallengesManager:
    def __init__(self, server, playerinfo, network,input_queue, pokedex):
        self.timeout_request = 50  # segundos do timeout aceitar ou não o desafio
        self.server = server
        self.playerinfo = playerinfo
        self.network = network


        self.enviados = {}
        self.recebidos = {}

        self.input_queue = input_queue
        self.pokedex = pokedex


    def setEventQueue(self, event_queue):
        self.event_queue = event_queue

    def setBattleStarted(self, battle_started):
        self.battle_started = battle_started




    def handler(self, command, target = None):
        if command in ['desafiar', 'aceitar']:
            if not target:
                logging.warning(f"Uso: {command} <nome>")
                return 0;

            if target == self.playerinfo.my_name:
                logging.warning("Você não pode se desafiar.")
                return 0;
            opp_info = self.server.match(target=target)


        elif command == 'aleatorio':
            opp_info = self.server.match()


        if opp_info:
            my_pokemon = self.pokedex.choose_pokemon(self.input_queue)

            if not my_pokemon:
                return 0;
            if command == 'aceitar':
                self.accept(opp_info, my_pokemon)
            else:
                self.add_send(opp_info, my_pokemon)
        else:
            logging.warning("Não foi possível encontrar um oponente.")




    def get_battle_started(self):
        return self.battle_started.is_set() #Isso aqui é algo que aprendemos em SO para evitar conflito de thread, é um mutex para não iniciar outra batalha enquanto outra está ativa (aulas do norton valeram a pena)


    #cada desafio enviado é uma thread que só fica esperando resposta até um timeout
    def add_send(self, opp, my_pokemon):
        desafio_id = f"{self.my_name}-{opp['name']}"
        queue_resposta_desafio = queue.Queue()
        self.enviados[desafio_id] = (queue_resposta_desafio)
        opp_conn = OpponentClient(opp,my_pokemon,self.event_queue, self.network)
        t = threading.Thread(target=opp_conn.enviar_desafio, args=(queue_resposta_desafio,), daemon=True)
        t.start()


    #Isso aqui é chamado lá pelo UDP Handler
    def receive_challenge(self, opp):
        logging.info("Desafio recebido de %s", opp['name'])
        opp["hora"] = time.time()
        self.recebidos[opp['name']] = opp


    #Aqui é chamado do comando "aceitar" da main
    def accept(self, opp_name, my_pokemon):
        if opp_name not in self.recebidos:
            logging.info("Nenhum desafio de %s", opp_name); return
        opp = self.recebidos.pop(opp_name)
        if time.time() - opp["hora"] > self.timeout_request:
            self.recebidos.pop(opp_name)
            logging.info("Desafio de %s expirou", opp_name)
            return
            
        opp_conn = OpponentClient(opp,my_pokemon,self.event_queue, self.network)
        opp_conn.enviar_aceitar_desafio()


    #Rjeita, só para quem enviou não ficar esperando
    def reject(self, opp_name):
        if opp_name not in self.recebidos:
            logging.info("Nenhum desafio de %s", opp_name); return
        opp = self.recebidos.pop(opp_name)
        OpponentClient.enviar_rejeitar(self.playerinfo.myname, self.network, opp)
       
