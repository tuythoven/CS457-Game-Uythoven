# Sprint 2: Game Behavior & Server Concurrency Architecture Design

## Server Concurrency Model 
Option B: Non-Blocking I/O Multiplexing (selectors/select.select)
* The server sets client sockets to non-blocking mode (sock.setblocking(False))
* An OS event loop monitors read/write availability across all sockets within a single thread

#### Explanation of concurrency model
In multi-threading, each client is assigned a dedicated thread. This approach introduces context-switching overhead and possibilities for deadlocks or starvation. Meanwhile non-blocking I/O uses a single thread and selectors to know when an event is happening. The selectors can monitor multiple client sockets concurrently. 

All the server sockets are configured for non-blocking mode. With sock.setblocking(False), operations like recv() or accept() do not block execution and do not freeze up the server if there is no data. 

The server then registers the sockets for OS event interfaces. The single thread blocks on selector.select() and sleeps until a file descriptor is ready to read or write. 

When data arrives from a connected client, the event loop becomes active and processes the socket's read buffer, reads the payload, and then executes game logic. This ensures that multiple simultaneous players can connect without thread complexity management. 

When a client disconnects or triggers EOF, the event loop will catch an exception. After that it will unregister the socket with selector.unregister(sock) and close the descriptor to prevent leaks with sock.close().

#### Thread safety analysis and lock acquisition strategy
Since I am using event driven select concurrency, there is no need to do explicit mutex locks to prevent race conditions. In the event loop, it processes incoming events one at a time. Each message is parsed, validated, and computed to completion before the loop goes to the next socket event. 

Because mutations to the state happen sequentially within a thread's execution, the in-between states are never exposed for interruptions. The event loop isolation ensures data integrity without deadlock risks that happen with mutex locking. 

The server should safely maintain state structures within the scope. This includes the scores, question index, and how each socket is mapped to a player. 


## Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor Client1 as Client 1 (Player 1)
    participant Server as Game Server
    actor Client2 as Client 2 (Player 2)

    Client1->>Server: MOVE (Answer Choice)
    Note over Server: Validate turn, question ID, and answer choice
    alt Valid Answer Choice
        Note over Server: Update scores & advance question
        Server-->>Client1: STATE_UPDATE (Round, Scores, Next Question)
        Server-->>Client2: STATE_UPDATE (Round, Scores, Next Question)
    else Invalid Answer Index
        Server-->>Client1: ERROR (Invalid answer index or out of turn)
    end
