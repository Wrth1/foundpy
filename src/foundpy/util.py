import re
from .config import *

def compile_file(filename, import_remappings={}):
    splittedfile = filename.split(":")
    if len(splittedfile) > 1:
        filename = splittedfile[0]
        contract_name = splittedfile[1]
    else:
        contract_name = None
    compiled_sol = solcx.compile_source(open(filename).read(), solc_version=config.solc_version ,output_values=['abi', 'bin', 'storage-layout'], import_remappings=import_remappings)
    possible_contract = []
    if contract_name:
        for contract_id, contract_interface in compiled_sol.items():
            if contract_id == f"<stdin>:{contract_name}":
                return contract_interface
    else:
        for contract_id, contract_interface in compiled_sol.items():
            if "<stdin>:" in contract_id:
                possible_contract.append(contract_id)

    assert len(possible_contract) != 0, f"Contract {contract_name} not found in file: {filename}"
    assert len(possible_contract) == 1, f"Multiple contract found in file: {possible_contract}, please specify contract name"
    return compiled_sol[possible_contract[0]]

def calculate_function_selector(function_signature):
    """
    Calculate the function selector for a function signature
    Automatically changes uint to uint256 and int to int256
    """
    function_signature = re.sub(r"\buint\b", "uint256", function_signature)
    function_signature = re.sub(r"\bint\b", "int256", function_signature)
    return Web3.keccak(text=function_signature)[:4]

def encode_arguments(function_signature, *args):
    assert function_signature.count("(") == 1 and function_signature.count(")") == 1, "Invalid function signature"
    if "()" in function_signature:
        types = []
    else:
        types = function_signature.split("(")[1].split(")")[0].split(",")
    assert len(types) == len(args), "Length of types and number of arguments mismatch"
    return encode_abi(types, args)

def ether(x):
    return x * 10**18

@call_check_setup
def get_age(block_number):
    return get_block(block_number)["timestamp"]

@call_check_setup
def get_balance(addr):
    balance = config.w3.eth.get_balance(addr)
    return balance

@call_check_setup
def get_block(block_number):
    return config.w3.eth.get_block(block_number)

@call_check_setup
def get_tx(tx_hash):
    return config.w3.eth.get_transaction(tx_hash)