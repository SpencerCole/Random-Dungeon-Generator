import argparse
import os
import random
import sys
import time
import timeit

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

class Maze(object):

  def __init__(self, width=None, height=None, speed=None, show_steps=None, no_print=None, seed=None):
    self.width = width * 2
    self.height = height * 2
    self.speed = speed
    self.show_steps = show_steps
    self.no_print = no_print
    self.mapping = {'[0, 0]': '  ', # Empty
                    '[0, 1]': ' .', # Floor
                    '[0, 2]': ' #', # Wall
                    '[0, 3]': ' +', # Locked Door
                    '[0, 4]': ' -', # Unlocked Door
                    '[0, 5]': ' C', # Chest
                    '[0, 6]': ' S', # Secret
                    '[0, 7]': ' T', # Trap
                    '[0, 8]': ' M', # Mob
                    }
    self.previous_cells = []
    self.visited_cells = {}
    self.rooms = {}
    self.current_cell = (1, 1)
    self.visited_cells[self.current_cell] = True
    self.previous_cells.append(self.current_cell)
    self.try_to_make_exit = False
    self.has_exit = False
    self.seed = seed or int(time.time())
    self.progress_pos = 0
    random.seed(self.seed)
    self._generate()


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
        if self.maze[str(self.current_cell[0] + y - 1)][str(self.current_cell[1] + x - 1)][1] == 0:
          self.maze[str(self.current_cell[0] + y - 1)][str(self.current_cell[1] + x - 1)][1] = 2
        if self.maze[str(cell[0] + y - 1)][str(cell[1] + x - 1)][1] == 0:
          self.maze[str(cell[0] + y - 1)][str(cell[1] + x - 1)][1] = 2

    extended_neighbor = []

    # up
    #   _ O _
    #  |X|O|X|
    #  |X|O|X|
    #  |X|X|X|
    #
    if cell[-1] == 'up':
        # bottom center
      self.maze[str(cell[0] + 1)][str(cell[1])][1] = 1
        # center top
      self.maze[str(self.current_cell[0] - 1)][str(self.current_cell[1])][1] = 1

      if self.maze.get(str(cell[0] + 3), {}).get(str(cell[1]), {}):
        extended_neighbor = [cell[0] + 3, cell[1]]
    # dn
    #   _ _ _
    #  |X|X|X|
    #  |X|O|X|
    #  |X|O|X|
    #     O
    if cell[-1] == 'dn':
        # top center
      self.maze[str(cell[0] - 1)][str(cell[1])][1] = 1
        # center bottom
      self.maze[str(self.current_cell[0] + 1)][str(self.current_cell[1])][1] = 1

      if self.maze.get(str(cell[0] - 3), {}).get(str(cell[1]), {}):
        extended_neighbor = [cell[0] - 3, cell[1]]
    # lt
    #   _ _ _
    #  |X|X|X|
    # O|O|O|X|
    #  |X|X|X|
    #
    if cell[-1] == 'lt':
        # right center
      self.maze[str(cell[0])][str(cell[1] + 1)][1] = 1
        # center left
      self.maze[str(self.current_cell[0])][str(self.current_cell[1] - 1)][1] = 1

      if self.maze.get(str(cell[0]), {}).get(str(cell[1] + 3), {}):
        extended_neighbor = [cell[0], cell[1] + 3]

    # rt
    #   _ _ _
    #  |X|X|X|
    #  |X|O|O|O
    #  |X|X|X|
    #
    if cell[-1] == 'rt':
        # left center
      self.maze[str(cell[0])][str(cell[1] - 1)][1] = 1
        # center right
      self.maze[str(self.current_cell[0])][str(self.current_cell[1] + 1)][1] = 1

      if self.maze.get(str(cell[0]), {}).get(str(cell[1] + 3), {}):
        extended_neighbor = [cell[0], cell[1] + 3]

    self.maze[str(self.current_cell[0])][str(self.current_cell[1])][1] = 1
    self.maze[str(cell[0])][str(cell[1])][1] = 1

    # No perfect maze maker. Randomly change a cell to '.'
    if random.randint(0, 1) == 0:
      if extended_neighbor:
        if not self.visited_cells.get(tuple(extended_neighbor)):
          self.maze[str(extended_neighbor[0])][str(extended_neighbor[1])][1] = 1
          self.visited_cells[tuple(extended_neighbor)] = True



  def _generate(self):
    # Build basic maze form
    self.maze = {}
    for row in range(self.height + 1):
      maze_row = {}
      for col in range(self.width + 1):
        if row == 0 or row == self.height:
          maze_row[str(col)] = list([0, 2])
          self.visited_cells[(row, col)] = True
        elif col == 0 or col == self.width:
          maze_row[str(col)] = list([0, 2])
          self.visited_cells[(row, col)] = True
        else:
          maze_row[str(col)] = list([0, 0])
      self.maze[str(row)] = maze_row

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
              if self.maze[str(ry + y)][str(rx + x)][1] != 0:
                return False
          return True

        # If it will fit then its okay.
        room_ok = _checkFit(room_y, room_x, rand_height, rand_width)
        if room_y + rand_height >= self.height or room_x + rand_width >= self.width:
          room_ok = False
      if room_ok:
        self._drawRoom(room_y, room_x, rand_height, rand_width)

        if self.show_steps:
          self._print()
          time.sleep(self.speed * 10)

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

      if self.show_steps:
        self._print()
        time.sleep(self.speed)

    # Remove dead ends (Anything with 3 sides.)
    # Also remove walls that block doors
    removed_one = True
    while removed_one:
      removed_one = False
      for y in range(self.height + 1):
        for x in range(self.width + 1):
          if self.maze[str(y)][str(x)][1] in [1, 3]:
            #      up, dn, lt, rt
            sides = [0, 0, 0, 0]
            if self.maze[str(y - 1)][str(x)][1] in [0, 2]:
              sides[0] = 1
            if self.maze[str(y + 1)][str(x)][1] in [0, 2]:
              sides[1] = 1
            if self.maze[str(y)][str(x - 1)][1] in [0, 2]:
              sides[2] = 1
            if self.maze[str(y)][str(x + 1)][1] in [0, 2]:
              sides[3] = 1

            if sides.count(1) >= 3:
              # If its a floor tile
              if self.maze[str(y)][str(x)][1] in [1]:
                self.maze[str(y)][str(x)][1] = 2
                removed_one = True

              # If its a locked door tile
              if self.maze[str(y)][str(x)][1] in [3]:
                # up down
                if sides[:2] == [1, 1]:
                  if sides[2] == 1:
                    self.maze[str(y)][str(x - 1)][1] = 1
                  if sides[3] == 1:
                    self.maze[str(y)][str(x + 1)][1] = 1

                # left right
                if sides[2:] == [1, 1]:
                  if sides[0] == 1:
                    self.maze[str(y - 1)][str(x)][1] = 1
                  if sides[1] == 1:
                    self.maze[str(y + 1)][str(x)][1] = 1

              if self.show_steps:
                self._print()
                time.sleep(self.speed * 10)


    #TODO(spencercole): Add dungeon things. Chests, Traps, Mobs.

    if not self.no_print:
      self._print()
      self._write()


  def _drawRoom(self, room_y, room_x, rand_height, rand_width):
    room_has_door = False
    for y in range(rand_height):
      for x in range(rand_width):
        self.rooms[(room_y + y, room_x + x)] = True
        self.visited_cells[(room_y + y, room_x + x)] = True

        #'[0, 0]': '  ', # Empty
        #'[0, 1]': ' .', # Floor
        #'[0, 2]': ' #', # Wall
        #'[0, 3]': ' +', # Locked Door
        #'[0, 4]': ' -', # Unlocked Door
        #'[0, 5]': ' C', # Chest
        #'[0, 6]': ' S', # Secret
        #'[0, 7]': ' T', # Trap
        #'[0, 8]': ' M', # Mob

        #TODO(spencercole): Add other room related things. Secret Doors, Locked/ Unlocked.
        if room_has_door:
          # Rare chance to add another door to the roo,m
          chance = 80
        else:
          chance = 10
        make_door = random.randint(0, chance)

        # last spot to put a door
        if not room_has_door:
          if y == rand_height - 1 and x == rand_width - 2:
            make_door = 0

        tile_type = 1 # Floor
        # If on the edge
        if y == 0 or x == 0 or y == rand_height - 1 or x == rand_width - 1:
          tile_type = 2 # Wall
          # If not on a corner
          if not (y == 0 and x ==0) and not (y ==0 and x == rand_width - 1) and not (y == rand_height - 1 and x == 0) and not (y == rand_height - 1 and x == rand_width - 1):
            if make_door == 0:
              tile_type = 3 # Locked Door
              room_has_door = True

        self.maze[str(room_y + y)][str(room_x + x)][1] = tile_type


  def _write(self):
    filename = '{} x {} - {}.txt'.format(self.width, self.height, time.ctime())
    file = open(filename, 'w')
    file.write(self.maze_text_buf)
    file.write('Seed: '+ str(self.seed))
    file.close()

  def _translate(self, num):
    return self.mapping[num]

  def _mazeString(self):
    self.maze_display_buf = ''
    self.maze_text_buf = ''
    color_mapping = {'[0, 0]': '  ', # Empty
             '[0, 1]': bcolors.BOLD + ' .' + bcolors.ENDC, # Floor
             '[0, 2]': bcolors.BLUE + ' #' + bcolors.ENDC, # Wall
             '[0, 3]': bcolors.RED + ' +' + bcolors.ENDC, # Locked Door
             '[0, 4]': bcolors.GREEN + ' -' + bcolors.ENDC, # Unlocked Door
             '[0, 5]': ' C', # Chest
             '[0, 6]': ' S', # Secret
             '[0, 7]': ' T', # Trap
             '[0, 8]': ' M', # Mob
             }
    for i in sorted(self.maze.iterkeys(), key=int):
      for x in sorted(self.maze[i].iterkeys(), key=int):
        col = self.maze[i][x]
        self.maze_text_buf += self._translate(str(col))
        self.maze_display_buf += (color_mapping[str(col)])
      self.maze_display_buf += '\n'
      self.maze_text_buf += '\n'





  def _print(self):
    self._mazeString()
    os.system('clear')
    sys.stdout.write(self.maze_display_buf)
    sys.stdout.flush()


