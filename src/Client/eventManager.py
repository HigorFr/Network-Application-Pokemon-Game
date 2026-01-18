import logging, time, queue, threading
from rede.challengesManager import ChallengesManager
import event


class EventQueue:
    def __init__(self):
        self.event_queue = queue.Queue()

    def put(self, evento: event.Evento ):
        self.event_queue.put(evento)

    def get(self) -> event.Evento:
        return self.event_queue.get()
        



class EventManager:
    def __init__(self,context):
        self.context = context

        #Desempacota
        self.playerinfo = context.playerinfo
        self.challenge_queue = context.challenge_queue
        self.input_queue = context.input_queue
        self.server = context.server       
        self.battle_started = context.battle_started
        self.event_queue = context.event_queue
 


        self.event_queue.put(event.EventoMenu())
        self.eventhandler()


    #gerenciador da fila
    def evenhandler(self):
        event = self.event_queue.get()
        event.start(self.context)




            
            

        
        
        
        
        
        
        
        
        
        
        

