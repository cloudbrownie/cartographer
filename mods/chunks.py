# tile data format : rel_x, rel_y, sheet_id, sheet_coords
from pygame import Surface
from time import time

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

    self.re_render = []

  # adds a chunk to chunk dict
  def add_chunk(self, tag : str) -> None:
    self.chunks[tag] = {
      'tiles':{

      },
      'decor':{

      }
    }

  # removes a chunk from chunk dict
  def remove_chunk(self, tag : str) -> None:
    del self.chunks[tag]

  # adds a tile layer to a chunk to a chunk
  def add_tile_layer(self, tag : str, layer : str) -> None:
    self.chunks[tag]['tiles'][layer] = []

    # sort layers
    layer = self.chunks[tag]['tiles']
    items = sorted(layer.items(), key=lambda x : x[0])
    layer = dict(items)

  # removes a tile layer from a chunk
  def remove_tile_layer(self, tag : str, layer : str) -> None:
    del self.chunks[tag]['tiles'][layer]

  # adds a decor layer to a chunk
  def add_decor_layer(self, tag : str, layer : str) -> None:
    self.chunks[tag]['decor'][layer] = []

    # sort layers
    layer = self.chunks[tag]['tiles']
    items = sorted(layer.items(), key=lambda x : x[0])
    layer = dict(items)

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

  # cache the chunk surfs
  def cache_chunk_surfs(self, tag : str, sheets : dict) -> None:
    
    for tile_layer in self.chunks[tag]['tiles']:
      tiles = self.chunks[tag]['tiles'][tile_layer]
      for tile_data in tiles:

        x, y, sheet_id, sheet_coords = tile_data
        sheet_name = self.sheet_refs[sheet_id]

        surf = sheets.get_surf(sheet_name, sheet_coords)

        x *= self.TILE_SIZE
        y *= self.TILE_SIZE

        offsetx, offsety = 0, 0

  # converts glob pos to chunk coord
  def get_chunk_coords(self, x : float, y : float) -> tuple[float, float]:
    return x // self.CHUNK_SIZE, y // self.CHUNK_SIZE

  # converts glob pos to tile coord 
  def get_tile_coords(self, x : float, y : float) -> tuple[float, float]:
    return x // self.TILE_SIZE, y // self.TILE_SIZE

  # converts tile coord to chunk rel tile coords
  def get_rel_tile_coords(self, x : float, y : float) -> tuple[float, float]:
    x %= self.CHUNK_SIZE
    y %= self.CHUNK_SIZE
    if x < 0:
      x = self.CHUNK_SIZE + x
    if y < 0:
      y = self.CHUNK_SIZE + y
    return x, y

  # formats x and y coords into a chunk tag
  def get_chunk_tag(self, x : float, y : float) -> str:
    return f'{int(x)},{int(y)}'

  # returns x and y coords from formatted chunk tag
  def deformat_chunk_tag(self, tag : str) -> tuple[int, int]:
    x, y = tag.split(',')
    return int(x), int(y)

  # get a tile in a layer in a chunk using rel tile coords
  def get_tile_in_chunk(self, x : float, y : float, layer : str,
                                                      tag : str) -> tuple:
    for tile in self.chunks[tag]['tiles'][layer]:
      if tile[0:2] == [x, y]:
        return tile

  # check if current tile data exists already
  def check_duplicate_tile(self, tag : str, layer : str, 
                                        tile_data : tuple) -> bool:
    return tile_data in self.chunks[tag]['tiles'][layer]

  # adds a tile to a layer in a chunk
  def add_tile(self, x : float, y : float, layer : str, 
                        sheet_name : str, sheet_coords : tuple) -> tuple:
    # grab tile coordinates and find the relative chunk pos
    tile_coords = x, y
    rel_coords = self.get_rel_tile_coords(*tile_coords)

    # find chunk and pack tile data
    chunk_x, chunk_y = self.get_chunk_coords(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)
    sheet_id = self.get_sheet_id(sheet_name)
    tile_data = *rel_coords, sheet_id, sheet_coords

    # case: chunk doesn't already exist
    if tag not in self.chunks:
      self.add_chunk(tag)
      self.add_tile_layer(tag, layer)

      self.chunks[tag]['tiles'][layer] = [tile_data]

      return tile_coords

    # case: chunk exists but layer does not
    if layer not in self.chunks[tag]['tiles']:
      self.add_tile_layer(tag, layer)
      self.chunks[tag]['tiles'][layer] = [tile_data]
      if tag not in self.re_render:
        self.re_render.append(tag)
      return tile_coords

    # case: chunk and layer exist
    insert_idx = 0
    tile_layer = self.chunks[tag]['tiles'][layer]
    for i, o_tile_data in enumerate(tile_layer):
      if tile_data[1] < o_tile_data[1]:
        break

      # this case actually replaces the current tile and break from the loop
      elif tile_data[0:2] == o_tile_data[0:2]:
        if tile_data == o_tile_data:
          return tile_coords

        tile_layer[i] = tile_data
        return tile_coords

      insert_idx += 1

    tile_layer.insert(insert_idx, tile_data)
    if tag not in self.re_render:
      self.re_render.append(tag)

    return tile_coords

  # removes a tile from a layer in a chunk
  def remove_tile(self, x : float, y : float, layer : str) -> None:
    chunk_x, chunk_y = self.get_chunk_coords(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)

    if tag not in self.chunks or layer not in self.chunks[tag]['tiles']:
      return

    rel_coords = self.get_rel_tile_coords(x, y)
    r_tile_coords = None
    for i, tile_data in enumerate(self.chunks[tag]['tiles'][layer]):
      if tile_data[0:2] == rel_coords:
        r_tile_coords = rel_coords
        self.chunks[tag]['tiles'][layer].pop(i)
        if tag not in self.re_render:
          self.re_render.append(tag)
        break

    return r_tile_coords

  def add_decor(self):
    return


  def remove_decor(self):
    return

  # return a list of chunks from chunk list that are within a specified rect
  def get_chunks(self, rect : tuple, skip_empty : bool = True) -> list[str]:
    chunks = []

    left, right, top, bot = self.get_bounds(rect)
    left, top = self.get_chunk_coords(left, top)
    right, bot = self.get_chunk_coords(right, bot)
    for i in range(left - 1, right + 1):
      for j in range(top - 1, bot + 1):

        tag = self.get_chunk_tag(i, j)

        if tag not in self.chunks and skip_empty:
          continue

        chunks.append(tag)

    return chunks

  # return a bounding rect list
  def get_bounds(self, rect : list) -> list:
    left, top = self.get_tile_coords(rect[0], rect[1])
    right, bot = self.get_tile_coords(rect[0] + rect[2], rect[1] + rect[3])
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

  # returns a list of connected tiles on point
  def mask_select(self, x : float, y : float, layer : str, rect : list) -> list:
    tile_x, tile_y = self.get_tile_coords(x, y)
    
    open_l = [(tile_x, tile_y)]
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

      closed_l.append((curr_x, curr_y))

    return closed_l

  def auto_tile(self, tiles : list, sheet_config : dict) -> None:
    return
