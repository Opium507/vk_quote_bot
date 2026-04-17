CHAT_PEER_ID_OFFSET = 2_000_000_000

def is_private_peer(peer_id: int) -> bool:
    return peer_id < CHAT_PEER_ID_OFFSET
