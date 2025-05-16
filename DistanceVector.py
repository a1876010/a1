#!/usr/bin/env python3

class Router:
    def __init__(self, name):
        self.name = name
        self.neighbors = {}  # {neighbor_name: cost}
        self.distance_table = {}  # {dest: {next_hop: cost}}
        self.routing_table = {}  # {dest: (next_hop, cost)}
        self.next_hop_for_dest = {}  # {dest: next_hop} - to track for poisoned reverse

    def add_neighbor(self, neighbor, cost):
        self.neighbors[neighbor] = cost
        
    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            del self.neighbors[neighbor]
    
    def update_neighbor_cost(self, neighbor, cost):
        if cost == -1:  # Remove the link
            self.remove_neighbor(neighbor)
        else:
            self.add_neighbor(neighbor, cost)
    
    def initialize_distance_table(self, all_routers):
        # Initialize distance table with all destinations
        for router in all_routers:
            if router != self.name:
                self.distance_table[router] = {}
                for neighbor in self.neighbors:
                    self.distance_table[router][neighbor] = float('inf')
        
        # Set direct costs to neighbors
        for neighbor, cost in self.neighbors.items():
            if neighbor in self.distance_table:
                self.distance_table[neighbor][neighbor] = cost
    
    def print_distance_table(self, time_step):
        print(f"Distance Table of router {self.name} at t={time_step}:")
        
        # Get all destinations and next_hops (excluding self)
        destinations = sorted([r for r in self.distance_table.keys()])
        next_hops = sorted([r for r in set(nh for d in self.distance_table.values() for nh in d.keys())])
        
        # Print header row
        print("     ", end="")
        for next_hop in next_hops:
            print(f"{next_hop}    ", end="")
        print()
        
        # Print each row
        for dest in destinations:
            print(f"{dest}    ", end="")
            for next_hop in next_hops:
                cost = self.distance_table[dest].get(next_hop, float('inf'))
                if cost == float('inf'):
                    print("INF  ", end="")
                else:
                    print(f"{cost}    ", end="")
            print()
        print()
    
    def update_routing_table(self):
        changed = False
        old_next_hop_for_dest = self.next_hop_for_dest.copy()
        
        for dest in self.distance_table:
            # Find minimum cost route to this destination
            min_cost = float('inf')
            best_next_hop = None
            
            # Search in alphabetical order
            for next_hop in sorted(self.distance_table[dest].keys()):
                cost = self.distance_table[dest][next_hop]
                if cost < min_cost:
                    min_cost = cost
                    best_next_hop = next_hop
            
            # Update routing table if there's a change
            old_entry = self.routing_table.get(dest, (None, float('inf')))
            if old_entry[1] != min_cost or old_entry[0] != best_next_hop:
                self.routing_table[dest] = (best_next_hop, min_cost)
                self.next_hop_for_dest[dest] = best_next_hop
                changed = True
        
        # Check if next hop changes for poisoned reverse
        return changed or old_next_hop_for_dest != self.next_hop_for_dest
    
    def print_routing_table(self):
        print(f"Routing Table of router {self.name}:")
        for dest in sorted(self.routing_table.keys()):
            next_hop, cost = self.routing_table[dest]
            if cost == float('inf'):
                print(f"{dest},INF,INF")
            else:
                print(f"{dest},{next_hop},{cost}")
        print()
    
    def get_distance_vector(self):
        dv = {}
        for dest, (next_hop, cost) in self.routing_table.items():
            dv[dest] = cost
        return dv
    
    def get_poisoned_distance_vector(self, to_neighbor):
        """Create a poisoned distance vector for a specific neighbor"""
        dv = {}
        
        for dest, (next_hop, cost) in self.routing_table.items():
            # If we route through this neighbor to get to dest, poison the route
            if next_hop == to_neighbor:
                dv[dest] = float('inf')  # Poisoned route
            else:
                dv[dest] = cost
        
        return dv


class Network:
    def __init__(self):
        self.routers = {}  # {router_name: Router}
    
    def add_router(self, router_name):
        if router_name not in self.routers:
            self.routers[router_name] = Router(router_name)
    
    def update_link(self, router1, router2, cost):
        # Make sure both routers exist
        self.add_router(router1)
        self.add_router(router2)
        
        # Update link costs in both directions
        self.routers[router1].update_neighbor_cost(router2, cost)
        self.routers[router2].update_neighbor_cost(router1, cost)
    
    def initialize_distance_tables(self):
        all_router_names = list(self.routers.keys())
        for router in self.routers.values():
            router.initialize_distance_table(all_router_names)
    
    def run_distance_vector(self):
        time_step = 0
        changes = True  # Initial run always shows tables
        
        # Initialize routing tables
        for router in self.routers.values():
            router.update_routing_table()
        
        # Print initial distance tables
        for name in sorted(self.routers.keys()):
            self.routers[name].print_distance_table(time_step)
        
        while changes:
            time_step += 1
            changes = False
            
            # Exchange poisoned distance vectors
            for router_name, router in self.routers.items():
                for neighbor in router.neighbors:
                    # Get poisoned distance vector for this neighbor
                    poisoned_dv = router.get_poisoned_distance_vector(neighbor)
                    neighbor_router = self.routers[neighbor]
                    neighbor_cost = router.neighbors[neighbor]
                    
                    # Update neighbor's distance table based on this poisoned DV
                    for dest, cost in poisoned_dv.items():
                        if dest != neighbor:  # Don't consider path to self
                            if cost == float('inf'):
                                new_cost = float('inf')  # Keep poisoned route as infinity
                            else:
                                new_cost = cost + neighbor_cost
                            
                            if dest not in neighbor_router.distance_table:
                                neighbor_router.distance_table[dest] = {}
                            
                            # Update the cost via this neighbor
                            neighbor_router.distance_table[dest][router_name] = new_cost
            
            # Update routing tables and check for changes
            for router in self.routers.values():
                if router.update_routing_table():
                    changes = True
            
            # Print distance tables for this time step
            if changes:
                for name in sorted(self.routers.keys()):
                    self.routers[name].print_distance_table(time_step)
        
        # Print final routing tables
        for name in sorted(self.routers.keys()):
            self.routers[name].print_routing_table()
        
        return time_step


def main():
    network = Network()
    
    # Parse input
    routers = []
    line = input().strip()
    
    # Read router names
    while line != "START":
        routers.append(line)
        line = input().strip()
    
    # Add routers to the network
    for router in routers:
        network.add_router(router)
    
    # Read initial topology
    line = input().strip()
    while line != "UPDATE":
        parts = line.split()
        router1, router2, cost = parts[0], parts[1], int(parts[2])
        network.update_link(router1, router2, cost)
        line = input().strip()
    
    # Initialize distance tables and run DV algorithm
    network.initialize_distance_tables()
    network.run_distance_vector()
    
    # Process updates
    updates = []
    line = input().strip()
    while line != "END":
        updates.append(line)
        line = input().strip()
    
    # If there are updates, apply them and run DV algorithm again
    if updates:
        for update in updates:
            parts = update.split()
            if len(parts) == 3:  # Valid update line
                router1, router2, cost = parts[0], parts[1], int(parts[2])
                network.update_link(router1, router2, cost)
        
        # Reset and re-run
        network.initialize_distance_tables()
        network.run_distance_vector()


if __name__ == "__main__":
    main()