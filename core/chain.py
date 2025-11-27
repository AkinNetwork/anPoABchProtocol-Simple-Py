import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Protocol

from .hashing import hash_json


@dataclass
class Signature:
    signer: str
    sig: str  # placeholder; no real crypto in v0.1


@dataclass
class Transaction:
    tx_id: str
    chain_id: str
    app: str
    sender: str
    payload: Dict[str, Any]
    signatures: List[Signature]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "chain_id": self.chain_id,
            "app": self.app,
            "sender": self.sender,
            "payload": self.payload,
            "signatures": [s.__dict__ for s in self.signatures],
            "timestamp": self.timestamp,
        }


@dataclass
class Block:
    index: int
    timestamp: float
    prev_hash: str
    validator: str
    transactions: List[Transaction]
    block_hash: str = field(init=False)
    validator_signature: str = ""

    def __post_init__(self):
        self.block_hash = self.calc_hash()

    def calc_hash(self) -> str:
        return hash_json(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "prev_hash": self.prev_hash,
                "validator": self.validator,
                "transactions": [tx.to_dict() for tx in self.transactions],
            }
        )


class AkinApp(Protocol):
    name: str

    def validate(self, tx: Transaction, state: Dict[str, Any]) -> Tuple[bool, str]:
        ...

    def apply(self, tx: Transaction, state: Dict[str, Any]) -> None:
        ...


class AkinChain:
    """Minimal PoA chain implementation for the Akin Protocol (simple & clean)."""

    def __init__(self, chain_id: str, validators: List[str], apps: Dict[str, AkinApp]):
        self.chain_id = chain_id
        self.validators = validators
        self.blocks: List[Block] = []
        self.pending: List[Transaction] = []
        self.apps = apps
        self.app_states: Dict[str, Dict[str, Any]] = {name: {} for name in apps.keys()}

                # genesis block
        genesis = Block(
            index=0,
            timestamp=time.time(),
            prev_hash="0x0",
            validator="GENESIS",
            transactions=[],
        )
        genesis.validator_signature = ""
        self.blocks.append(genesis)

    def add_tx(self, tx: Transaction) -> Tuple[bool, str]:
        if tx.chain_id != self.chain_id:
            return False, "wrong chain_id"
        if tx.app not in self.apps:
            return False, "unknown app"

        app = self.apps[tx.app]
        state = self.app_states[tx.app]
        ok, msg = app.validate(tx, state)
        if not ok:
            return False, msg

        # NOTE: no real signature verification in v0.1
        self.pending.append(tx)
        return True, "queued"

    def _new_block(self, validator: str, txs: List[Transaction]) -> Block:
        prev = self.blocks[-1]
        blk = Block(
            index=len(self.blocks),
            timestamp=time.time(),
            prev_hash=prev.block_hash,
            validator=validator,
            transactions=txs,
        )
        blk.validator_signature = f"sig_by_{validator}"  # placeholder
        return blk

    def propose_block(self, validator: str) -> Tuple[bool, str]:
        if validator not in self.validators:
            return False, "unauthorized validator"
        if not self.pending:
            return False, "no pending txs"

        txs = self.pending
        self.pending = []
        blk = self._new_block(validator, txs)

                # basic validation
        prev = self.blocks[-1]
        if blk.prev_hash != prev.block_hash:
            self.pending.extend(txs)
            return False, "prev_hash mismatch"

        if blk.block_hash != blk.calc_hash():
            self.pending.extend(txs)
            return False, "block_hash mismatch"

        self.blocks.append(blk)

                # apply state transitions
        for tx in blk.transactions:
            app = self.apps[tx.app]
            state = self.app_states[tx.app]
            app.apply(tx, state)

        return True, f"block {blk.index} added"

    def is_valid_chain(self) -> Tuple[bool, str]:
        for i in range(1, len(self.blocks)):
            cur = self.blocks[i]
            prev = self.blocks[i - 1]
            if cur.prev_hash != prev.block_hash:
                return False, f"prev_hash mismatch at {i}"
            if cur.block_hash != cur.calc_hash():
                return False, f"hash mismatch at {i}"
        return True, "ok"


def make_transaction(
    chain_id: str, app: str, sender: str, payload: Dict[str, Any], signer: str
) -> Transaction:
    """Helper to create a simple transaction with a single signature."""
    return Transaction(
        tx_id=str(uuid.uuid4()),
        chain_id=chain_id,
        app=app,
        sender=sender,
        payload=payload,
        signatures=[Signature(signer=signer, sig="dummy")],
        timestamp=time.time(),
    )
        