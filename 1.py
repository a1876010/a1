#!/usr/bin/env python3
import sys
import math
from collections import defaultdict, deque

INF = float('inf')

class Router:
    def __init__(self, name, all_routers):
        self.name = name
        self.neighbours = {}  # direct links {neighbour: cost}
        self.distance_table = {
            dest: {via: (0 if dest == via == self.name else INF) for via in all_routers}
            for dest in all_routers
        }
        self.routing_table = {}

    def update_distance_table(self, network):
        updated = False
        for dest in network.routers:
            if dest == self.name:
                continue
            best_cost = INF
            best_via = None
            for neighbour in self.neighbours:
                if dest not in network.routers[neighbour].routing_table:
                    continue
                cost = self.neighbours[neighbour] + network.routers[neighbour].routing_table[dest][1]
                if cost < best_cost:
                    best_cost = cost
                    best_via = neighbour
            if best_cost != self.routing_table.get(dest, (None, INF))[1]:
                self.routing_table[dest] = (best_via, best_cost)
                updated = True
            for via in network.routers:
                if via == self.name:
                    continue
                if via in self.neighbours and dest in network.routers[via].routing_table:
                    cost = self.neighbours[via] + network.routers[via].routing_table[dest][1]
                    self.distance_table[dest][via] = cost
                else:
                    self.distance_table[dest][via] = INF
        return updated

    def print_distance_table(self, t, all_routers):
        print(f"Distance Table of router {self.name} at t={t}:")
        headers = sorted(r for r in all_routers if r != self.name)
        print("   " + "  ".join(headers))
        for dest in headers:
            row = []
            for via in headers:
                val = self.distance_table[dest].get(via, INF)
                row.append(str(val if val != INF else "INF"))
            print(f"{dest}  {'  '.join(row)}")
        print()

    def print_routing_table(self):
        print(f"Routing Table of router {self.name}:")
        for dest in sorted(self.routing_table):
            via, cost = self.routing_table[dest]
            if cost == INF:
                print(f"{dest},INF,INF")
            else:
                print(f"{dest},{via},{cost}")
        print()


class Network:
    def __init__(self):
        self.routers = {}

    def ensure_router(self, name):
        if name not in self.routers:
            self.routers[name] = Router(name, self.routers)

    def apply_link(self, r1, r2, cost):
        self.ensure_router(r1)
        self.ensure_router(r2)
        if cost == -1:
            self.routers[r1].neighbours.pop(r2, None)
            self.routers[r2].neighbours.pop(r1, None)
        else:
            self.routers[r1].neighbours[r2] = cost
            self.routers[r2].neighbours[r1] = cost

    def initialize_tables(self):
        for r in self.routers:
            router = self.routers[r]
            router.routing_table = {}
            for dest in self.routers:
                if dest == r:
                    continue
                if dest in router.neighbours:
                    router.routing_table[dest] = (dest, router.neighbours[dest])
                else:
                    router.routing_table[dest] = (None, INF)

    def run_distance_vector(self):
        t = 0
        while True:
            any_updates = False
            for r in sorted(self.routers):
                updated = self.routers[r].update_distance_table(self)
                self.routers[r].print_distance_table(t, self.routers)
                any_updates = any_updates or updated
            if not any_updates:
                break
            t += 1

    def print_final_tables(self):
        for r in sorted(self.routers):
            self.routers[r].print_routing_table()
            print()


def parse_input():
    lines = [line.strip() for line in sys.stdin if line.strip()]
    i = 0
    router_names = []

    # Parse routers
    while i < len(lines) and lines[i] != "START":
        router_names.append(lines[i])
        i += 1
    i += 1  # skip START

    net = Network()
    for name in router_names:
        net.ensure_router(name)

    # Parse initial links
    while i < len(lines) and lines[i] != "UPDATE":
        r1, r2, cost = lines[i].split()
        net.apply_link(r1, r2, int(cost))
        i += 1
    i += 1  # skip UPDATE

    net.initialize_tables()
    net.run_distance_vector()
    net.print_final_tables()

    # Parse updates
    while i < len(lines) and lines[i] != "END":
        r1, r2, cost = lines[i].split()
        net.apply_link(r1, r2, int(cost))
        i += 1
    i += 1  # skip END

    if i > 0:
        net.initialize_tables()
        net.run_distance_vector()
        net.print_final_tables()


if __name__ == "__main__":
    parse_input()
