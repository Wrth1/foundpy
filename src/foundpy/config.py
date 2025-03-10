import solcx
from web3 import Web3, HTTPProvider
from eth_abi import encode as encode_abi

is_warned = False

class Config():
    def __init__(self) -> None:
        self.rpc_url = None
        self.privkey = None
        self.w3 = None
        self.wallet = None
        self.is_setup = False

        latest_solc_version = solcx.get_installed_solc_versions()
        if latest_solc_version == []:
            print("solcx's solc not found, installing solc")
            solcx.install_solc()
            latest_solc_version = solcx.get_installed_solc_versions()

        solcx.set_solc_version(latest_solc_version[0])
        self.solc_version = latest_solc_version[0]

    def setup(self, rpc_url, privkey):
        self.is_setup = True
        self.rpc_url = rpc_url
        self.privkey = privkey
        self.w3 = Web3(HTTPProvider(rpc_url))
        from .contract import Account
        self.wallet = Account(self.w3.eth.account.from_key(privkey))
        self.w3.eth.default_account = self.wallet.address

    def change_solc_version(self, version):
        if version == "latest":
            version = solcx.get_installed_solc_versions()[0]
        solcx.install_solc(version)
        solcx.set_solc_version(version)
        self.solc_version = version

    def from_tcp1p(self, address):
        import base64
        import struct
        import requests
        from tqdm import trange
        try:
            self.tcp1p_session
        except:
            self.tcp1p_session = requests.Session()

        session = self.tcp1p_session

        VERSION = "s"
        MOD = 2 ** 1279 - 1
        EXP = 2 ** 1277

        self.tcp1p_url = address
        response = session.get(self.tcp1p_url + "/kill")
        if response.status_code == 200:
            print("session already found, skipping PoW...")
            response = session.get(self.tcp1p_url + "/launch")
            resp_json = response.json()
        else:
            response = session.get(self.tcp1p_url + "/challenge")
            challenge = response.json()["challenge"]
            print("solving PoW:", challenge)
            parts = challenge.split(".", 2)
            d_bytes = base64.standard_b64decode(parts[1])
            d = struct.unpack(">I", d_bytes)[0]
            x_bytes = base64.standard_b64decode(parts[2])
            x = int.from_bytes(x_bytes, byteorder="big")

            for _ in trange(d):
                x = pow(x, EXP, MOD)
                x ^= 1
            x_bytes = int.to_bytes(x, (x.bit_length()+7)//8, byteorder="big")
            print("PoW done")
            solution = f"{VERSION}.{base64.standard_b64encode(x_bytes).decode()}"

            response = session.post(self.tcp1p_url + "/solution", json={"solution": solution})
            response = session.get(self.tcp1p_url + "/launch")
            resp_json = response.json()
            
        resp_json['1']['RPC Endpoint'] = resp_json['1']['RPC Endpoint'].replace('{ORIGIN}', self.tcp1p_url)

        uuid = resp_json['0']['UUID']
        rpc_endpoint = resp_json['1']['RPC Endpoint']
        private_key = resp_json['2']['Private Key']
        setup_contract = resp_json['3']['Setup Contract']
        wallet = resp_json['4']['Wallet']
        message = resp_json['message']

        print(f"UUID: {uuid}")
        print(f"RPC Endpoint: {rpc_endpoint}")
        print(f"Private Key: {private_key}")
        print(f"Setup Contract: {setup_contract}")
        print(f"Wallet: {wallet}")
        print(f"Message: {message}")

        self.setup(
            rpc_url=rpc_endpoint,
            privkey=private_key
        )
        self.flag = lambda: session.get(self.tcp1p_url + "/flag").json()['message']
        return {"uuid": uuid, "rpc_endpoint": rpc_endpoint, "private_key": private_key, "setup_contract": setup_contract, "wallet": wallet, "message": message}

    def from_htb(self, address, restart=False):
        import time
        import requests
        self.htb_url = address
        if restart:
            print("Restarting...")
            response = requests.get(self.htb_url + "/restart")
            # sleep for a while to let the server restart
            time.sleep(15)
            print("Restarted")
        response = requests.get(self.htb_url + "/connection_info").json()
        print(f"PrivateKey: {response['PrivateKey']}")
        print(f"Address: {response['Address']}")
        print(f"setupAddress: {response['setupAddress']}")
        print(f"TargetAddress: {response['TargetAddress']}")
        self.setup(
            rpc_url=address+"/rpc",
            privkey=response['PrivateKey']
        )
        self.flag = lambda: requests.get(self.htb_url + "/flag").text
        return response

def check_setup():
    global is_warned
    if not config.is_setup:
        if not is_warned:
            print("Warning: Configuration not set up, this may cause unexpected behavior")
            print("please run config.setup(rpc_url, privkey) first")
            is_warned = True
        return False
    return True

def call_check_setup(func):
    def wrapper(*args, **kwargs):
        check_setup()
        return func(*args, **kwargs)
    return wrapper

def check_setup_on_create(cls):
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
        check_setup() 
        original_init(self, *args, **kwargs)
    cls.__init__ = new_init
    return cls

config = Config()