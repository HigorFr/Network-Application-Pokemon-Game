import logging
import queue
import event
from rede.crypto import Crypto
from utils import Utils
from game.battle import Battle
from rede.network import Network

class OpponentClient:
        #Envia desafio e espera resposta


    def __init__(self, opp, playerinfo, battle_started, event_queue, network):
        self.opp = opp
        self.battle_started = battle_started
        self.event_queue = event_queue
        self.network = network
        self.fileobj = None
        self.shared_key = None
        self.playerinfo = playerinfo
        self.timeout_request = 20

    def enviar_desafio(self, queue_resposta_desafio, my_pokemon):
            
        if self.battle_started.is_set(): return
        op_name = self.opp['name']
        dest_udp_port =  self.opp['udp_port']
        msg = { "type": "DES", "opponent": { "name": self.playerinfo.my_name, "ip": None, "udp_port": self.playerinfo.udp_port, "p2p_port": self.playerinfo.p2p_port, "public_key": self.network.crypto.public_key_b64() } }
        
        try:
            self.network.udp_send(msg, ip= self.opp.get('ip', '255.255.255.255'), port=dest_udp_port)
            logging.info("Desafio enviado para %s", op_name)

        except Exception as e:
            logging.error("Falha ao enviar desafio: %s", e)
            return
        
        
        #Caso de timeout
        try:
            resposta = queue_resposta_desafio.get(timeout=self.timeout_request)
        except queue.Empty:
            if self.battle_started.is_set(): return
            self.battle_started.clear()
            logging.info("Timeout aguardando resposta de %s", op_name); return


        if self.battle_started.is_set(): return
            
        if resposta and resposta.get('res') == 'ACE':
            logging.info("%s aceitou. Iniciando batalha.", op_name)

            self.event_queue.put(event.EventoBatalha(self, my_pokemon, True))
            
            
        else:
            logging.info("%s recusou o desafio.", op_name)





    def enviar_aceitar_desafio(self, my_pokemon):
        res = {"type": "RES", "opp": self.playerinfo.my_name, "res": "ACE"}
        self.network.udp_send(res, ip= self.opp.get('ip', '255.255.255.255'), port= self.opp.get('udp_port', self.playerinfo.udp_port))
        logging.info("Aceitei desafio de %s",  self.opp['name'])


        #Isso aqui Passa os nomes dos jogadores para a classe Battle
        #Observa que ele já prepara a batalha depois de aceitar, mesmo se quem tiver desafiado a batalha já tiver iniciado com outra pessoa
            #Nesse caso quem enviou vai ficar esperando sem respota até dar timeout e acabar a batalha, dava para arrumar isso fazendo uma nova mensagem (tipo ack) que volta de quem desafiou para confirmar
        
        self.event_queue.put(event.EventoBatalha(self, my_pokemon, False))




    def connect(self, dial):
        if dial:
            conn = Network.p2p_connect(self.opp['ip'], int(self.opp['p2p_port']))
        
        else:
            conn = Network.p2p_listen(self.playerinfo.p2p_port, backlog=1, timeout=10)
        if not conn: return False

        self.fileobj = conn.makefile("rwb")
        self.shared_key = self.network.crypto.shared_key(self.opp['public_key'])
        self.conn = conn
        logging.debug(f"Shared key e troca de Pokémon feitos com sucesso: { self.shared_key }")



    def trade_pokemon_info(self, my_pokemon):
        my_choice_msg = Crypto.encrypt_json(self.shared_key, {"type": "POKEMON_CHOICE", "name": my_pokemon.name})
        Network.send_line(self.conn, my_choice_msg.encode())

        self.conn.settimeout(10.0)
        opp_choice_line = Network.recv_line(self.fileobj)
        if not opp_choice_line:
            logging.error("Conexão P2P perdida ao receber escolha do oponente.")
            return False
        
        opp_choice_msg = Crypto.decrypt_json(self.shared_key, opp_choice_line.decode())

        if not opp_choice_msg or opp_choice_msg.get("type") != "POKEMON_CHOICE":
            logging.error("Falha ao receber a escolha de Pokémon do oponente."); return False

        opp_pokemon_name = opp_choice_msg.get("name")
        
        return opp_pokemon_name


    #aqui ele utiliza a criptografia para enviar os json
    def send_encrypted(self, obj):
        assert self.shared_key is not None
        msg = Crypto.encrypt_json(self.shared_key, obj).encode()
        Network.send_line(self.conn, msg)

    def recv_encrypted(self):
        assert self.shared_key is not None
        line = Network.recv_line(self.fileobj)
        if line is None: return None
        return Crypto.decrypt_json(self.shared_key, line.decode())





    def send_move(self, move):
        self.send_encrypted({"type": "MOVE", "name": move})



    @staticmethod
    def enviar_rejeitar(my_name,network,opp):
        res = {"type": "RES", "opp": my_name, "res": "NEG"}
        network.udp_send(res, ip=opp.get('ip', '255.255.255.255'), port=opp.get('udp_port'))
        logging.info("Recusei desafio de %s", opp['name'])







        