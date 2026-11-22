#!/usr/bin/env python3
"""Sprint 3 TCP Trivia Game Server"""

import argparse
import copy
import json
import random
import selectors
import socket
import sys
import time

sel = selectors.DefaultSelector()


class GameRoom:
    """Manages 2-player match state, individual randomized questions, and turn flow."""

    def __init__(self, p1_sock, p2_sock, room_id, questions, max_rounds):
        self.p1_sock = p1_sock
        self.p2_sock = p2_sock
        self.room_id = room_id
        self.max_rounds = max_rounds

        # Create independent randomized question pools per player
        p1_qs = copy.deepcopy(questions)
        p2_qs = copy.deepcopy(questions)
        random.shuffle(p1_qs)
        random.shuffle(p2_qs)
        self.player_questions = {p1_sock: p1_qs, p2_sock: p2_qs}

        self.player_names = {p1_sock: "Player1", p2_sock: "Player2"}
        self.scores = {"Player1": 0, "Player2": 0}
        self.buffers = {p1_sock: "", p2_sock: ""}

        self.players = [p1_sock, p2_sock]
        self.active_idx = 0  # 0 for Player 1, 1 for Player 2
        self.turns_played = 0

        self.q_indices = {p1_sock: 0, p2_sock: 0}
        self.current_questions = {}
        self.current_turn_multiplier = 1
        self.game_started = False

    def send_to(self, sock, message_dict):
        """Serializes dictionary to JSON and sends over TCP with newline framing."""
        payload = (json.dumps(message_dict) + "\n").encode("utf-8")
        try:
            sock.sendall(payload)
        except Exception as e:
            print(f"[ERROR] Failed to send to socket: {e}", file=sys.stderr)

    def handle_client_data(self, sock, mask):
        """Event handler triggered when a client socket has readable data."""
        if mask & selectors.EVENT_READ:
            try:
                data = sock.recv(4096)
                if not data:
                    # TCP EOF: Remote host closed socket cleanly
                    self.handle_disconnect(sock, "transport_drop")
                    return

                self.buffers[sock] += data.decode("utf-8")

                while "\n" in self.buffers[sock]:
                    line, self.buffers[sock] = self.buffers[sock].split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    self.process_message(sock, msg)

            except (ConnectionResetError, TimeoutError, socket.error) as e:
                print(f"[ERROR] Socket read error: {e}", file=sys.stderr)
                self.handle_disconnect(sock, "socket_error")

    def process_message(self, sock, msg):
        msg_type = msg.get("msg_type")

        if msg_type == "CONNECT":
            player_id = msg.get("player_id", "Anonymous")
            self.player_names[sock] = player_id
            self.scores = {
                self.player_names[self.p1_sock]: 0,
                self.player_names[self.p2_sock]: 0,
            }

            # Start game once both players sent CONNECT with aliases
            if (
                self.player_names[self.p1_sock] != "Player1"
                and self.player_names[self.p2_sock] != "Player2"
                and not self.game_started
            ):
                self.game_started = True
                p1_name = self.player_names[self.p1_sock]
                p2_name = self.player_names[self.p2_sock]

                game_start_msg = {
                    "msg_type": "GAME_START",
                    "room_id": self.room_id,
                    "players": [p1_name, p2_name],
                    "total_rounds": self.max_rounds,
                    "timestamp": int(time.time()),
                }
                self.send_to(self.p1_sock, game_start_msg)
                self.send_to(self.p2_sock, game_start_msg)
                self.prompt_active_player()

        elif msg_type == "MOVE":
            expected_sock = self.players[self.active_idx]
            if sock != expected_sock:
                err_msg = {
                    "msg_type": "ERROR",
                    "error_code": 4002,
                    "message": "Out of turn move received. Wait for your turn!",
                    "timestamp": int(time.time()),
                }
                self.send_to(sock, err_msg)
                return

            payload = msg.get("payload", {})
            choice = payload.get("choice")

            if choice not in [0, 1, 2, 3]:
                err_msg = {
                    "msg_type": "ERROR",
                    "error_code": 4001,
                    "message": "Invalid answer index. Must choose between 0 and 3",
                    "timestamp": int(time.time()),
                }
                self.send_to(sock, err_msg)
                choice = -1

            q = self.current_questions.get(sock)
            active_name = self.player_names[sock]
            is_correct = False

            points_earned = 100 * self.current_turn_multiplier

            if q and choice == q.get("answer"):
                self.scores[active_name] += points_earned
                is_correct = True

            correctness_str = (
                f"Correct! (+{points_earned} pts)" if is_correct else "Incorrect."
            )
            notification = (
                f"[Result] {active_name} answered choice [{choice}] —"
                f" {correctness_str}"
            )

            self.turns_played += 1

            if self.turns_played >= self.max_rounds:
                self.end_game(notification)
            else:
                self.active_idx = 1 - self.active_idx
                self.prompt_active_player(notification)

        elif msg_type == "DISCONNECT":
            self.handle_disconnect(sock, msg.get("reason", "intentional_quit"))

    def prompt_active_player(self, notification=None):
        active_sock = self.players[self.active_idx]
        waiting_sock = self.players[1 - self.active_idx]
        active_name = self.player_names[active_sock]

        # Get unique question for active player
        q_list = self.player_questions[active_sock]
        q_idx = self.q_indices[active_sock]
        q = q_list[q_idx % len(q_list)]
        self.q_indices[active_sock] += 1
        self.current_questions[active_sock] = q

        # 30% chance for double points multiplier
        is_double_points = random.random() < 0.3
        self.current_turn_multiplier = 2 if is_double_points else 1

        prefix = f"{notification}\n" if notification else ""
        bonus_banner = (
            "🔥 *** DOUBLE POINTS TURN! (200 PTS) *** 🔥\n"
            if is_double_points
            else ""
        )

        # Active player message
        active_state_msg = {
            "msg_type": "STATE_UPDATE",
            "round": self.turns_played + 1,
            "scores": self.scores,
            "is_my_turn": True,
            "next_question": {
                "question_id": q["question_id"],
                "prompt": f"{prefix}{bonus_banner}[Your Turn] {q['prompt']}",
                "options": q["options"],
            },
            "timestamp": int(time.time()),
        }
        self.send_to(active_sock, active_state_msg)

        # Waiting player message
        waiting_state_msg = {
            "msg_type": "STATE_UPDATE",
            "round": self.turns_played + 1,
            "scores": self.scores,
            "is_my_turn": False,
            "next_question": {
                "question_id": 0,
                "prompt": (
                    f"{prefix}[Opponent's Turn] Waiting for {active_name} to answer"
                    " their question..."
                ),
                "options": [],
            },
            "timestamp": int(time.time()),
        }
        self.send_to(waiting_sock, waiting_state_msg)

    def end_game(self, notification=None):
        winner = max(self.scores, key=self.scores.get)
        outcome = "DRAW" if len(set(self.scores.values())) == 1 else "WIN"
        if outcome == "DRAW":
            winner = "None (Tie)"

        prefix = f"{notification}\n" if notification else ""
        game_over_msg = {
            "msg_type": "GAME_OVER",
            "outcome": outcome,
            "winner": winner,
            "final_scores": self.scores,
            "message": f"{prefix}Match completed!",
            "timestamp": int(time.time()),
        }
        self.send_to(self.p1_sock, game_over_msg)
        self.send_to(self.p2_sock, game_over_msg)
        self.cleanup()

    def handle_disconnect(self, sock, reason):
        quitting_player = self.player_names.get(sock, "Unknown")
        remaining_sock = self.p2_sock if sock == self.p1_sock else self.p1_sock
        remaining_name = self.player_names.get(remaining_sock, "Opponent")

        game_over_msg = {
            "msg_type": "GAME_OVER",
            "outcome": "WIN",
            "winner": remaining_name,
            "final_scores": self.scores,
            "timestamp": int(time.time()),
        }
        self.send_to(remaining_sock, game_over_msg)
        self.cleanup()

    def cleanup(self):
        for sock in self.players:
            try:
                sel.unregister(sock)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass


