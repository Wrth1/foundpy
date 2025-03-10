from .util import *
from .config import *

@check_setup_on_create
class Account:
    def __init__(self, account=None, privkey=None) -> None:
        if privkey:
            self.account = config.w3.eth.account.from_key(privkey)
        else:
            self.account = account
        self.address = self.account.address

    def send(self, to, value):
        tx = {
            "from": self.address,
            "to": to,
            "value": value
        }
        tx_hash = config.w3.eth.send_transaction(tx)
        return tx_hash
    
    def get_balance(self):
        return get_balance(self.address)

@check_setup_on_create
class Contract:
    def __init__(self, addr, file=None, abi=None, import_remappings={}) -> None:
        addr = Web3.to_checksum_address(addr)
        self.file = file
        self.address = addr
        self.abi = None
        self.import_remappings = import_remappings
        if abi:
            self.abi = abi
            self.contract = config.w3.eth.contract(addr, abi=abi)
        elif file:
            self.abi = self.get_abi()
            self.contract = config.w3.eth.contract(addr, abi=self.abi)
        
    def call(self, func_name, *args):
        if self.abi:
            return getattr(self.contract.functions, func_name)(*args).call()
        else:
            function_selector = calculate_function_selector(func_name)
            encoded_args = encode_arguments(func_name, *args)
            data = function_selector + encoded_args
            tx = {
                "from": config.wallet.address,
                "to": self.address,
                "data": data
            }
            return config.w3.eth.call(tx)
    
    def code(self):
        return config.w3.eth.get_code(self.address)
    
    def codesize(self):
        return len(self.code())

    def send(self, func_name, *args, value=0, gas_limit=None):
        if func_name == "":
            return config.wallet.send(self.address, value)
        tx = {
            "value": value,
            "nonce": config.w3.eth.get_transaction_count(config.wallet.address),
            "gasPrice": config.w3.eth.gas_price,
            "chainId": config.w3.eth.chain_id
        }
        if gas_limit:
            tx["gas"] = gas_limit
            
        if self.abi:
            tx = getattr(self.contract.functions, func_name)(*args).build_transaction(tx)
        else:
            function_selector = calculate_function_selector(func_name)
            encoded_args = encode_arguments(func_name, *args)
            data = function_selector + encoded_args
            tx.update({
                "from": config.wallet.address,
                "to": self.address,
                "data": data,
                "value": value,
            })
            tx["gas"] = config.w3.eth.estimate_gas(tx)
        
        # tx_hash = config.w3.eth.send_transaction(tx)
        signed_tx = config.w3.eth.account.sign_transaction(tx, config.privkey)
        tx_hash = config.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash
        
    def storage(self, slot):
        return config.w3.eth.get_storage_at(self.address, slot)

    def get_abi(self):
        return compile_file(self.file, self.import_remappings)['abi']
    
    def get_balance(self):
        return get_balance(self.address)
    
    def storage_layout(self):
        if not self.file:
            raise Exception("No file provided for storage layout.")
        return compile_file(self.file, self.import_remappings)['storage-layout']
    
    def get_private_variable_offset(self, name) -> int:
        storage_layout = self.storage_layout()
        for variable in storage_layout['storage']:
            if variable['label'] == name:
                return variable['offset']
        raise Exception(f'Variable {name} not found in storage layout.')
    
    @classmethod
    def deploy_contract(cls, file, *args, value=0, import_remappings={}):
        contract = deploy_contract(file, *args, value=value, import_remappings=import_remappings)
        return cls(contract.address, file=contract.file, abi=contract.abi, import_remappings=contract.import_remappings)

@call_check_setup
def deploy_contract(file, *args, value=0, import_remappings={}):
    compiled_sol = compile_file(file, import_remappings)
    abi = compiled_sol['abi']
    bytecode = compiled_sol['bin']
    contract = config.w3.eth.contract(abi=abi, bytecode=bytecode)
    # tx_hash = contract.constructor(*args).transact({"from":config.wallet.address, "value":value})
    tx = contract.constructor(*args).build_transaction({
        "from": config.wallet.address,
        "value": value,
        "nonce": config.w3.eth.get_transaction_count(config.wallet.address),
        "gasPrice": config.w3.eth.gas_price,
        "chainId": config.w3.eth.chain_id
    })
    tx["gas"] = config.w3.eth.estimate_gas(tx)
    signed_tx = config.w3.eth.account.sign_transaction(tx, config.privkey)
    tx_hash = config.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = config.w3.eth.wait_for_transaction_receipt(tx_hash)
    contract = Contract(tx_receipt.contractAddress, file, abi)
    return contract