## 2. Detailed Design Specifications
### 2.1 Transport Layer & Packet Framing Mechanism

Transport Protocol: TCP
Serialization Format: Structured JSON
Framing Rule Requirement: TCP is a continuous byte-stream protocol without built-in message boundaries. Multiple messages sent back-to-back may arrive in a single recv() chunk (coalescing), or a single message may be split across multiple chunks (fragmentation). Your protocol blueprint must explicitly define a deterministic framing rule to delimit message boundaries on the wire.

Framing Options & Examples:
Option A: Newline-Delimited JSON (\n Framing)
Framing Rule: Every JSON object is UTF-8 encoded and terminated by a newline character \n (0x0A). The receiver accumulates incoming bytes into a stream buffer until a \n is encountered, extracts the complete line, and deserializes the JSON object.
    Wire Stream Example (Continuous Stream):

    {"msg_type":"CONNECT","player_id":"Alice","timestamp":1727000000}\n{"msg_type":"MOVE","player_id":"Alice","payload":{"question_id":1,"choice":2},"timestamp":1727000005}\n


| Message Type | Direction | Purpose & Description |
| :---: | :---: | :---: | 
| CONNECT | Client -> Server | Client requests to join game room with player alias. | 
| LOBBY_WAIT | Server -> Client  | Server notifies Client 1 that it is waiting for Player 2 to connect. | 
| GAME_START | Server -> Clients | Server notifies both clients that game has started and assigns roles (Player 1 / Player 2). | 
| MOVE | Client -> Server | Active player submits answer selection. | 
| STATE_UPDATE | Server -> Clients | Server broadcasts answer correctness, updates scores, and gives next question. | 
| ERROR | Server -> Client | Server notifies client of out-of-turn move, invalid choice, or malformed message. | 
| DISCONNECT | Client -> Server | Client notifies server of intentional departure/quit. 	 | 
| GAME_OVER | Server -> Clients | Server broadcasts final game outcome (Winner / Draw / Forfeit) and final scores. | 

#### CONNECT Schema
    {
      "msg_type": "CONNECT",
      "player_id": "ALICE",
      "timestamp": 1727000000
    }
#### LOBBY_WAIT Schema
    {
      "msg_type": "LOBBY_WAIT",
      "message": "Waiting in lobby for other player...",
      "timestamp": 1727000001
    }
#### GAME_START Schema 
    {
      "msg_type": "GAME_START",
      "room_id": "room_01",
      "players": ["Alice", "Billy"],
      "total_rounds": 10,
      "timestamp": 1727000010
    }
#### MOVE Schema 
    {
      "msg_type": "MOVE",
      "player_id": "Alice",
      "payload": {
        "question_id": 1,
        "choice": 2
      },
      "timestamp": 1727000015
    }
#### STATE_UPDATE Schema 
    {
      "msg_type": "STATE_UPDATE",
      "round": 3,
      "scores": {
        "Alice": 100,
        "Billy": 300
      },
      "next_question": {
        "question_id": 4,
        "prompt": "Where was ice cream invented?",
        "options": ["USA", "China", "Switzerland", "Mexico"]
      },
      "timestamp": 1727000018
    }
#### ERROR Schema 
    {
      "msg_type": "ERROR",
      "error_code": 4001,
      "message": "Invalid answer index. Must choose between 0 and 3",
      "timestamp": 1727000020
    }
#### DISCONNECT Schema 
    {
      "msg_type": "DISCONNECT",
      "player_id": "Billy",
      "reason": "intentional_quit",
      "timestamp": 1727000030
    }
#### GAME_OVER Schema 
    {
      "msg_type": "GAME_OVER",
      "outcome": "WIN",
      "winner": "Alice",
      "final_scores": {
        "Alice": 500,
        "Billy": 300
      },
      "timestamp": 1727000035
    }

