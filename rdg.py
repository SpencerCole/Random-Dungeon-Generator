import argparse
import os
import random
import sys
import time

class bcolors:
  RED='\033[31m'
  GREEN='\033[32m'
  ORANGE='\033[33m'
  BLUE='\033[34m'
  PURPLE='\033[35m'
  CYAN='\033[36m'
  LIGHTGREY='\033[37m'
  DARKGREY='\033[90m'
  LIGHTRED='\033[91m'
  LIGHTGREEN='\033[92m'
  YELLOW='\033[93m'
  LIGHTBLUE='\033[94m'
  PINK='\033[95m'
  LIGHTCYAN='\033[96m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  ENDC = '\033[0m'

class Hero(object):
  def __init__(self, y=None, x=None, health=20, inventory=[], status=[]):
    self.y = y
    self.x = x
    self.health = health
    self.inventory = inventory
    self.status = status
    # Strength, Constitution, Dexterity, Intelligence, Wisdom, Charisma
    self.stats = {
      'str': 3, # Strength - Melee Damage
      'con': 3, # Stamina - Hit Points
      'dex': 3, # Dexterity - Speed
      'int': 3, # Intellect - Spell Damage
      'wis': 3, # Wisdom - Mana Points
      'cha': 3, # Charisma - Bartering Selling / Buying
      'luk': 0, # Luck
    }

class Maze(object):

  def __init__(self, width=None, height=None):
    self.width = width * 2
    self.height = height * 2
    self.mapping = {'[0, 0]': '  ', # Empty
                    '[0, 1]': ' .', # Floor
                    '[0, 2]': ' #', # Wall
                    '[0, 3]': ' +', # Locked Door
                    '[0, 4]': ' \'', # Unlocked Door
                    '[0, 5]': ' C', # Chest
                    '[0, 6]': ' S', # Secret
                    '[0, 7]': ' T', # Trap
                    '[0, 8]': ' M', # Mob
                    '[0, 9]': ' >', # Up Stairs
                    '[0, 10]': ' <', # Down Stairs
                    }
    self.previous_cells = []
    self.visited_cells = {}
    self.current_cell = (1, 1)
    self.visited_cells[self.current_cell] = True
    self.previous_cells.append(self.current_cell)
    self.seed = int(time.time())
    random.seed(self.seed)
    self.level = 1
    self.shown_tiles = []
    self.rooms = {}
    self.chests = {}
    self.traps = {}
    self.mobs = {}
    self.loot = {}
    self.exits = {}
    self.hero = Hero()
    self._generate()


  def getMazeCell(self, y, x, i=0):
    if i:
      return self.maze.get(str(y), {}).get(str(x))[1]
    else:
      return self.maze.get(str(y), {}).get(str(x), {})


  def setMazeCell(self, y, x, v):
    if type(v) == int:
      self.maze[str(y)][str(x)][1] = v
    else:
      self.maze[str(y)][str(x)] = v



  def _generate(self):
    self._buildBase()
    self._placeRooms()
    self._placeDoors()
    self._placePaths()
    self._cleanPaths()
    self._placeExits()
    self._placeTraps()
    self._placeChests()
    self._placeLoot()
    self._placeMobs()


  def _buildBase(self):
    # Build basic maze form
    self.maze = {}
    for row in range(self.height + 1):
      maze_row = {}
      for col in range(self.width + 1):
        # Walls on the borders
        if row == 0 or row == self.height:
          maze_row[str(col)] = list([0, 2])
          self.visited_cells[(row, col)] = True
        # Walls on the borders
        elif col == 0 or col == self.width:
          maze_row[str(col)] = list([0, 2])
          self.visited_cells[(row, col)] = True
        else:
          maze_row[str(col)] = list([0, 0])
      self.maze[str(row)] = maze_row


  def _placeRooms(self):
    # Place Rooms Randomly
    num_rooms = (self.width * self.height)
    while num_rooms > 0:
      room_ok = False
      while not room_ok and num_rooms > 0:
        num_rooms -= 1
        # Choose point
        room_x = random.randrange(2, self.width - 2, 2)
        room_y = random.randrange(2, self.height - 2, 2)
        # Choose size
        rand_width = random.randrange(2, 8, 2) + 3
        rand_height = random.randrange(2, 8, 2) + 3


        def _checkFit(ry, rx, yw, xw):
          """Checks to make sure all the rooms cells are in the map."""
          for y in range(yw + 1):
            for x in range(xw + 1):
              if self.getMazeCell(y + ry, x + rx, 1) != 0:
                return False
          return True

        # If it will fit then its okay.
        room_ok = _checkFit(room_y, room_x, rand_height, rand_width)
        if room_y + rand_height >= self.height or room_x + rand_width >= self.width:
          room_ok = False
      if room_ok:
        self._drawRoom(room_y, room_x, rand_height, rand_width)


  def _drawRoom(self, room_y, room_x, rand_height, rand_width):
    # TODO(spencercole) Add special rooms here. Library, Trapped Room, etc...
    for y in range(rand_height):
      for x in range(rand_width):
        self.visited_cells[(y + room_y, x + room_x)] = True
        tile_type = 1 # Floor
        # If on the edge
        if y == 0 or x == 0 or y == rand_height - 1 or x == rand_width - 1:
          tile_type = 2 # Wall
        self.setMazeCell(y + room_y, x + room_x, tile_type)
    self.rooms[(room_y, room_x)] = {'width': rand_width, 'height': rand_height, 'doors': {}}


  def _placeDoors(self):
    # Add doors to rooms
    # TODO(spencercole) Lights? Bold #
    for room in self.rooms:
      # self.rooms[(room_y, room_x)] = {'width': rand_width, 'height': rand_height, 'doors': {}}
      if not self.rooms[room]['doors']:
        walls = [
          [0, random.randrange(1, self.rooms[room]['width'] - 1)], # Up
          [self.rooms[room]['height'] - 1, random.randrange(1, self.rooms[room]['width'] - 1)], # Down
          [random.randrange(1, self.rooms[room]['height'] - 1), 0], # Left
          [random.randrange(1, self.rooms[room]['height'] - 1), self.rooms[room]['width'] - 1] # Right
        ]

        wall = random.choice(walls)
        door_type = random.randint(0, 100)
        if door_type < 10:
          # Secret Door
          self.setMazeCell(room[0] + wall[0], room[1] + wall[1], 6)
          self.rooms[room]['doors'][(wall[0], wall[1])] = 6
        elif 10 < door_type < 20:
          # Locked Door
          self.setMazeCell(room[0] + wall[0], room[1] + wall[1], 3)
          self.rooms[room]['doors'][(wall[0], wall[1])] = 3
        else:
          # Unlocked Door
          self.setMazeCell(room[0] + wall[0], room[1] + wall[1], 4)
          self.rooms[room]['doors'][(wall[0], wall[1])] = 4


  def _placePaths(self):
    # Generate Pathways (Maze Generator)
    while self.previous_cells:
      neighbor= self._chooseNeighbor()
      # choose random neighbor thats not been visited
      if neighbor:
        # remove wall between
        self._removeWall(neighbor)
        # push current cell to previous stack
        if self.current_cell not in self.previous_cells:
          self.previous_cells.append(self.current_cell)
        self.current_cell = tuple(neighbor[:2])
        # make new cell the current cell and mark it as visited
        if not self.visited_cells.get(self.current_cell):
          self.visited_cells[self.current_cell] = True
      #if no neighbor and the stack is not empty
      else:
        self.current_cell = self.previous_cells.pop()


  def _chooseNeighbor(self):
    unvisited_neighbors = []
    neighbors = [[self.current_cell[0] - 2, self.current_cell[1], 'up'],
                 [self.current_cell[0] + 2, self.current_cell[1], 'dn'],
                 [self.current_cell[0], self.current_cell[1] - 2, 'lt'],
                 [self.current_cell[0], self.current_cell[1] + 2, 'rt']]

    for n in neighbors:
      if not self.visited_cells.get(tuple(n[:2])) and self.maze.get(str(n[0]), {}).get(str(n[1])):
        unvisited_neighbors.append(n)

    return random.choice(unvisited_neighbors) if unvisited_neighbors else None


  def _removeWall(self, cell):
    # Set all squares to X
    for y in range(2):
      for x in range(2):
        if self.getMazeCell(self.current_cell[0] + y - 1, self.current_cell[1] + x - 1, 1) == 0:
          self.setMazeCell(self.current_cell[0] + y - 1, self.current_cell[1] + x - 1, 2) # Wall
        if self.getMazeCell(cell[0] + y - 1, cell[1] + x - 1, 1) == 0:
          self.setMazeCell(cell[0] + y - 1, cell[1] + x - 1, 2) # Wall

    extended_neighbor = []

    # up
    #   _ O _
    #  |X|O|X|
    #  |X|O|X|
    #  |X|X|X|
    #
    if cell[-1] == 'up':
        # bottom center
      self.setMazeCell(cell[0] + 1, cell[1], 1) # Floor
        # center top
      self.setMazeCell(self.current_cell[0] - 1, self.current_cell[1], 1) # Floor
      if self.getMazeCell(cell[0] - 3, cell[1]):
        extended_neighbor = [cell[0] - 3, cell[1]]

    # dn
    #   _ _ _
    #  |X|X|X|
    #  |X|O|X|
    #  |X|O|X|
    #     O
    if cell[-1] == 'dn':
        # top center
      self.setMazeCell(cell[0] - 1, cell[1], 1) # Floor
        # center bottom
      self.setMazeCell(self.current_cell[0] + 1, self.current_cell[1], 1) # Floor
      if self.getMazeCell(cell[0] + 3, cell[1]):
        extended_neighbor = [cell[0] + 3, cell[1]]

    # lt
    #   _ _ _
    #  |X|X|X|
    # O|O|O|X|
    #  |X|X|X|
    #
    if cell[-1] == 'lt':
        # right center
      self.setMazeCell(cell[0], cell[1] + 1, 1) # Floor
        # center left
      self.setMazeCell(self.current_cell[0], self.current_cell[1] - 1, 1) # Floor
      if self.getMazeCell(cell[0], cell[1] - 3):
        extended_neighbor = [cell[0], cell[1] - 3]

    # rt
    #   _ _ _
    #  |X|X|X|
    #  |X|O|O|O
    #  |X|X|X|
    #
    if cell[-1] == 'rt':
        # left center
      self.setMazeCell(cell[0], cell[1] - 1, 1) # Floor
        # center right
      self.setMazeCell(self.current_cell[0], self.current_cell[1] + 1, 1) # Floor
      if self.getMazeCell(cell[0], cell[1] + 3):
        extended_neighbor = [cell[0], cell[1] + 3]

    # Set current cell and the next cell to a floor tile
    self.setMazeCell(self.current_cell[0], self.current_cell[1], 1) # Floor
    self.setMazeCell(cell[0], cell[1], 1) # Floor

    # No perfect maze maker. Randomly change a cell to '.'
    if random.randint(0, 1) == 0:
      if extended_neighbor:
        if not self.visited_cells.get(tuple(extended_neighbor)):
          self.setMazeCell(extended_neighbor[0], extended_neighbor[1], 1) # Floor
          self.visited_cells[tuple(extended_neighbor)] = True


  def _cleanPaths(self):
    # Remove dead ends (Anything with 3 sides.)
    # Also remove walls that block doors
    removed_one = True
    while removed_one:
      removed_one = False
      for y in range(self.height + 1):
        for x in range(self.width + 1):
          if self.getMazeCell(y, x, 1) in [1, 3, 4, 6]: # Floor, Locked Door, Unlocked Door, Secret Door
            #      up, dn, lt, rt
            sides = [0, 0, 0, 0]
            if self.getMazeCell(y - 1, x, 1) in [0, 2]: # Empty or Wall
              sides[0] = 1
            if self.getMazeCell(y + 1, x, 1) in [0, 2]:
              sides[1] = 1
            if self.getMazeCell(y, x - 1, 1) in [0, 2]:
              sides[2] = 1
            if self.getMazeCell(y, x + 1, 1) in [0, 2]:
              sides[3] = 1

            if sides.count(1) >= 3:
              if self.getMazeCell(y, x, 1) in [3, 4, 6]: # Locked Door, Unlocked Door, Secret Door
                # up down
                if sides[:2] == [1, 1]:
                  if sides[2] == 1:
                    self.setMazeCell(y, x - 1, 1) # Floor
                  if sides[3] == 1:
                    self.setMazeCell(y, x + 1, 1) # Floor

                # left right
                if sides[2:] == [1, 1]:
                  if sides[0] == 1:
                    self.setMazeCell(y - 1, x, 1) # Floor
                  if sides[1] == 1:
                    self.setMazeCell(y + 1, x, 1) # Floor

              # If its a floor tile
              if self.getMazeCell(y, x, 1) in [1]: # Floor
                self.setMazeCell(y, x, 2) # Wall
                removed_one = True


  def _placeExits(self):
    if not self.exits:
      while len(self.exits) < 2:
        coor = random.choice(self.rooms.keys())
        room = self.rooms[coor]
        stair_x = (room['width']) / 2
        stair_y = (room['height']) / 2
        # If cell not in locked/ secret room.
        # 4: Unlocked Door
        if (4 not in self.rooms[coor]['doors'].values() or
            self.getMazeCell(coor[0] + stair_y, coor[1] + stair_x, 1) not in [1]): # Floor
          stair_x = None
          stair_y = None
        else:
          if self.exits:
            stair = 9 # Up Stairs
          else:
            stair = 10 # Down Stairs
          self.setMazeCell(coor[0] + stair_y, coor[1] + stair_x, stair)
          self.exits[(coor[0] + stair_y, coor[1] + stair_x)] = stair

  def _placeTraps(self):
    #self.traps = {}
    for y in range(self.height + 1):
        for x in range(self.width + 1):
          chance = 200 - self.level if self.level < 190 else 10
          if random.randint(0, chance) == 0:
            if self.getMazeCell(y, x, 1) in [1]: # Floor
              self.setMazeCell(y, x, 7) # Trap
              self.traps[(y, x)] = True

  def _placeChests(self):
    #self.chests = {}
    for y in range(self.height + 1):
        for x in range(self.width + 1):
          chance = 200 + self.level
          if (random.randint(0, chance) == 0 or
              set([3, 6]).intersection(self.rooms.get((y, x), {'doors': {}})['doors'].values())):
            chest_x = None
            chest_y = None
            while chest_y is None and chest_x is None:
              coor = random.choice(self.rooms.keys())
              room = self.rooms[coor]
              chest_x = random.randrange(1, room['width'] - 2)
              chest_y = random.randrange(1, room['height'] - 2)
            if self.getMazeCell(coor[0] + chest_y, coor[1] + chest_x, 1) not in [1]: # Floor
              chest_x = None
              chest_y = None
            else:
              self.setMazeCell(coor[0] + chest_y, coor[1] + chest_x, 5) # Chest
              self.chests[(coor[0] + chest_y, coor[1] + chest_x)] = True

  def _placeLoot(self):
    #self.loot = {}
    # Gold, Potions, Gear, Scrolls, Keys, Bones
    for y in range(self.height + 1):
        for x in range(self.width + 1):
          chance = 200 + self.level
          if (random.randint(0, chance) == 0 or
              set([3, 6]).intersection(self.rooms.get((y, x), {'doors': {}})['doors'].values())):
            loot_x = None
            loot_y = None
            while loot_y is None and loot_x is None:
              coor = random.choice(self.rooms.keys())
              room = self.rooms[coor]
              loot_x = random.randrange(1, room['width'] - 2)
              loot_y = random.randrange(1, room['height'] - 2)
            if self.getMazeCell(coor[0] + loot_y, coor[1] + loot_x, 1) not in [1]: # Floor
              loot_x = None
              loot_y = None
            else:
              loot_types = {
                'gold': 20,
                'potion': 21,
                'gear': 22,
                'weapon': 23,
                'scroll': 24,
                'key': 25,
                'bones': 26
              }
              loot_type = random.choice(loot_types.keys())
              loot = loot_types[loot_type]
              self.setMazeCell(coor[0] + loot_y, coor[1] + loot_x, loot) # Chest
              self.loot[(coor[0] + loot_y, coor[1] + loot_x)] = loot

  def _placeMobs(self):
    pass
    #self.mobs = {}
    # Each room should have 0 - 3 mobs in it.
    # The game will randomly add one every X steps as well.


  def _translate(self, num):
    color_mapping = {
      '[0, 0]': '  ', # Empty
      '[0, 1]': bcolors.BOLD + ' .' + bcolors.ENDC, # Floor
      '[0, 2]': bcolors.LIGHTBLUE + ' #' + bcolors.ENDC, # Wall
      '[0, 3]': bcolors.RED + ' +' + bcolors.ENDC, # Locked Door
      '[0, 4]': bcolors.GREEN + ' \'' + bcolors.ENDC, # Unlocked Door
      '[0, 5]': bcolors.ORANGE + ' C' + bcolors.ENDC, # Chest
      '[0, 6]': bcolors.PINK + ' S' + bcolors.ENDC, # Secret
      '[0, 7]': bcolors.LIGHTRED + ' T' + bcolors.ENDC, # Trap
      '[0, 8]': bcolors.CYAN + ' M' + bcolors.ENDC, # Mob
      '[0, 9]': bcolors.LIGHTGREY + ' <' + bcolors.ENDC, # Up Stairs
      '[0, 10]': bcolors.LIGHTGREY + ' >' + bcolors.ENDC, # Down Stairs
      '[0, 20]': bcolors.YELLOW + ' $' + bcolors.ENDC, # Loot: Gold
      '[0, 21]': bcolors.PURPLE + ' P' + bcolors.ENDC, # Loot: Potion
      '[0, 22]': bcolors.PURPLE + ' &' + bcolors.ENDC, # Loot: Gear
      '[0, 23]': bcolors.PURPLE + ' |' + bcolors.ENDC, # Loot: Weapon
      '[0, 24]': bcolors.PURPLE + ' -' + bcolors.ENDC, # Loot: Scroll
      '[0, 25]': bcolors.PURPLE + ' ~' + bcolors.ENDC, # Loot: Key
      '[0, 26]': bcolors.PURPLE + ' %' + bcolors.ENDC, # Loot: Bones
    }

    #if num not in self.shown_tiles:
    #  # write black tile, or dont at all.
    #  return color_mapping['[0, 0]']
    #else:
      # draw tile normally
    return color_mapping[str(num)]


  def _mazeString(self):
    self.maze_display_buf = ''

    for i in sorted(self.maze.iterkeys(), key=int):
      for x in sorted(self.maze[i].iterkeys(), key=int):
        col = self.getMazeCell(i, x)
        self.maze_display_buf += (self._translate(col))
      self.maze_display_buf += '\n'


  def draw(self):
    self._mazeString()
    os.system('clear')
    sys.stdout.write(self.maze_display_buf)
    sys.stdout.flush()


def main():
  parser = argparse.ArgumentParser(description='Random Maze Generator')
  parser.add_argument('--width', required=True, type=int, help='(X > 1) an integer for the width of the maze.')
  parser.add_argument('--height', required=True, type=int, help='(X > 1) an integer for the height of the maze.')
  args = parser.parse_args()

  m = Maze(width=args.width, height=args.height)

  m.draw()

if __name__ == '__main__':
  main()