def main():
  parser = argparse.ArgumentParser(description='Random Maze Generator')
  parser.add_argument('--width', required=True, type=int, help='(X > 1) an integer for the width of the maze.')
  parser.add_argument('--height', required=True, type=int, help='(X > 1) an integer for the height of the maze.')
  parser.add_argument('--seed', type=int, help='an integer seed for the random module to generate the maze.')
  parser.add_argument('--speed', default=0.01, type=float, help='a float for the speed of the show_steps generation.')
  parser.add_argument('--show_steps', default=False, action='store_true', help='a flag to show the maze construction.')
  parser.add_argument('--no_print', default=False, action='store_true', help='a flag to show the maze after construction.')
  parser.add_argument('--test_runs', type=int, help='an integer for the number of iterations to run the time test against.')
  args = parser.parse_args()

  if args.test_runs:
    start_time = time.clock()
    for x in range(args.test_runs):
      Maze(width=args.width, height=args.height, show_steps=False, no_print=True)
    process_time = time.clock() - start_time
    print '\nIt took {}\'s to process {} mazes of that size. {}\'s per maze.'.format(process_time, args.test_runs, (process_time/args.test_runs))

  else:
    m = Maze(width=args.width, height=args.height, speed=args.speed, show_steps=args.show_steps,
         no_print=args.no_print, seed=args.seed)


if __name__ == '__main__':
  main()
