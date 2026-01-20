import logging, time, queue, threading
from rede.challengesManager import ChallengesManager
from event import EventoMenu, Evento


class EventQueue:
    def __init__(self):
        self.event_queue = queue.Queue()

    def put(self, evento: Evento ):
        self.event_queue.put(evento)

    def get(self) -> Evento:
        return self.event_queue.get()
        
    def is_empty(self) -> bool:
        return self.event_queue.empty()


class EventManager:
    def __init__(self,context):
        self.context = context

        #Desempacota
        self.playerinfo = context.playerinfo
        self.challenge_manager = context.challenge_manager
        self.input_queue = context.input_queue
        self.server = context.server       
        self.battle_started = context.battle_started
        self.event_queue = context.event_queue
        self.can_run = True

    def run(self):
        self.eventhandler()
        


    #gerenciador da fila
    def eventhandler(self):
        while self.can_run:
            if self.event_queue.is_empty(): self.event_queue.put(EventoMenu(True))
            event = self.event_queue.get()
            event.start(self.context)




            
            

        
        
        
        
        
        
        
        
        
        
        