def load_questions_from_file(filepath="questions.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load questions: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="TCP Trivia Server")
    parser.add_argument(
        "-p", "--port", required=True, type=int, help="Listening port (1024-65535)"
    )
    parser.add_argument(
        "-q", "--questions", default="questions.json", help="Questions JSON file"
    )
    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=10,
        help="Total number of game turns (default: 10)",
    )
    args = parser.parse_args()

    questions = load_questions_from_file(args.questions)
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", args.port))
    server_sock.listen(100)
    server_sock.setblocking(False)

    sel.register(server_sock, selectors.EVENT_READ, data=None)
    print(
        f"[+] Trivia Server listening on 0.0.0.0:{args.port} (Default Rounds:"
        f" {args.rounds})..."
    )

    waiting_client = None
    room_counter = 1

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    conn, addr = key.fileobj.accept()
                    conn.setblocking(False)
                    if waiting_client is None:
                        waiting_client = conn
                        try:
                            wait_msg = (
                                json.dumps({
                                    "msg_type": "LOBBY_WAIT",
                                    "message": "Waiting in lobby for other player...",
                                    "timestamp": int(time.time()),
                                })
                                + "\n"
                            )
                            conn.sendall(wait_msg.encode("utf-8"))
                        except Exception:
                            pass
                    else:
                        room_id = f"room_{room_counter:02d}"
                        room_counter += 1
                        room = GameRoom(
                            waiting_client, conn, room_id, questions, args.rounds
                        )
                        sel.register(
                            waiting_client, selectors.EVENT_READ, data=room.handle_client_data
                        )
                        sel.register(
                            conn, selectors.EVENT_READ, data=room.handle_client_data
                        )
                        print(f"[+] Matched 2 players into {room_id}.")
                        waiting_client = None
                else:
                    callback = key.data
                    callback(key.fileobj, mask)
    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
    finally:
        sel.close()
        server_sock.close()


if __name__ == "__main__":
    main()
