
import logging
import threading
import queue
import time
from rede.comunicacaoPlayer import OpponentClient

#gerenciador da fila de aceitar ou enviar desafios
    #ela que vai chamaro processo que faz toda preparação da batalha

class ChallengesManager:
    def __init__(self, context):
        self.timeout_request = 50  # segundos do timeout aceitar ou não o desafio
        self.server = context.server
        self.playerinfo = context.playerinfo
        self.network = context.network


        self.enviados = {}
        self.recebidos = {}

        self.input_queue = context.input_queue
        self.pokedex = context.pokedex

        self.event_queue = context.event_queue

        self.battle_started = context.battle_started
 

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



    #cada desafio enviado é uma thread que só fica esperando resposta até um timeout
    def add_send(self, opp, my_pokemon):
        desafio_id = f"{self.playerinfo.my_name}-{opp['name']}"
        queue_resposta_desafio = queue.Queue()
        self.enviados[desafio_id] = (queue_resposta_desafio)
        opp_conn = OpponentClient(opp,self.playerinfo,self.battle_started,self.event_queue, self.network)
        t = threading.Thread(target=opp_conn.enviar_desafio, args=(queue_resposta_desafio,my_pokemon), daemon=True)
        t.start()


    #Isso aqui é chamado lá pelo UDP Handler
    def receive_challenge(self, opp):
        logging.info("Desafio recebido de %s", opp['name'])
        opp["hora"] = time.time()
        self.recebidos[opp['name']] = opp


    #Aqui é chamado do comando "aceitar" da main
    def accept(self, opp, my_pokemon):
        if not self.recebidos.get(opp['name']):
            logging.info("Nenhum desafio de %s", opp['name']); return
        
        opp = self.recebidos.pop(opp['name'])
        if time.time() - opp["hora"] > self.timeout_request:
            logging.info("Desafio de %s já expirou", opp)
            return
            
        opp_conn = OpponentClient(opp,self.playerinfo,self.battle_started,self.event_queue, self.network)
        opp_conn.enviar_aceitar_desafio(my_pokemon)


    #Rjeita, só para quem enviou não ficar esperando
    def reject(self, opp_name):
        if not self.recebidos.get(opp_name):
            logging.info("Nenhum desafio de %s", opp); return
        opp = self.recebidos.pop(opp_name)
        OpponentClient.enviar_rejeitar(self.playerinfo.my_name, self.network, opp)
       
