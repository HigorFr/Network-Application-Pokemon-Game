import logging, threading, queue, time, sys, queue
from rede.network import Network
from rede.comunicacaoServer import ServerClient
from rede.challengesManager import ChallengesManager
from leitor import Leitor
from game.pokemonDB import PokemonDB
from utils import Utils
from eventManager import EventManager, EventQueue
from rede.network import Udp_handler
#Obs: muita coisa a gente jogou aqui na main por questões de facilidade, mesmo que n seja uma boa prática (que bom que n é um trabalho de engenharia de software)

#Como o código ficou grande, alguns comentarios foi o GPT que fez para evitar ficar descrevendo muita coisa

#Foram no total +60 commits no github



#logging.basicConfig(level=logging.INFO, format='\n[%(levelname)s] %(message)s')

#Para mudar o para debug só descomentar isso
logging.basicConfig(level=logging.DEBUG, format='\n[%(levelname)s] %(message)s')



class PlayerInfo:
    def __init__(self, my_name, p2p_port, udp_port):
        self.my_name = my_name
        self.p2p_port = p2p_port
        self.udp_port = udp_port



class GameContext:
    def __init__(self, playerinfo, network, server, pokedex, input_queue):
        self.playerinfo = playerinfo
        self.network = network
        self.server = server
        self.pokedex = pokedex
        self.input_queue = input_queue
        self.battle_started = threading.Event()
        self.event_queue = EventQueue()
        self.challenge_manager = ChallengesManager(self)
        self.event_manager = EventManager(self)

def main():
    
    #inputs automaticos (seja pelo arquivo ou depois pelo input)
    print("Uso fácil: python client.py <meu_nome> <ip_server> <porta_server> <minha_porta_udp> <minha_porta_tcp>")
    my_name = sys.argv[1] if len(sys.argv) > 1 else input("Seu nome: ").strip()
    server_ip = sys.argv[2] if len(sys.argv) > 2 else Utils.input_default("IP do servidor (Vazio para 127.0.0.1)", "127.0.0.1")
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else int(Utils.input_default("Porta do servidor (Vazio para 5000)", "5000"))
    udp_port = int(sys.argv[4]) if len(sys.argv) > 4 else int(Utils.input_default("Porta UDP (Vazio para 5001)", "5001"))
    p2p_port = int(sys.argv[5]) if len(sys.argv) > 5 else int(Utils.input_default("Porta P2P (Vazio para 7000)", "7000"))



    player = PlayerInfo(my_name, p2p_port, udp_port)
    network = Network(udp_broadcast_port=udp_port)
    server = ServerClient(player,server_ip, server_port, network.crypto.public_key_b64())
    pokedex = PokemonDB()

    input_queue = queue.Queue()
    input_reader = Leitor(input_queue)
    input_reader.start()

    
    
    context = GameContext(player, network, server, pokedex, input_queue)
    Udp_handler(player.my_name, context.challenge_manager, player.udp_port)

    context.event_manager.run()


if __name__ == '__main__':
    main()



