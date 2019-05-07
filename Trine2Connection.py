#! /usr/bin/env python3
import sys
import socket
import os

class Trine2Connection:
    __server = ("185.20.138.174", 27300)

    def __init__(self):
        self.__connect()

    def __connect(self):
        # this message requests a 4 byte cookie which has to be prepended to all later messages
        hello_payload = bytes.fromhex("ddfb00000a00000003000000c90000000203")
        # pick source port and save
        # packets will only be accepted if {source_ip, source_port} is exactly as it was when
        # we requested the cookie
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sent = self.__sock.sendto(hello_payload, self.__server)
        ans, server = self.__sock.recvfrom(4096)
        message = ans.hex()

        # check if the response has the correct message type
        if not message[:4] == "cf00":
            raise Exception('Got invalid cookie message %s' % message.hex())

        self.__cookie = message[4:]


    def search(self, password):
        '''
        Search for all games protected by the given password string.

        The password parameter is expected to be a string of length <= 16.
        '''
        # convert to hex and enforce length of 16 bytes
        # cut if to long, pad with zeros if to short
        password = password.encode("utf-8").hex()[:32].ljust(32, "0")
        request_id = os.urandom(4).hex()
        # payload form: type[1] + cookie[4] + 03 + requestid[4] + 00000001 + password + padding
        get_games_payload = bytes.fromhex("e0" + self.__cookie + "03" + request_id + "00000001" + password)

        self.__sock.sendto(get_games_payload, self.__server)
        message, _ = self.__sock.recvfrom(4096)

        return self.__parse_games_message(message, request_id)


    def search_public(self):
        '''
        Get a list of all public games.
        '''
        # TODO: randomize
        request_id = os.urandom(4).hex()
        # payload form: type[1] + cookie[4] + 03 + requestid[4] + 000000 + {notfull=01|full=02|all=03} + padding
        get_list_payload = bytes.fromhex("e0" + self.__cookie + "03" + request_id + "000000" + "03" + "00000000000000000000000000000000")

        self.__sock.sendto(get_list_payload, self.__server)
        message, _ = self.__sock.recvfrom(4096)

        return self.__parse_games_message(message, request_id)

    def __parse_games_message(self, message, request_id):
        # check if the response has the correct message type and request_id
        if not message[:5].hex() == ("da" + request_id):
            raise Exception('Got invalid search result message %s' % message.hex())

        games = []
        num_of_games = int(message[5])
        for i in range(num_of_games):
            # first game starts at 6
            # following ones at 6+n*68
            # game format is:
            # id[4]+"00fb5331"[4]+{classic|unltd}{00|01}[1]+level[1]+difficulty[1]+num_players[1]+max_players[1]+"01"[1]+name_with_padding[]
            # -> offsets for known values are therefore:
            # 0: id[4]
            # 8: mode[1] (unlimited/classic)
            # 9: level[1]
            # 10: difficulty[1]
            # 11: num_players[1]
            # 12: max_players[1]
            # 15: name

            offset = 6+i*68
            # find name and
            # cut off at first nullbyte
            end = message.find(b"\x00",offset+15)
            name = message[offset+15:end].decode("utf-8")
            id = message[offset:offset+4].hex()

            mode_map = ["Classic","Unlimited"]
            mode = mode_map[int(message[offset+8])]

            level = int(message[offset+9])

            difficulty_map = ["Easy","Medium","Hard"]
            difficulty = difficulty_map[int(message[offset+10])]

            num_players = int(message[offset+11])
            max_players = int(message[offset+12])

            game = {"id": id, "name": name, "level": level, "difficulty": difficulty, "num_players": num_players, "max_players": max_players, "mode": mode}
            games.append(game)
        return games
        