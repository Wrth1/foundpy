from .util import *
from .config import *
from .contract import *

class Forge():
    def __init__(self):
        pass

    @call_check_setup
    def init(self):
        print("Warning: You do not need to call forge.init, you can immediately use forge.create instead")
        return None
    
    @call_check_setup
    def create(self, file, *args, value=0, import_remappings=DEFAULT_REMAPPINGS):
        deployed = deploy_contract(file, *args, value=value, import_remappings=import_remappings).address
        return deployed