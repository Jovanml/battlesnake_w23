# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com
import copy
import typing


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
  print("INFO")

  return {
    "apiversion": "1",
    "author": "",  # TODO: Your Battlesnake Username
    "color": "#93E9BE",  # TODO: Choose color
    "head": "nr-rocket",  # TODO: Choose head
    "tail": "coffee",  # TODO: Choose tail
  }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
  print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
  print("GAME OVER\n")


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

  is_move_safe = {"up": True, "down": True, "left": True, "right": True}

  my_head = game_state["you"]["body"][0]  # Coordinates of your head
  my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"
  my_health = game_state["you"]["health"]
  my_length = game_state["you"]["length"]
  my_id = game_state["you"]["id"]

  # Step 1 - Prevent your Battlesnake from colliding with the wall
  check_wall(my_head, game_state, is_move_safe)
  print(f"step 1 {is_move_safe}")

  # Step 2 - Prevent your Battlesnake from colliding with itself
  my_body = game_state['you']['body']
  check_self(my_neck, my_body, my_head, is_move_safe)
  print(f"step 2 {is_move_safe}")

  # Step 3 - Prevent your Battlesnake from colliding with other Battlesnakes
  snakes = game_state['board']['snakes']
  opponent_heads_and_length = []
  opponent_bodies = []

  for snake in snakes:
    id = snake["id"]
    if id != my_id:
      body = snake["body"]
      opponent_heads_and_length.append([snake["head"], snake["length"]])
      for cell in body[1:]:
        opponent_bodies.append(cell)

  check_others(my_head, my_length, opponent_heads_and_length, opponent_bodies,
               is_move_safe)
  print(f"step 3 {is_move_safe}")

  # Are there any safe moves left?
  safe_moves = []
  for move, isSafe in is_move_safe.items():
    if isSafe:
      safe_moves.append(move)

  if len(safe_moves) == 0:
    print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
    return {"move": "down"}

  # Secondary check to prioritize the most safe moves
  dict1 = prioritize_moves(safe_moves, my_head, my_neck, my_body, my_length,
                           game_state, opponent_bodies,
                           opponent_heads_and_length)

  priority_moves = sorted(dict1, key=dict1.get, reverse=True)
  print(f"priority: {dict1}")
  next_move = priority_moves[0]

  # Step 4 - Move towards food to regain health and survive longer
  food = game_state['board']['food']
  if len(food) > 0:
    food_dict = {}
    for i in range(0, len(food)):
      f = food[i]
      f_dis = abs(f["x"] - my_head["x"]) + abs(f["y"] - my_head["y"])
      food_dict[i] = f_dis

    food_dict = sorted(food_dict, key=food_dict.get)
    target_food_index = food_dict[0]
    target_food = food[target_food_index]

    BUFFER = 35
    if my_health <= (food_dict[target_food_index] + BUFFER) or my_health < 40:
      food_move = move_towards_food(target_food, my_head, is_move_safe, dict1)
      if food_move is not None:
        next_move = food_move
      elif len(food_dict) > 1:
        snd_food_index = food_dict[1]
        if my_health <= food_dict[snd_food_index]:
          snd_food = food[snd_food_index]
          food_move = move_towards_food(snd_food, my_head, is_move_safe, dict1)
          if food_move is not None:
            target_food = snd_food
            next_move = food_move
      print(f"food:{target_food}, move:{food_move}")

  print(f"health:{my_health}")
  print(f"MOVE {game_state['turn']}: {next_move}")
  print('---------------------------------------')
  return {"move": next_move}


# Helper function that prevents snake from colliding with wall
def check_wall(my_head, game_state, is_move_safe):
  if my_head["x"] == 0:
    is_move_safe["left"] = False
  if my_head["x"] == game_state['board']['width'] - 1:
    is_move_safe["right"] = False
  if my_head["y"] == 0:
    is_move_safe["down"] = False
  if my_head["y"] == game_state['board']['height'] - 1:
    is_move_safe["up"] = False
  # print(f"step 1 {is_move_safe}")


