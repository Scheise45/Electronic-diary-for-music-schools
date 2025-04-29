

import creat_db
import dataclass
from threading import Thread
class Sheldure:
    def __init__(self):
        Thread(target=self.saver).start()

    def saver(self):
        
