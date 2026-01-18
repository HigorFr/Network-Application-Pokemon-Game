import socket, threading, json, logging, time
from rede.crypto import Crypto
from utils import Utils


#O coração da comunicação, basciamente o nível mais baixo do projeto
    #Aqui é onde os sockets são de fato usado, o resto do projeto abstrai usando as funções daqui
class Network:
    def __init__(self, udp_broadcast_port):
        self.crypto = Crypto();
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_broadcast_port = udp_broadcast_port
        self.BUFFER_SIZE = 4096
 

        self.start_udp_listener(self.udp_handler)

  
    #Isso aqui são só funções auxiliares para colocar linhas dentro de um socket qualquer
    @staticmethod
    def send_line(sock, data):
        sock.sendall(data + b"\n")

    @staticmethod
    def recv_line(fileobj):
        line = fileobj.readline()
        if not line:
            return None
        return line.strip()


    @staticmethod
    def send_json(sock, obj):
        """Envia um objeto JSON e retorna True em caso de sucesso, False se a conexão falhar."""
        try:
            line = (json.dumps(obj) + "\n").encode()
            sock.sendall(line)
            return True
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            return False

    
    #recv_json agora lida com erros de forma mais robusta
    @staticmethod
    def recv_json(sock):
        """Recebe um objeto JSON e retorna None se a conexão falhar."""
        buf = b""
        sock.settimeout(5.0)  #adiciona timeout para evitar bloqueio eterno
        try:
            while True:
                ch = sock.recv(1)
                if not ch:
                    return None  #Conexão fechada
                if ch == b"\n":
                    break
                buf += ch
        except (ConnectionAbortedError, ConnectionResetError, OSError, socket.timeout):
            return None
        finally:
            sock.settimeout(None)  #Remove o timeout
        try:
            return json.loads(buf.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None













    @staticmethod
    def udp_send(self, obj, ip='255.255.255.255', port=None):
        if port is None:
            port = self.udp_broadcast_port
        data = json.dumps(obj).encode()
        self.udp_sock.sendto(data, (ip, port))
        logging.debug(f"Enviado {data} para {ip}:{port} ")

    @staticmethod
    def p2p_listen(self, port, backlog=1, timeout=None):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("0.0.0.0", port))
        listener.listen(backlog)
        if timeout is not None:
            listener.settimeout(timeout)
        socket, addr = listener.accept()
        logging.info(f"P2P: conexão aceita {addr}")
        try:
            listener.close()
        except Exception:
            pass
        return socket

    @staticmethod
    def p2p_connect(self, ip, port, timeout=5.0):
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.settimeout(timeout)
        socket.connect((ip, port))
        logging.info(f"P2P: conectado a {(ip, port)}")
        socket.settimeout(None)
        return socket

   


    #Roda em uma thread separada para enviar mensagens periódicas ao servidor e manter a conexão viva.
    def send_keepalive(sock, queue):
        while True:
            time.sleep(20) #Envia a cada 20 segundos (Foi usado mais para teste, mas o tempo poderia ser menor)
            if not queue.get_battle_started():    
                try:
                    
                    logging.debug("Enviado Keep alive.")
                    if Network.send_json(sock, {"cmd": "KEEPALIVE"}): continue;
                        
                    else:
                        logging.debug("Falha ao enviar keepalive.")
                        queue.put("erro")
                        break

                except Exception:
                        logging.debug("Falha ao enviar keepalive.")
                        queue.put("erro")
                        break


class Udp_handler:

    def __init__(self,player_name, challenge_manager):
        self.player_name = player_name
        self.challenge_manager = challenge_manager
        

    #UDP ta sempre ligado, tratando o que recebe pela função UDP_handler
    def start_udp_listener(self, handler):
        def _listen():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            s.bind(("0.0.0.0", self.udp_broadcast_port))
            logging.info(f"UDP listener rodando na porta {self.udp_broadcast_port}")

        
            while True:
                try:
                    data, addr = s.recvfrom(self.BUFFER_SIZE)
                    try:
                        msg = json.loads(data.decode())
                        handler(msg, addr)

                    except json.JSONDecodeError:
                        logging.debug("Recebeu UDP inválido")

                except Exception as e:
                    logging.exception("Erro no UDP listener: %s", e)
                    break

        t = threading.Thread(target=_listen, daemon=True)
        t.start()    
  
    
    #Gerenciador do que ele receber de UDP (vai ser jogado na thread)
    def udp_handler(self, msg, addr):
        try:
            #apagar
            t = msg.get('type')
            if t == 'DES':
                opp = msg.get('opponent')
                if opp['name'] == self.player_name:
                    return  # Ignora desafios para si mesmo
                opp['ip'] = addr[0]
                self.challenge_manager.receive_challenge(opp)

            elif t == 'EVENT':
                sub = msg.get('sub')
                if sub == 'JOIN':
                    joined_name = msg.get('name')
                    logging.info(f"O jogador {joined_name} entrou no servidor.")

                elif sub == 'LEAVE':
                    joined_name = msg.get('name')
                    logging.info(f"O jogador {joined_name} saiu do servidor.")

            elif t == 'RES':
                opp_name = msg.get('opp')
                desafio_id = f"{self.player_name}-{opp_name}"
                q = self.challenge_manager.enviados.get(desafio_id)
                if q:
                    q.put(msg)
        except Exception:
            logging.exception("Erro tratando mensagem UDP")