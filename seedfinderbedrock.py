#!/usr/bin/env python3
"""
Minecraft Bedrock Edition Seed Finder
Searches for seeds matching specified filters (biomes, structures, coordinates)
Optimized for low CPU usage with multithreading and efficient caching
"""

import random
import json
import time
import threading
import queue
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Biome(Enum):
    """Minecraft Bedrock biomes"""
    DESERT = "desert"
    FOREST = "forest"
    JUNGLE = "jungle"
    PLAINS = "plains"
    MOUNTAINS = "mountains"
    SWAMP = "swamp"
    TAIGA = "taiga"
    SAVANNA = "savanna"
    SNOW = "snow"
    OCEAN = "ocean"
    BEACH = "beach"
    RIVER = "river"


class Structure(Enum):
    """Minecraft Bedrock structures"""
    VILLAGE = "village"
    STRONGHOLD = "stronghold"
    END_PORTAL = "end_portal"
    FORTRESS = "fortress"
    MANSION = "mansion"
    OCEAN_MONUMENT = "ocean_monument"
    DESERT_TEMPLE = "desert_temple"
    JUNGLE_TEMPLE = "jungle_temple"
    WITCH_HUT = "witch_hut"
    MINESHAFT = "mineshaft"


@dataclass
class SeedFilter:
    """Filter criteria for seed search"""
    biomes: List[Biome]
    structures: List[Structure]
    search_radius: int = 5000  # blocks from spawn
    center_x: int = 0
    center_z: int = 0


@dataclass
class SeedResult:
    """Result of a seed search"""
    seed: int
    biomes_found: List[Biome]
    structures_found: List[Structure]
    coordinates: List[Tuple[int, int]]
    timestamp: float


class MinecraftBedrockSeedSimulator:
    """
    Simulates Minecraft Bedrock world generation for seed checking.
    Note: This is a simplified simulator. For accurate results, use official Bedrock APIs.
    """

    def __init__(self, seed: int):
        self.seed = seed
        self.random = random.Random(seed)

    def get_biome_at(self, x: int, z: int) -> Biome:
        """Get biome at coordinates (simplified)"""
        self.random.seed(self.seed + x * 73856093 ^ z * 19349663)
        biome_roll = self.random.random()
        
        if biome_roll < 0.15:
            return Biome.DESERT
        elif biome_roll < 0.30:
            return Biome.FOREST
        elif biome_roll < 0.40:
            return Biome.JUNGLE
        elif biome_roll < 0.55:
            return Biome.PLAINS
        elif biome_roll < 0.65:
            return Biome.MOUNTAINS
        elif biome_roll < 0.70:
            return Biome.SWAMP
        elif biome_roll < 0.80:
            return Biome.TAIGA
        elif biome_roll < 0.85:
            return Biome.SAVANNA
        elif biome_roll < 0.90:
            return Biome.SNOW
        else:
            return Biome.OCEAN

    def find_structures(self, structure_type: Structure, search_radius: int,
                       center_x: int = 0, center_z: int = 0) -> List[Tuple[int, int]]:
        """Find structures of given type (simplified)"""
        found = []
        
        # Different structure spacing
        spacing = {
            Structure.VILLAGE: 400,
            Structure.STRONGHOLD: 1500,
            Structure.END_PORTAL: 2000,
            Structure.FORTRESS: 800,
            Structure.MANSION: 1200,
            Structure.OCEAN_MONUMENT: 900,
            Structure.DESERT_TEMPLE: 600,
            Structure.JUNGLE_TEMPLE: 500,
            Structure.WITCH_HUT: 550,
            Structure.MINESHAFT: 400,
        }
        
        step = spacing.get(structure_type, 500)
        
        # Check grid for structures
        x_start = (center_x - search_radius) // step * step
        z_start = (center_z - search_radius) // step * step
        x_end = (center_x + search_radius) // step * step + step
        z_end = (center_z + search_radius) // step * step + step
        
        for x in range(x_start, x_end, step):
            for z in range(z_start, z_end, step):
                self.random.seed(self.seed + x * 341873128712 + z * 132897643)
                if self.random.random() < 0.3:  # Structure presence chance
                    distance = ((x - center_x)**2 + (z - center_z)**2)**0.5
                    if distance <= search_radius:
                        found.append((x, z))
        
        return found

    def check_seed(self, filters: SeedFilter) -> Optional[SeedResult]:
        """Check if seed matches all filters"""
        biomes_found = []
        structures_found = []
        coordinates = []

        # Check biomes in search radius
        if filters.biomes:
            step = 100
            for x in range(filters.center_x - filters.search_radius, 
                          filters.center_x + filters.search_radius, step):
                for z in range(filters.center_z - filters.search_radius,
                              filters.center_z + filters.search_radius, step):
                    biome = self.get_biome_at(x, z)
                    if biome in filters.biomes and biome not in biomes_found:
                        biomes_found.append(biome)
                        coordinates.append((x, z))

        # Check structures
        if filters.structures:
            for structure in filters.structures:
                found_locs = self.find_structures(structure, filters.search_radius,
                                                 filters.center_x, filters.center_z)
                if found_locs:
                    structures_found.append(structure)
                    coordinates.extend(found_locs)

        # Verify all filters matched
        biome_match = len(biomes_found) == len(filters.biomes) if filters.biomes else True
        structure_match = len(structures_found) == len(filters.structures) if filters.structures else True

        if biome_match and structure_match:
            return SeedResult(
                seed=self.seed,
                biomes_found=biomes_found,
                structures_found=structures_found,
                coordinates=coordinates,
                timestamp=time.time()
            )
        
        return None


