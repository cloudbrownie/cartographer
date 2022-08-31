# tile data format : [rel_x, rel_y, sheet_id, sheet_row, sheet_col]
from copy import deepcopy
from sys import getsizeof
from pickle import dumps

# returns if a value is in bounds
def is_inbounds(p : tuple, l : float, r : float, t : float, b : float) -> bool:
  return l <= p[0] <= r and t <= p[1] <= b

class Chunks:
  # init everything
  def __init__(self):
    self.chunks = {}

    self.sheet_refs = {}
    self.sheet_id = 0

    self.CHUNK_SIZE = 8
    self.TILE_SIZE = 16
    self.SURF_PADDING = 3
    self.CHUNK_PX = self.CHUNK_SIZE * self.TILE_SIZE + self.SURF_PADDING * 2

    self.render_cache = {}

    self.re_render = set()

  # adds a chunk to chunk dict
  def add_chunk(self, tag : str) -> None:
    self.chunks[tag] = {
      'tiles':{

      },
      'decor':{

      }
    }

  # copies the entire chunk system and returns as pickled obj (for mem space)
  def copy(self) -> dict:
    self.prune()

    chunks_copy = deepcopy(self.chunks)
    pickle = dumps(chunks_copy)

    return pickle

  # removes a chunk from chunk dict
  def remove_chunk(self, tag : str) -> None:
    del self.chunks[tag]

  # adds a tile layer to a chunk to a chunk
  def add_tile_layer(self, tag : str, layer : str) -> None:
    self.chunks[tag]['tiles'][layer] = []

    # sort layers
    layers = self.chunks[tag]['tiles']
    items = sorted(list(layers.keys()), key=lambda x : int(x))
    sorted_layers = {}
    for layer_key in items:
      sorted_layers[layer_key] = layers[layer_key]
    layers = sorted_layers

  # removes a tile layer from a chunk
  def remove_tile_layer(self, tag : str, layer : str) -> None:
    del self.chunks[tag]['tiles'][layer]

  # adds a decor layer to a chunk
  def add_decor_layer(self, tag : str, layer : str) -> None:
    self.chunks[tag]['decor'][layer] = []

    # sort layers
    layers = self.chunks[tag]['tiles']
    items = sorted(list(layers.keys()), key=lambda x : int(x))
    sorted_layers = {}
    for layer_key in items:
      sorted_layers[layer_key] = layers[layer_key]
    layers = sorted_layers

  # removes a decor layer from a chunk
  def remove_decor_layer(self, tag : str, layer : str) -> None:
    del self.chunks[tag]['decor'][layer]

  # adds a sheet refernece to ref dict
  def add_sheet_ref(self, sheet_name : str) -> None:
    self.sheet_id += 1
    self.sheet_refs[self.sheet_id] = sheet_name

  # grabs ref id for sheet from ref dict
  def get_sheet_id(self, sheet_name : str) -> int:
    for sheet_id in self.sheet_refs:
      if self.sheet_refs[sheet_id] == sheet_name:
        return sheet_id

    self.add_sheet_ref(sheet_name)
    return self.sheet_id

  # converts glob tile pos to chunk coord
  def chunk_pos(self, x : float, y : float) -> tuple[int, int]:
    return int(x // self.CHUNK_SIZE), int(y // self.CHUNK_SIZE)

  # converts glob exact pos to tile coord 
  def tile_pos(self, x : float, y : float) -> tuple[int, int]:
    return int(x // self.TILE_SIZE), int(y // self.TILE_SIZE)

  # converts the relative tile position to global
  def glob_tile_pos(self, x : float, y : float, tag : str) -> tuple[int, int]:
    chunk_x, chunk_y = self.deformat_chunk_tag(tag)
    tx = x + chunk_x * self.CHUNK_SIZE
    ty = y + chunk_y * self.CHUNK_SIZE
    return int(tx), int(ty)

  # converts tile coord to chunk rel tile coords
  def rel_tile_pos(self, x : float, y : float) -> tuple[int, int]:
    x %= self.CHUNK_SIZE
    y %= self.CHUNK_SIZE
    # adjust for negative relative values
    if x < 0:
      x = self.CHUNK_SIZE + x
    if y < 0:
      y = self.CHUNK_SIZE + y
    return int(x), int(y)

  # formats x and y coords into a chunk tag
  def get_chunk_tag(self, x : float, y : float) -> str:
    return f'{int(x)},{int(y)}'

  # returns x and y coords from formatted chunk tag
  def deformat_chunk_tag(self, tag : str) -> tuple[int, int]:
    x, y = tag.split(',')
    return int(x), int(y)

  # returns tile data from a layer
  def get_tile(self, x : float, y : float, layer : str) -> tuple:
    chunk_x, chunk_y = self.chunk_pos(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)
    if tag not in self.chunks or layer not in self.chunks[tag]['tiles']:
      return None

    rel_pos = list(self.rel_tile_pos(x, y))
    for tile in self.chunks[tag]['tiles'][layer]:
      if tile[0:2] == rel_pos:
        return tile

  # calculate the bitsum of a tile
  def calculate_bitsum(self, x : int, y : int, tile_data : list, \
      layer : str) -> int:
    # find bitsum using bitwise algorithm
    bitsum = 0
    neighbor_weight = 1
    for nx, ny in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
      curr_pos = x + nx, y + ny
      chunk_pos = self.chunk_pos(*curr_pos)
      tag = self.get_chunk_tag(*chunk_pos)
      if self.get_tile(*curr_pos, layer):
        bitsum += neighbor_weight
        self.re_render.add(tag)
      neighbor_weight *= 2
    tile_data[3] = bitsum
    return bitsum

  # calculate the bitsum for a certain tile and fixes the bitsum for neighbors
  def auto_tile(self, x : int, y : int, layer : str) -> int:
    # bitwise algorithm and store neighbors along the way
    bitsum = 0
    neighbor_weight = 1
    neighbors = []
    for nx, ny in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
      curr_pos = x + nx, y + ny
      chunk_pos = self.chunk_pos(*curr_pos)
      tag = self.get_chunk_tag(*chunk_pos)
      n_tile_data = self.get_tile(*curr_pos, layer)
      if n_tile_data:
        bitsum += neighbor_weight
        neighbors.append((*curr_pos, n_tile_data))
        self.re_render.add(tag)
      neighbor_weight *= 2

    # fix neighbors
    for nx, ny, neighbor in neighbors:
      self.calculate_bitsum(nx, ny, neighbor, layer)

    return bitsum

  # adds a tile to a layer in a chunk
  def add_tile(self, x : float, y : float, layer : str, 
    sheet_name : str, sheet_coords : tuple, auto_tile : bool = False) -> tuple:
    # grab tile coordinates and find the relative chunk pos
    rel_pos = self.rel_tile_pos(x, y)

    # find chunk and pack tile data
    chunk_x, chunk_y = self.chunk_pos(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)
    sheet_id = self.get_sheet_id(sheet_name)
    tile_data = [*rel_pos, sheet_id, *sheet_coords]

    # case: chunk doesn't already exist
    if tag not in self.chunks:
      self.add_chunk(tag)
      self.add_tile_layer(tag, layer)
      self.chunks[tag]['tiles'][layer] = [tile_data]
      if auto_tile:
        tile_data[3] = self.auto_tile(x, y, layer)
      return x, y

    # case: chunk exists but layer does not
    if layer not in self.chunks[tag]['tiles']:
      self.add_tile_layer(tag, layer)
      self.chunks[tag]['tiles'][layer] = [tile_data]
      if auto_tile:
        tile_data[3] = self.auto_tile(x, y, layer)
        self.re_render.add(tag)
      return x, y

    # case: chunk and layer exist
    insert_idx = 0
    tile_layer = self.chunks[tag]['tiles'][layer]
    for i, o_tile_data in enumerate(tile_layer):
      if tile_data[1] < o_tile_data[1]:
        break

      # this case actually replaces the current tile and break from the loop
      elif tile_data[0:2] == o_tile_data[0:2]:
        if tile_data == o_tile_data:
          return x, y

        tile_layer[i] = tile_data
        if auto_tile:
          tile_data[3] = self.auto_tile(x, y, layer)
        return x, y

      insert_idx += 1

    # normal case
    tile_layer.insert(insert_idx, tile_data)
    if auto_tile:
      tile_data[3] = self.auto_tile(x, y, layer)
    self.re_render.add(tag)

    return x, y

  # removes a tile from a layer in a chunk
  def remove_tile(self, x : float, y : float, layer : str, \
      auto_tile : bool = False) -> None:
    chunk_x, chunk_y = self.chunk_pos(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)

    if tag not in self.chunks or layer not in self.chunks[tag]['tiles']:
      return

    rel_pos = list(self.rel_tile_pos(x, y))
    for i, tile_data in enumerate(self.chunks[tag]['tiles'][layer]):
      if tile_data[0:2] == rel_pos:
        self.chunks[tag]['tiles'][layer].pop(i)
        self.re_render.add(tag)
        if auto_tile:
          self.auto_tile(x, y, layer)
        return rel_pos

  def add_decor(self):
    return


  def remove_decor(self):
    return

  # return a list of chunks from chunk list that are within a specified rect
  def get_chunks(self, rect : tuple, skip_empty : bool = True) -> list[str]:
    chunks = []

    left, right, top, bot = self.get_bounds(rect)
    left, top = self.chunk_pos(left, top)
    right, bot = self.chunk_pos(right, bot)
    for i in range(left - 1, right + 1):
      for j in range(top - 1, bot + 1):

        tag = self.get_chunk_tag(i, j)

        if tag not in self.chunks and skip_empty:
          continue

        chunks.append(tag)

    return chunks

  # return a bounding rect list
  def get_bounds(self, rect : list) -> list:
    left, top = self.tile_pos(rect[0], rect[1])
    right, bot = self.tile_pos(rect[0] + rect[2], rect[1] + rect[3])
    return int(left), int(right), int(top), int(bot)

  # prunes the current chunks, removes all empty layers and empty chunks
  def prune(self) -> None:

    for chunk_tag in list(self.chunks.keys()):

      chunk = self.chunks[chunk_tag]

      # pre check if chunk is empty
      if not chunk['tiles'] and not chunk['decor']:
        del self.chunks[chunk_tag]
        continue

      # can't delete during iteration

      # delete empty tile layers
      for tile_layer in list(chunk['tiles'].keys()):
        if not chunk['tiles'][tile_layer]:
          del chunk['tiles'][tile_layer]

      # delete empty decor layers
      for decor_layer in list(chunk['decor'].keys()):
        if not chunk['decor'][decor_layer]:
          del chunk['decor'][decor_layer]

      # post check if chunk is empty
      if not chunk['tiles'] and not chunk['decor']:
        del self.chunks[chunk_tag]

  # TODO: make this a process function (too slow for large sections)
  # returns a list of connected tiles on point (glob pos)
  def mask_select(self, x : float, y : float, layer : str, rect : list) -> list:
    open_l = [(int(x), int(y))]
    closed_l = []

    if not rect:
      left = bot = float('-inf')
      right = top = float('inf')
    else:
      left, right, top, bot = self.get_bounds(rect)

    chunks = self.get_chunks(rect, skip_empty=True)
    tiles = []
    for chunk_tag in chunks:
      if layer not in self.chunks[chunk_tag]['tiles']:
        continue

      chunk_x, chunk_y = self.deformat_chunk_tag(chunk_tag)

      layer_tiles = self.chunks[chunk_tag]['tiles'][layer]
      for tile_data in layer_tiles:
        rel_x, rel_y = tile_data[0:2]
        
        unrel_x = chunk_x * self.CHUNK_SIZE + rel_x
        unrel_y = chunk_y * self.CHUNK_SIZE + rel_y

        tiles.append((unrel_x, unrel_y))

    while len(open_l) > 0:
      curr_x, curr_y = open_l.pop(0)

      for nx, ny in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        n_pos = curr_x + nx, curr_y + ny

        if n_pos in closed_l or not is_inbounds(n_pos, left, right, top, bot):
          continue

        if n_pos not in open_l and n_pos in tiles:
          open_l.append(n_pos)

      if (curr_x, curr_y) in tiles:
        closed_l.append((curr_x, curr_y))

    return closed_l
