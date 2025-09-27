#!/usr/bin/env python3
"""
RootDown Valley - Stardew Valley Style Farming Game Launcher
"""

import sys
import subprocess
import os

def check_pygame():
    """Check if pygame is installed"""
    try:
        import pygame
        print(f"✅ Pygame {pygame.version.ver} is installed")
        return True
    except ImportError:
        print("❌ Pygame is not installed")
        print("Installing pygame...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
            print("✅ Pygame installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install pygame")
            return False

def main():
    """Main launcher function"""
    print("🌱 RootDown Valley - Stardew Valley Style Farming Game")
    print("=" * 50)
    
    # Check pygame installation
    if not check_pygame():
        print("Please install pygame manually: pip install pygame")
        return
    
    # Check if game file exists
    game_file = "stardew_valley_game.py"
    if not os.path.exists(game_file):
        print(f"❌ Game file {game_file} not found")
        return
    
    print("🚀 Starting RootDown Valley...")
    print("Controls:")
    print("  WASD/Arrow Keys: Move")
    print("  1-4: Select tools (Hoe, Water, Seeds, Harvest)")
    print("  Q-Y: Select seeds (Tomato, Corn, Carrot, Native, Grass)")
    print("  Space: Use tool")
    print("  N: Next day")
    print("  ESC: Close game")
    print("\nPress Enter to start...")
    input()
    
    try:
        # Run the game
        subprocess.run([sys.executable, game_file])
    except KeyboardInterrupt:
        print("\n👋 Thanks for playing RootDown Valley!")
    except Exception as e:
        print(f"❌ Error running game: {e}")

if __name__ == "__main__":
    main()
