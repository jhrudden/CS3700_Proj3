#!/usr/bin/env python3

import argparse, socket, time, json, select, struct, math, copy

#DEBUG = True
DEBUG = False

parser = argparse.ArgumentParser(description='route packets')
parser.add_argument('asn', type=int, help="AS Number")
parser.add_argument('networks', metavar='networks', type=str, nargs='+', help="networks")
args = parser.parse_args()

##########################################################################################

# Message Fields
TYPE = "type"
SRCE = "src"
DEST = "dst"
MESG = "msg"
TABL = "table"

# Message Types
DATA = "data"
DUMP = "dump"
UPDT = "update"
RVKE = "revoke"
NRTE = "no route"

# Update Message Fields
NTWK = "network"
NMSK = "netmask"
ORIG = "origin"
LPRF = "localpref"
APTH = "ASPath"
SORG = "selfOrigin"

# internal route info
CUST = "cust"
PEER = "peer"
PROV = "prov"


##########################################################################################

class Route: 
    port = None
    network = None
    netMask = None
    localPref = None
    selfOrigin = None
    AsPath = None
    origin = None
    def __init__(self, port, packet):
        self.port = port
        self.network = packet[MESG][NTWK]
        self.netmask = packet[MESG][NMSK]
        self.localPref = packet[MESG][LPRF]
        self.selfOrigin = packet[MESG][SORG]
        self.AsPath = packet[MESG][APTH]
        self.origin = packet[MESG][ORIG]


## TODO: do we need table for routes

class Router:
    asn = None
    routes = None
    updates = None
    relations = None
    sockets = None

    def __init__(self, asn, networks):
        self.asn = asn
        self.routes = {} # {port: Route[]}
        self.updates = []
        self.relations = {}
        self.sockets = {}
        for relationship in networks:
            network, relation = relationship.split("-")
            if DEBUG: 
                print("Starting socket for", network, relation)
            self.sockets[network] = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            self.sockets[network].setblocking(0)
            self.sockets[network].connect(network)
            self.relations[network] = relation
            self.routes[network] = []
        return

    def lookup_routes(self, daddr):
        """ Lookup all valid routes for an address """
        # TODO
        outroutes = []
        return outroutes

    def get_shortest_as_path(self, routes):
        """ select the route with the shortest AS Path """
        if len(routes) == 0:
            return []
        shortest_routes = [routes[0]]
        shortest_length = routes[0].ASPath.count(",") + 1
        for route_index in range(1, len(routes)):
            current_route = routes[route_index]
            current_length = current_route.ASPath.count(",") + 1
            if current_length == shortest_length:
                shortest_routes.append(current_route)
            elif current_length < shortest_length:
                shortest_length = current_length
                shortest_routes = [current_route]
        return shortest_routes
            
    def get_highest_preference(self, routes):
        """ select the route with the highest local pref """
        if len(routes) == 0:
            return []
        highest_routes = [routes[0]]
        highest_pref = routes[0].localPref
        for route_index in range(1, len(routes)):
            current_route = routes[route_index]
            if current_route.localPref == highest_pref:
                highest_routes.append(current_route)
            elif current_route.localPref > highest_pref:
                highest_pref = current_route.localPref
                highest_routes = [current_route]
        return highest_routes
         
    def get_self_origin(self, routes):
        """ select self originating routes """
        # TODO
        outroutes = []
        for route in routes:
            if route.selfOrigin == "true":
                outroutes.append(route)
        return outroutes

    def get_origin_routes(self, routes):
        """ select origin routes: IGP > EGP > UNK """
        # TODO
        outroutes = []
        current_priority = "UNK"
        better = ["EGP", "IGP"]
        for route in routes:
            if route.origin == current_priority:
                outroutes.append(routes)
            elif route.origin in better:
                current_priority = route.origin
                better.remove(route.origin)
                outroutes = [route]

        return outroutes
        

    def filter_relationships(self, srcif, routes):
        """ Don't allow Peer->Peer, Peer->Prov, or Prov->Peer forwards """
        outroutes = []
        for route in routes:
            srcif_rel = self.relations[srcif]
            route_rel = self.relations[route.port]
            if (srcif_rel == CUST or route_rel == CUST):
                outroutes.append(route)
            elif (srcif_rel == PROV and route_rel == PROV):
                outroutes.append(route)
        return outroutes

    def get_route(self, srcif, daddr):
        """	Select the best route for a given address	"""
        # TODO
        peer = None
        routes = self.lookup_routes(daddr)
        # Rules go here
        if routes:
            # 1. Highest Preference
            routes = self.get_highest_preference(routes)
            # 2. Self Origin
            routes = self.get_self_origin(routes)
            # 3. Shortest ASPath
            routes = self.get_shortest_as_path(routes)
            # 4. IGP > EGP > UNK
            routes = self.get_origin_routes(routes)
            # 5. Lowest IP Address
            # TODO
            # Final check: enforce peering relationships
            routes = self.filter_relationships(srcif, routes)
        return self.sockets[peer] if peer else None

    def forward(self, srcif, packet):
        """	Forward a data packet	"""
        # TODO
        return False

    def coalesce(self):
        """	coalesce any routes that are right next to each other	"""
        # TODO (this is the most difficult task, save until last)
        return False

    def update(self, srcif, packet):
        """	handle update packets	"""
        # TODO 
        self.routes[srcif].extend(Route(srcif, packet))
        packet_copy = copy.deepcopy(packet)
        packet_copy[MESG][APTH] = f"[{self.asn}, " + packet_copy[MESG][APTH][1:]
        packet_json = json.dumps(packet_copy)
        if self.relations[srcif] == CUST:
            for socket in self.sockets.keys():
                if socket != srcif:
                    self.sockets[socket].send(packet_json)
        else:
           for socket in self.sockets.keys():
                if socket != srcif and not(self.relations[socket] in [PROV, PEER]):
                    self.sockets[socket].send(packet_json) 
    
    def revoke(self, packet):
        """	handle revoke packets	"""
        # TODO
        return True

    def dump(self, packet):
        """	handles dump table requests	"""
        # TODO
        return True

    def handle_packet(self, srcif, packet):
        """	dispatches a packet """
        # TODO
        return False

    def send_error(self, conn, msg):
        """ Send a no_route error message """
        # TODO
        return

    def run(self):
        while True:
            socks = select.select(self.sockets.values(), [], [], 0.1)[0]
            for conn in socks:
                try:
                    k = conn.recv(65535)
                except:
                    # either died on a connection reset, or was SIGTERM's by parent
                    return
                if k:
                    for sock in self.sockets:
                        if self.sockets[sock] == conn:
                            srcif = sock
                    msg = json.loads(k)
                    if not self.handle_packet(srcif, msg):
                        self.send_error(conn, msg)
                else:
                    return
        return

if __name__ == "__main__":
    router = Router(args.asn ,args.networks)
    router.run()