# Helper function that prevents snake from colliding with itself
def check_self(my_neck, my_body, my_head, is_move_safe):
  for cell in my_body[:-1]:  # skip tail
    if cell["x"] == my_head["x"] - 1 and cell["y"] == my_head[
        "y"]:  # Body cell is left of head, don't move left
      is_move_safe["left"] = False

    if cell["x"] == my_head["x"] + 1 and cell["y"] == my_head[
        "y"]:  # Body cell is right of head, don't move right
      is_move_safe["right"] = False

    if cell["x"] == my_head["x"] and cell[
        "y"] == my_head["y"] - 1:  # Body cell is below head, don't move down
      is_move_safe["down"] = False

    if cell["x"] == my_head["x"] and cell[
        "y"] == my_head["y"] + 1:  # Body cell is above head, don't move up
      is_move_safe["up"] = False


# Helper function that prevents snake from colliding with other Battlesnakes
def check_others(my_head, my_length, opponent_heads_and_length,
                 opponent_bodies, is_move_safe):
  dirMap = {(1, 0): "right", (-1, 0): "left", (0, 1): "up", (0, -1): "down"}

  for x, y in dirMap.keys():
    potential_move = {"x": my_head["x"] + x, "y": my_head["y"] + y}
    dir = dirMap[(x, y)]
    if potential_move in opponent_bodies:
      is_move_safe[dir] = False

    # checks if potential move collides with the head of a longer opponent
    for head, length in opponent_heads_and_length:
      if potential_move == head and length >= my_length:
        is_move_safe[dir] = False


# Helper function that scores the safety of each potential move
def prioritize_moves(moves, my_head, my_neck, my_body, my_length, game_state,
                     opponent_bodies, opponent_heads_and_length):
  dict = {}
  for move in moves:
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}
    new_head = move_position(move, my_head)
    new_body = copy.deepcopy(my_body)
    new_body.pop()
    new_body.insert(0, new_head)
    check_wall(new_head, game_state, is_move_safe)
    check_self(new_body[1], new_body, new_head, is_move_safe)
    check_others(new_head, my_length, opponent_heads_and_length,
                 opponent_bodies, is_move_safe)

    safe_moves = []
    for nextMove, isSafe in is_move_safe.items():
      if isSafe:
        safe_moves.append(nextMove)

    addedPoints = 0
    for dir in is_move_safe.keys():
      addedPoints += tertiary_check(dir, my_head, my_body, game_state,
                                    my_length, opponent_heads_and_length,
                                    opponent_bodies)

    dict[move] = len(safe_moves) + addedPoints

  return dict


# Tertiary check to do a shallow look at two moves ahead
def tertiary_check(move, my_head, my_body, game_state, my_length,
                   opponent_heads_and_length, opponent_bodies):
  is_move_safe = {"up": True, "down": True, "left": True, "right": True}
  new_head = move_position(move, my_head)
  new_body = copy.deepcopy(my_body)
  new_body.pop()
  new_body.insert(0, new_head)
  check_wall(new_head, game_state, is_move_safe)
  check_self(new_body[1], new_body, new_head, is_move_safe)

  check_others(new_head, my_length, opponent_heads_and_length, opponent_bodies,
               is_move_safe)

  safe_moves = []
  for nextMove, isSafe in is_move_safe.items():
    if isSafe:
      safe_moves.append(nextMove)

  return len(safe_moves)


# Helper function that moves snake towards food target
def move_towards_food(target_food, my_head, is_move_safe, dict1):
  next_move = None
  if target_food["x"] > my_head["x"] and is_move_safe[
      "right"] and "right" in dict1.keys() and dict1["right"] > 1:
    next_move = "right"
  elif target_food["x"] < my_head["x"] and is_move_safe[
      "left"] and "left" in dict1.keys() and dict1["left"] > 1:
    next_move = "left"
  elif target_food["y"] > my_head["y"] and is_move_safe[
      "up"] and "up" in dict1.keys() and dict1["up"] > 1:
    next_move = "up"
  elif target_food["y"] < my_head["y"] and is_move_safe[
      "down"] and "down" in dict1.keys() and dict1["down"] > 1:
    next_move = "down"

  return next_move


# Helper function that determines new head position after a move
def move_position(move_str, my_head):
  if move_str == "up":
    new_head = {"x": my_head["x"], "y": my_head["y"] + 1}
  if move_str == "down":
    new_head = {"x": my_head["x"], "y": my_head["y"] - 1}
  if move_str == "left":
    new_head = {"x": my_head["x"] - 1, "y": my_head["y"]}
  if move_str == "right":
    new_head = {"x": my_head["x"] + 1, "y": my_head["y"]}

  return new_head


# Start server when `python main.py` is run
if __name__ == "__main__":
  from server import run_server

  run_server({"info": info, "start": start, "move": move, "end": end})
