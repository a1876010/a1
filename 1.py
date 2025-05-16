#!/usr/bin/env python3

class Router:
    def __init__(self, name):
        self.name = name
        self.neighbors = {}  # {neighbor_name: cost}
        self.distance_table = {}  # {dest: {next_hop: cost}}
        self.routing_table = {}  # {dest: (next_hop, cost)}

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
        # Initialize distance table with direct neighbors
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
                changed = True
        
        return changed
    
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
        for dest, (_, cost) in self.routing_table.items():
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
        converged = False
        
        # Print initial distance tables
        for name in sorted(self.routers.keys()):
            self.routers[name].print_distance_table(time_step)
        
        while not converged:
            time_step += 1
            converged = True
            
            # Step 1: Each router computes its routing table
            routing_table_changes = []
            for router in self.routers.values():
                changed = router.update_routing_table()
                routing_table_changes.append(changed)
            
            if any(routing_table_changes):
                converged = False
            
            # Step 2: Exchange distance vectors
            distance_vectors = {}
            for name, router in self.routers.items():
                distance_vectors[name] = router.get_distance_vector()
            
            # Step 3: Update distance tables based on received DVs
            for router_name, router in self.routers.items():
                for neighbor in router.neighbors:
                    neighbor_dv = distance_vectors[neighbor]
                    neighbor_cost = router.neighbors[neighbor]
                    
                    for dest, cost in neighbor_dv.items():
                        if dest != router_name:  # Don't consider path to self
                            new_cost = neighbor_cost + cost
                            
                            if dest not in router.distance_table:
                                router.distance_table[dest] = {}
                            
                            # Update the cost via this neighbor
                            router.distance_table[dest][neighbor] = new_cost
            
            # Print distance tables for this time step
            if not converged:
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
    line = input().strip()
    while line != "END":
        parts = line.split()
        if len(parts) == 3:  # Valid update line
            router1, router2, cost = parts[0], parts[1], int(parts[2])
            network.update_link(router1, router2, cost)
        line = input().strip()
    
    # Run DV algorithm again if there were updates
    if line == "END":
        network.initialize_distance_tables()
        network.run_distance_vector()


if __name__ == "__main__":
    main()