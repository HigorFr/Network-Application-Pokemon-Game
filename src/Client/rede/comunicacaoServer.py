import socket
import threading
import logging
from queue import Queue
from rede.network import Network



#Isso aqui é só uma camada a mais de abstração para comunicações diretas com o servidor, tudo bem autoexplicativo

class ServerClient:
    def __init__(self, playerinfo, server_ip, server_port, pk_b64):
        self.server_ip = server_ip
        self.server_port = server_port
        self.playerinfo = playerinfo
        self.pk_b64 = pk_b64

        try:
            self.server_sock = self.register(self.playerinfo.my_name, self.playerinfo.p2p_port, self.playerinfo.udp_port)
        except Exception:
            logging.info("Erro, tente colocar um servidor válido")
            logging.debug("Erro ocorreu", exc_info=True)
            raise Exception
            

        #Inicia Keepalive
        keepalive_queue = Queue()
        threading.Thread(target=Network.send_keepalive, args=(self.server_sock,), daemon=True).start()



    def register(self, name, p2p_port, udp_port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((self.server_ip, self.server_port))

        except (ConnectionRefusedError, socket.gaierror) as e:
            logging.info("Não foi possível conectar ao servidor")
            s.close() 
            raise


        if not Network.send_json(s, {
            "cmd": "REGISTER",
            "name": name,
            "p2p_port": p2p_port,
            "udp_port": udp_port,
            "public_key": self.pk_b64
        }):
            logging.error("Falha ao enviar registro para o servidor.")
            return None

        resp = Network.recv_json(s)
        if not resp or resp.get("type") != "OK":
            logging.error("Falha ao registrar no servidor: %s", resp)
            s.close()
            return None

        logging.info("Registrado no servidor com sucesso")
        return s

    
    def list(self):
        if not Network.send_json(self.server_sock, {"cmd": "LIST"}):
            logging.error("Falha ao enviar comando LIST para o servidor")
            return 0;

        resp = Network.recv_json(self.server_sock)
        if resp and resp.get("type") == "LIST":
            players = resp.get("players", [])
            if players:
                print("\n--- Jogadores Online ---")
                for player in players:
                    print(f"  {player}")
                print("-------------------------")
            else:
                print("\nNão há jogadores online no momento.")
        else:
            logging.error("Resposta inválida do servidor para LIST: %s", resp)


    def stats(self):
        Network.send_json(self.server_sock, {"cmd": "GET_STATS"})
        resp = Network.recv_json(self.server_sock)
        if resp and resp.get("type") == "STATS":
            print(f"\n--- Suas Estatísticas ---")
            print(f"  Vitórias: {resp.get('wins', 0)}")
            print(f"  Derrotas: {resp.get('losses', 0)}")
            print(f"-------------------------")
        else:
            print("Erro ao obter estatísticas:", resp)


    def ranking(self):
        Network.send_json(self.server_sock, {"cmd": "RANKING"})
        resp = Network.recv_json(self.server_sock)
        if resp and resp.get("type") == "RANKING":
            print("\n--- Ranking de Jogadores (por Vitórias) ---")
            for i, player in enumerate(resp.get("ranking", []), 1):
                print(f"  {i}. {player['name']} - Vitórias: {player['wins']}, Derrotas: {player['losses']}")
            print(f"-------------------------------------------")
        else:
            print("Erro ao obter ranking:", resp)


    def close(self):
        self.server_sock.close()


    #O random, não é nada mais que a mensagem do match sem o argumento de target
    #o servidor fica responsavel de enviar para alguem aleaorio
    def match(self, target=None):
        cmd = "CHALLENGE" if target else "MATCH_RANDOM"
        if not Network.send_json(self.server_sock, {"cmd": cmd, "target": target}):
            return None

        resp = Network.recv_json(self.server_sock)
        if not resp:
            return None

        if resp.get("type") == "MATCH":
            return resp["opponent"]

        if resp.get("type") == "ERR":
            logging.error("Erro do servidor: %s", resp.get("msg"))
            return None

        return None


    def send_match_won(self, opponent):
        Network.send_json(self.server_sock, {
            "cmd": "RESULT", 
            "me": self.playerinfo.my_name, 
            "opponent": opponent, 
            "winner": self.playerinfo.my_name
        })
        Network.recv_json(self.server_sock) # Espera a confirmação do servidor