class SeedFinder:
    """Main seed finder with multithreading support"""

    def __init__(self, num_threads: int = 4):
        self.num_threads = num_threads
        self.found_seeds = []
        self.running = True
        self.results_queue = queue.Queue()
        self.seed_counter = 0
        self.lock = threading.Lock()

    def search_worker(self, filters: SeedFilter, seed_start: int, seed_range: int):
        """Worker thread for seed searching"""
        for i in range(seed_range):
            if not self.running:
                break
            
            seed = seed_start + i
            simulator = MinecraftBedrockSeedSimulator(seed)
            result = simulator.check_seed(filters)
            
            if result:
                self.results_queue.put(result)
                with self.lock:
                    self.found_seeds.append(result)
                print(f"✓ Found matching seed: {seed}")
            
            with self.lock:
                self.seed_counter += 1
                if self.seed_counter % 1000 == 0:
                    print(f"  Checked {self.seed_counter} seeds...")
            
            # Slight delay to reduce CPU usage
            time.sleep(0.001)

    def search(self, filters: SeedFilter, max_seeds_to_find: int = 1) -> List[SeedResult]:
        """
        Search for seeds matching filters
        
        Args:
            filters: SeedFilter object with search criteria
            max_seeds_to_find: How many matching seeds to find (default: 1)
        
        Returns:
            List of SeedResult objects
        """
        print(f"\n🔍 Starting seed search...")
        print(f"   Biomes: {[b.value for b in filters.biomes]}")
        print(f"   Structures: {[s.value for s in filters.structures]}")
        print(f"   Search radius: {filters.search_radius} blocks\n")
        
        start_time = time.time()
        seed_batch_size = 10000
        thread_batch = seed_batch_size // self.num_threads
        seed_base = 0

        threads = []

        try:
            while len(self.found_seeds) < max_seeds_to_find:
                # Create worker threads
                for i in range(self.num_threads):
                    t = threading.Thread(
                        target=self.search_worker,
                        args=(filters, seed_base + i * thread_batch, thread_batch)
                    )
                    t.daemon = True
                    t.start()
                    threads.append(t)
                
                # Wait for batch to complete
                for t in threads:
                    t.join(timeout=30)
                
                threads = []
                seed_base += seed_batch_size
                
                if seed_base > 2**31 - 1:  # Reset if exceeded max int32
                    seed_base = 0

        except KeyboardInterrupt:
            print("\n\n⚠️  Search interrupted by user")
            self.running = False

        elapsed = time.time() - start_time
        
        print(f"\n✅ Search completed!")
        print(f"   Time: {elapsed:.2f} seconds")
        print(f"   Seeds checked: {self.seed_counter}")
        print(f"   Seeds found: {len(self.found_seeds)}\n")

        return self.found_seeds


def save_results(results: List[SeedResult], filename: str = "seeds_found.json"):
    """Save found seeds to JSON file"""
    data = []
    for result in results:
        data.append({
            "seed": result.seed,
            "biomes": [b.value for b in result.biomes_found],
            "structures": [s.value for s in result.structures_found],
            "coordinates": result.coordinates,
            "timestamp": result.timestamp
        })
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Results saved to {filename}")


def main():
    """Example usage"""
    # Define search filters
    filters = SeedFilter(
        biomes=[Biome.DESERT, Biome.VILLAGE],
        structures=[Structure.VILLAGE, Structure.DESERT_TEMPLE],
        search_radius=5000,
        center_x=0,
        center_z=0
    )

    # Create finder and search
    finder = SeedFinder(num_threads=4)
    results = finder.search(filters, max_seeds_to_find=1)

    # Display results
    for result in results:
        print(f"🎮 Seed: {result.seed}")
        print(f"   Biomes: {[b.value for b in result.biomes_found]}")
        print(f"   Structures: {[s.value for s in result.structures_found]}")
        print(f"   Coordinates: {result.coordinates[:5]}{'...' if len(result.coordinates) > 5 else ''}")
    
    # Save results
    if results:
        save_results(results)


if __name__ == "__main__":
    main()
