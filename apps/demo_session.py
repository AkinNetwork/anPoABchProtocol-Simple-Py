        from typing import Dict, Any, Tuple
        from core.chain import Transaction  # assumes you run from inside python/ folder


        class DemoSessionApp:
            """Generic N-party confirmation app."""

            name = "demo_session"

            def validate(self, tx: Transaction, state: Dict[str, Any]) -> Tuple[bool, str]:
                payload = tx.payload
                action = payload.get("action")

                if action == "create":
                    if "service_id" not in payload:
                        return False, "service_id required"
                    if not isinstance(payload.get("participants"), list):
                        return False, "participants list required"
                    if not isinstance(payload.get("required_signers"), list):
                        return False, "required_signers list required"
                    return True, "ok"

                if action == "sign":
                    if "service_id" not in payload:
                        return False, "service_id required"
                    if not tx.signatures:
                        return False, "signature required"
                    return True, "ok"

                return False, f"unknown action {action}"

            def apply(self, tx: Transaction, state: Dict[str, Any]) -> None:
                sessions = state.setdefault("sessions", {})
                payload = tx.payload
                action = payload["action"]
                sid = payload["service_id"]

                if action == "create":
                    required = payload["required_signers"]
                    sessions[sid] = {
                        "service_id": sid,
                        "participants": payload["participants"],
                        "required_signers": required,
                        "signatures_collected": {p: False for p in required},
                        "status": "pending",
                    }
                elif action == "sign":
                    sess = sessions.get(sid)
                    if not sess:
                        return
                    for sig in tx.signatures:
                        if sig.signer in sess["signatures_collected"]:
                            sess["signatures_collected"][sig.signer] = True
                    if all(sess["signatures_collected"].values()):
                        sess["status"] = "completed"
        