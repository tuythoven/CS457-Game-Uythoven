## 2. Detailed Design Specifications
### 2.1 Transport Layer & Packet Framing Mechanism

Transport Protocol: TCP
Serialization Format: Structured JSON
Framing Rule Requirement: TCP is a continuous byte-stream protocol without built-in message boundaries. Multiple messages sent back-to-back may arrive in a single recv() chunk (coalescing), or a single message may be split across multiple chunks (fragmentation). Your protocol blueprint must explicitly define a deterministic framing rule to delimit message boundaries on the wire.

Framing Options & Examples:
Option A: Newline-Delimited JSON (\n Framing)
Framing Rule: Every JSON object is UTF-8 encoded and terminated by a newline character \n (0x0A). The receiver accumulates incoming bytes into a stream buffer until a \n is encountered, extracts the complete line, and deserializes the JSON object.
    Wire Stream Example (Continuous Stream):

    {"msg_type":"CONNECT","player_id":"Alice","timestamp":1727000000}\n{"msg_type":"MOVE","player_id":"Alice","payload":{"row":0,"col":2},"timestamp":1727000005}\n

    JSON Schema / Structure Specification (MOVE):

    {
      "msg_type": "MOVE",
      "player_id": "Player_1",
      "payload": {
        "row": 0,
        "col": 2
      },
      "timestamp": 1727000000
    }

Message Type 	Direction 	Purpose & Description
CONNECT 	Client -> Server 	Client requests to join game room with player alias.
LOBBY_WAIT 	Server -> Client 	Server notifies Client 1 that it is waiting for Player 2 to connect.
GAME_START 	Server -> Clients 	Server notifies both clients that game has started and assigns roles (Player 1 / Player 2).
MOVE 	Client -> Server 	Active player submits move coordinates or answer selection.
STATE_UPDATE 	Server -> Clients 	Server broadcasts updated board state, scores, and active player turn.
ERROR 	Server -> Client 	Server notifies client of out-of-turn move, invalid coordinates, or malformed message.
DISCONNECT 	Client -> Server 	Client notifies server of intentional departure/quit.
GAME_OVER 	Server -> Clients 	Server broadcasts final game outcome (Winner / Draw / Forfeit) and final scores.



