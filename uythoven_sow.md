# CS 457 Project Statement of Work (SOW) & Protocol Specification Template

**Student Name:** Tisha Uythoven  
**Date:** 2026-09-18  
**Course:** CS 457 - Computer Networks  
**Target Server Domain:** `server.uythoven.edu`  

---

## 1. Game Selection & Scope (Sprint 0)

> Planning is going to be an iterative process through the sprints so you don't have to have all the details now. Focus on big overview concepts. You will be updating the SOW as we plan.
> You have a lot of freedom to choose a game. There are a couple caveats.  

> - It must run in the console. The lab nodes won't be able to handle extensive graphics.
> - It has to be self-contained. You can use a internet-connector to download you code, but because the architecture must run 5 nodes you won't be able to run 
> - You are encouraged to use python, but I'm not going to make it a strict requirement. The instructor and TA's ability to help with C or Rust, etc will be diminished in other languages.

### 1.1 Game Overview
- **Chosen Game:** Terminal Trivia
- **Player Capacity:** 2 Players (Simulated via 2 CML Client nodes)
- **Game Summary:** The game will work somewhat like Jeopardy where there will be a few categories to choose from for a specified number of turns. There will also be a double points question randomly assigned. Players will win by having a higher score than the other player. If the round ends in a tie with the same scores, try 1 tie breaker question.

### 1.2 Core Game Rules & Win/Draw Conditions
- **Turn Mechanics:** Each player gets a turn to chose a question and then answer. The next turn will be the other player's. Player 2 cannot answer Player 1's question and vice versa. Once the answer is given and correctness evaluated, the turn will move to the next player.
- **Victory Condition:** The player with the most points by the end is the winner. 
- **Draw/Tie Condition:** If the scores are the same, then 1 tie breaker question will be asked to each player. If it's still a draw, then that will be the declared outcome

---

## 2. Application-Layer Messaging Protocol Blueprint (Sprint 1 Deliverable)

### 2.1 Message Transport & Serialization Format
- **Transport Protocol:** TCP
- **Serialization Format:** JSON
- **Framing Mechanism:** JSON payloads

### 2.2 Message Schema Definitions
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
---

### 2.3 Game State Machine (FSM) Design (Sprint 1 Deliverable)
- **State Transitions:**
[FSM Design](https://github.com/tuythoven/CS457-Game-Uythoven/blob/main/docs/fsm_specification.md)

---

## 3. Game Behavior & Server Concurrency Architecture (Sprint 2 Deliverable)

### 3.1 Server Concurrency Strategy
- **Architecture Choice:** [Multi-Threading (`threading.Thread`) OR Non-blocking I/O multiplexing (`select.select` / `selectors`)]
- **Synchronization Logic:** Explain how shared game state and client list are thread-safe (e.g. `threading.Lock`) to prevent race conditions during turn processing.

### 3.2 State & Score Synchronization Across Clients
- **Turn Enforcement:** Detail how the server validates active player ID before processing moves and broadcasts updated turn notifications to all clients.
- **Score & Board Synchronization:** Describe how state broadcasts keep client screens synchronized in real time.

---

## 4. Coding & AI Implementation Plan (Sprint 3)

- **Permitted AI Tools:** [e.g., GitHub Copilot, ChatGPT, Claude]
- **AI Prompting & Constraint Strategy:** Explain how you will constrain AI models to generate code (in Python or your chosen language) that adheres strictly to the protocol blueprint and FSM designed in Sprints 1 & 2.
- **Implementation Risk Management:** Detail your plan to leverage past programming experience and manage time to ensure code completion on schedule.

---

## 5. CML Multi-Subnet Topology & Wireshark Deployment Plan (Sprint 4 & 5 Deliverable)

> For now you can use the topology below. We may update this when we get to defining subnets.

### 5.1 Subnet & Router Design
- **Subnet A (Client 1):** `192.168.10.0/24` (Interface `Gi0/1` on Router R1)
- **Subnet B (Client 2):** `192.168.11.0/24` (Interface `Gi0/2` on Router R1)
- **Subnet C (Game Server):** `192.168.20.0/24` (Interface `Gi0/1` on Router R2)
- **Router Backbone:** `10.0.0.0/30` (Interface `Gi0/0` on R1 <-> `Gi0/0` on R2)

### 5.2 DHCP Pools & DNS Configuration Plan
- **Router R1 DHCP Pool 1 (`CLIENT1_POOL`):** Leases `192.168.10.10` - `192.168.10.50`, gateway `192.168.10.1`, DNS `10.0.0.2`.
- **Router R1 DHCP Pool 2 (`CLIENT2_POOL`):** Leases `192.168.11.10` - `192.168.11.50`, gateway `192.168.11.1`, DNS `10.0.0.2`.
- **Router R2 Authoritative DNS:** Configured with `ip dns server` and static host mapping `server.[yourlastname].edu` -> `192.168.20.100`.

### 5.3 Deployment Strategy & Wireshark Trace Capture
- **CML Deployment Strategy:** Deploy `server.py` onto Subnet C node (`192.168.20.100`) behind Router R2, and `client.py` onto Subnet A and Subnet B nodes behind Router R1.
- **Cisco Infrastructure Configuration:** Router R1 DHCP pools (`CLIENT1_POOL`, `CLIENT2_POOL`) and Router R2 authoritative DNS (`ip host server.[lastname].edu 192.168.20.100`).
- **Wireshark Trace Capture Plan:** Capture DHCP DORA exchange (`dhcp_negotiation.pcap`) and DNS query/response resolution (`dns_lookup.pcap`).
