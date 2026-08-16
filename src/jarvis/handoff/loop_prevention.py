"""Pure max-hop and message-type loop prevention rules."""
from dataclasses import replace
from .protocol import HandoffEnvelope, ProtocolError, REQUESTS

def consume_hop(envelope: HandoffEnvelope) -> HandoffEnvelope:
    if envelope.max_hops <= 0: raise ProtocolError("Maximum handoff hops reached.")
    return replace(envelope, max_hops=envelope.max_hops - 1)

def may_invoke_agent(envelope: HandoffEnvelope) -> bool:
    return envelope.type in REQUESTS
