### Sequence Diagram 457 Uythoven Trivia Game

```mermaid
sequenceDiagram
    autonumber
    actor Client1 as Client 1 (Player 1)
    participant Server as Game Server
    actor Client2 as Client 2 (Player 2)

    Client1->>Server: MOVE (Choice)
    Note over Server: Validate answer and question ID
    alt Valid Answer Choice
        Note over Server: Update scores & advance question
        Server-->>Client1: STATE_UPDATE (Round, Scores, Next Question)
        Server-->>Client2: STATE_UPDATE (Round, Scores, Next Question)
    else Invalid Answer Index
        Server-->>Client1: ERROR (Invalid answer index)
    end
