#! /usr/bin/env python3
import sys
import socket
import os
import ipaddress
from requests import get

class Trine2Connection:
    __server = ("185.20.138.174", 27300)

    def __init__(self):
        self.local_ip = ipaddress.IPv4Address(get('https://api.ipify.org').text).packed.hex()
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


    def search(self, password=""):
        '''
        Search for all games protected by the given password string.

        The password parameter is expected to be a string of length <= 16.
        No password or empty password returns all public games.
        '''
        if password != "":
            # convert to hex and enforce length of 16 bytes
            # cut if to long, pad with zeros if to short
            password_bytes = password.encode("utf-8").hex()[:32].ljust(32, "0")
        else:
            password_bytes = "0"*32

        request_id = os.urandom(4).hex()
        # payload form: type[1] + cookie[4] + 03 + requestid[4] + 000000 + {notfull=01|full=02|all=03} + password + padding
        get_games_payload = bytes.fromhex("e0" + self.__cookie + "03" + request_id + "000000" "03" + password_bytes)

        self.__sock.sendto(get_games_payload, self.__server)
        message, _ = self.__sock.recvfrom(4096)

        return self.__parse_games_message(message, request_id)

    def getGameIP(self, game_id):
        '''
        Returns the IP of game with ID.
        '''
        if len(game_id) != 8:
            return

        request_id = os.urandom(4)
        request_id2 = os.urandom(4)

        # payload format is:
        #    cookie   game_id  (fix?)   req_id            req_id2
        # e4 ca865408 cdb31383 95e99f2f 6aa4c0a8 2a516aa4 80a60deb 000000010110000100a3f5cc
        get_ip_payload = bytes.fromhex("e4" + self.__cookie + game_id + self.local_ip + request_id.hex() + "2a516aa4" + request_id2.hex() + "000000010110000100a3f5cc")

        self.__sock.sendto(get_ip_payload, self.__server)
        message1, _ = self.__sock.recvfrom(4096)
        message2, _ = self.__sock.recvfrom(4096)

        # message1 format is:
        #    game_id  cookie            resp_id  req_id2
        # d1 08f29c44 9771226b 00000000 da522874 02e4648a

        # check request_id2 and grab resp_id
        if request_id2 != message1[17:21]:
            return
        response_id = message1[13:17]

        # message2 format is:
        #    game_id  cookie   srv_ip   (???)    req_id  resp_id
        # e4 08f29c44 9771226b 95e99f2f 6aa4c0a8 2a516aa4 da522874 00000003 0110000100a3f5cc

        # log for analysis
        print("game_id = %s and game_fix = %s" % (game_id, message2[13:17].hex()))
        print("request_id = %s and message[34:42] = %s" % (request_id.hex(), message2[17:21].hex()))

        # check response_id and grab ip
        if response_id != message2[21:25]:
            return
        ip = ipaddress.IPv4Address(message2[9:13])
        return str(ip)



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
            game_id = message[offset:offset+4].hex()

            mode_map = ["Classic","Unlimited"]
            mode = mode_map[int(message[offset+8])]

            level = int(message[offset+9])

            difficulty_map = ["Easy","Medium","Hard"]
            difficulty = difficulty_map[int(message[offset+10])]

            num_players = int(message[offset+11])
            max_players = int(message[offset+12])

            # get game ip
            ip = self.getGameIP(game_id)

            game = {"id": game_id, "name": name, "level": level, "difficulty": difficulty, "num_players": num_players, "max_players": max_players, "mode": mode, "ip": ip}
            games.append(game)
        return games
