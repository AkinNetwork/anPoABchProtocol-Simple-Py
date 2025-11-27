import json

from core.chain import AkinChain, make_transaction
from apps.demo_session import DemoSessionApp


def main() -> None:
    chain_id = "AKIN:CHAIN:DEMO"
    validators = ["AKIN:VALIDATOR:1"]
    apps = {"demo_session": DemoSessionApp()}
    chain = AkinChain(chain_id, validators, apps)

    required = ["AKIN:USER:1", "AKIN:ORG:AT", "AKIN:SYS:PAY"]

    # 1. Create session
    tx_create = make_transaction(
        chain_id,
        "demo_session",
        "AKIN:USER:1",
        {
            "action": "create",
            "service_id": "SESSION-1",
            "participants": required,
            "required_signers": required,
        },
        signer="AKIN:USER:1",
    )
    print("ADD create:", chain.add_tx(tx_create))

    # 2. First two signers
    for signer in required[:-1]:
        tx = make_transaction(
            chain_id,
            "demo_session",
            signer,
            {"action": "sign", "service_id": "SESSION-1"},
            signer=signer,
        )
        print(f"ADD sign from {signer}:", chain.add_tx(tx))

    ok, msg = chain.propose_block("AKIN:VALIDATOR:1")
    print("PROPOSE block 1:", ok, msg)
    print("STATE after block 1:", json.dumps(chain.app_states["demo_session"], indent=2))

    # 3. Last signer
    last = required[-1]
    tx_last = make_transaction(
        chain_id,
        "demo_session",
        last,
        {"action": "sign", "service_id": "SESSION-1"},
        signer=last,
    )
    print("ADD sign from last:", chain.add_tx(tx_last))

    ok, msg = chain.propose_block("AKIN:VALIDATOR:1")
    print("PROPOSE block 2:", ok, msg)
    print("STATE final:", json.dumps(chain.app_states["demo_session"], indent=2))

    print("CHAIN valid?:", chain.is_valid_chain())


if __name__ == "__main__":
    main()
        