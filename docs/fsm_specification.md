### FSM 457 Uythoven Trivia Game

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> WAITING_FOR_PLAYERS: Server starts, listens

    WAITING_FOR_PLAYERS --> GAME_START : 2 Clients Connected (CONNECT is received)

    WAITING_FOR_PLAYERS --> DISCONNECT_HANDLER : Client disconnects before start

    GAME_START --> PLAYER_TURN : Initialize questions and assign player roles

    state PLAYER_TURN {
        [*] --> WaitForAnswers
    }

    PLAYER_TURN --> EVALUATE_MOVE : Current player sends MOVE
    
    EVALUATE_MOVE --> PLAYER_TURN : Valid move and more rounds remain (STATE_UPDATE sent)
    EVALUATE_MOVE --> PLAYER_TURN : Invalid move (Send ERROR to Client)
    EVALUATE_MOVE --> GAME_OVER : Winner or end of all rounds

    %% Disconnect and Forfeit flows from active states
    PLAYER_TURN --> DISCONNECT_HANDLER : TCP drops or DISCONNECT message received
    EVALUATE_MOVE --> DISCONNECT_HANDLER : Client drops suddenly

    DISCONNECT_HANDLER --> CheckForfeit : Determine remaining player
    CheckForfeit --> GAME_OVER : Declare remaining player the Winner

    GAME_OVER --> CLEAN : GAME_OVER broadcasted to clients

    CLEAN --> [*] : Reset State
