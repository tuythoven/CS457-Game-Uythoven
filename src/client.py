#!/usr/bin/env python3
"""Sprint 3 TCP Trivia Game Client."""

import argparse
import json
import socket
import sys
import time


def send_message(sock, message_dict):
    try:
        payload = json.dumps(message_dict) + "\n"
        sock.sendall(payload.encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError, TimeoutError, socket.error) as e:
        print(f"[ERROR] Socket transmission failed: {e}", file=sys.stderr)
        raise


def parse_arguments():
    parser = argparse.ArgumentParser(description="TCP Trivia Game Client")
    parser.add_argument(
        "-i", "--hostname", required=True, help="Server DNS hostname or IP"
    )
    parser.add_argument(
        "-p", "--port", required=True, type=int, help="Server port (1024-65535)"
    )
    parser.add_argument(
        "-n", "--name", default="Player 1", help="Player alias for CONNECT message"
    )
    args = parser.parse_args()
    if not (1024 <= args.port <= 65535):
        print(f"[ERROR] Port {args.port} out of range (1024-65535).", file=sys.stderr)
        sys.exit(1)
    return args


def main():
    args = parse_arguments()

    # DNS Resolution Exception Handling (Mandatory Requirement)
    try:
        server_ip = socket.gethostbyname(args.hostname)
    except socket.gaierror:
        print(
            f"[ERROR] Unable to resolve DNS hostname '{args.hostname}'.",
            file=sys.stderr,
        )
        print(
            "Please check your Cisco router DNS configuration ('ip dns server' /"
            " 'ip host') or verify domain spelling.",
            file=sys.stderr,
        )
        sys.exit(1)

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_sock.connect((server_ip, args.port))
        print(f"[+] Connected to Trivia Server at {server_ip}:{args.port}")
    except socket.error as e:
        print(f"[ERROR] Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    receive_buffer = ""

    try:
        connect_msg = {
            "msg_type": "CONNECT",
            "player_id": args.name,
            "timestamp": int(time.time()),
        }
        send_message(client_sock, connect_msg)

        while True:
            # Accumulate incoming stream until newline delimiter is reached
            while "\n" not in receive_buffer:
                data = client_sock.recv(4096)
                if not data:
                    # TCP EOF Check: Prevents 100% CPU infinite loop
                    print("\n[!] Connection closed by remote host (TCP EOF).")
                    return
                receive_buffer += data.decode("utf-8")

            line, receive_buffer = receive_buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("msg_type")

            if msg_type == "LOBBY_WAIT":
                print(f"[LOBBY] {msg.get('message')}")

            elif msg_type == "GAME_START":
                print("\n" + "=" * 50)
                print(f"[GAME] Match started in room: {msg.get('room_id')}")
                print(f"Players: {', '.join(msg.get('players', []))}")
                print(f"Total Turns: {msg.get('total_rounds')}")
                print("=" * 50)

            elif msg_type == "STATE_UPDATE":
                print(f"\n--- Turn {msg.get('round')} ---")
                print(f"Scores: {msg.get('scores')}")
                q_data = msg.get("next_question", {})
                print(f"{q_data.get('prompt')}")

                is_my_turn = msg.get("is_my_turn", False)
                options = q_data.get("options", [])

                if is_my_turn:
                    for idx, option in enumerate(options):
                        print(f"  [{idx}] {option}")

                    try:
                        choice_str = input("Select option index (0-3): ").strip()
                        choice_val = int(choice_str) if choice_str else 0
                    except ValueError:
                        choice_val = 0

                    move_msg = {
                        "msg_type": "MOVE",
                        "player_id": args.name,
                        "payload": {
                            "question_id": q_data.get("question_id"),
                            "choice": choice_val,
                        },
                        "timestamp": int(time.time()),
                    }
                    send_message(client_sock, move_msg)
                else:
                    # Non-turn player: Display status and block on recv() for next update
                    print("[~] Waiting for opponent to take their turn...")

            elif msg_type == "ERROR":
                print(
                    f"[ERROR CODE {msg.get('error_code')}]: {msg.get('message')}",
                    file=sys.stderr,
                )

            elif msg_type == "GAME_OVER":
                print("\n[***] GAME OVER [***]")
                if "message" in msg:
                    print(msg["message"])
                print(f"Outcome: {msg.get('outcome')}")
                print(f"Winner: {msg.get('winner')}")
                print(f"Final Scores: {msg.get('final_scores')}")
                break

            elif msg_type == "DISCONNECT":
                print(
                    f"[!] Player {msg.get('player_id')} disconnected:"
                    f" {msg.get('reason')}"
                )
                break

    except KeyboardInterrupt:
        print("\n[!] Client terminating intentionally...")
        try:
            disconnect_msg = {
                "msg_type": "DISCONNECT",
                "player_id": args.name,
                "reason": "intentional_quit",
                "timestamp": int(time.time()),
            }
            send_message(client_sock, disconnect_msg)
        except Exception:
            pass
    finally:
        client_sock.close()


if __name__ == "__main__":
    main()
