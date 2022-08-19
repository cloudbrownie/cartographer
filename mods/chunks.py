# tile data format : rel_x, rel_y, sheet_id, sheet_coords
from pygame import Surface

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
  def add_sheet_ref(self, sheetname : str) -> None:
    self.sheet_id += 1
    self.sheet_refs[self.sheet_id] = sheetname

  # grabs ref id for sheet from ref dict
  def get_sheet_id(self, sheetname : str) -> int:
    for sheet_id in self.sheet_refs:
      if self.sheet_refs[sheet_id] == sheetname:
        return sheet_id

    self.add_sheet_ref(sheetname)
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
    chunk_size = self.CHUNK_SIZE * self.TILE_SIZE
    return x // chunk_size, y // chunk_size

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
                        sheetname : str, sheet_coords : tuple) -> tuple:
    # grab tile coordinates and find the relative chunk pos
    tile_coords = self.get_tile_coords(x, y)
    rel_coords = self.get_rel_tile_coords(*tile_coords)

    # find chunk and pack tile data
    chunk_x, chunk_y = self.get_chunk_coords(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)
    sheet_id = self.get_sheet_id(sheetname)
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

    # case: chunk and layer exist
    elif not self.check_duplicate_tile(tag, layer, tile_data):
      insert_idx = 0
      tile_layer = self.chunks[tag]['tiles'][layer]
      for i, o_tile_data in enumerate(tile_layer):
        if tile_data[1] < o_tile_data[1]:
          break

        # this case actually replaces the current tile and break from the loop
        elif tile_data[0:2] == o_tile_data[0:2]:
          tile_layer[i] = tile_data
          return tile_coords

        insert_idx += 1

      tile_layer.insert(insert_idx, tile_data)

    return tile_coords

  # removes a tile from a layer in a chunk
  def remove_tile(self, x : float, y : float, layer : str) -> None:
    chunk_x, chunk_y = self.get_chunk_coords(x, y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)

    if tag not in self.chunks or layer not in self.chunks[tag]['tiles']:
      return

    tile_coords = self.get_tile_coords(x, y)
    rel_coords = self.get_rel_tile_coords(*tile_coords)
    r_tile_coords = None
    for i, tile_data in enumerate(self.chunks[tag]['tiles'][layer]):
      if tile_data[0:2] == rel_coords:
        r_tile_coords = rel_coords
        self.chunks[tag]['tiles'][layer].pop(i)
        break

    return r_tile_coords

  def add_decor(self):
    return


  def remove_decor(self):
    return

  # returns a dict fill of rendered surfaces of each chunk
  def render_chunks(self, chunks : list, sheets : dict) -> dict:
    
    render_dict = {

    }

    for chunk_tag in chunks:
      
      layers = {

      }

      for layer in self.chunks[chunk_tag]['tiles']:

        layer_surf = Surface((self.CHUNK_PX, self.CHUNK_PX))
        layer_surf.set_colorkey((0, 0, 0))

        for tile_data in self.chunks[chunk_tag]['tiles'][layer]:

          x, y, sheet_id, sheet_coords = tile_data
          x = x * self.TILE_SIZE + self.SURF_PADDING
          y = y * self.TILE_SIZE + self.SURF_PADDING
          sheet_name = self.sheet_refs[sheet_id]
          tile_surf = sheets[sheet_name][sheet_coords[0]][sheet_coords[1]]

          layer_surf.blit(tile_surf, (x, y))
        
        layers[layer] = layer_surf

      render_dict[chunk_tag] = layers

    return render_dict

  # return a list of chunks from chunk list that are within a specified rect
  def get_chunks(self, rect : tuple, skip_empty : bool = True) -> list[str]:
    chunks = []

    left, right, top, bot = self.get_bounds(rect)
    
    for i in range(left, right):
      for j in range(top, bot):

        tag = self.get_chunk_tag(i, j)

        if tag not in self.chunks and skip_empty:
          continue

        chunks.append(tag)

    return chunks

  # return a bounding rect list
  def get_bounds(self, rect : list) -> list:
    left, top = self.get_tile_coords(rect[0], rect[1])
    right, bot = self.get_tile_coords(rect[0] + rect[2], rect[1] + rect[3])
    left -= self.CHUNK_SIZE
    top -= self.CHUNK_SIZE
    right += 1
    bot += 1
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

  # flood files an area with tiles
  def flood(self, pos : tuple, layer : str, sheet_data : tuple, 
                                                  rect : list) -> list:
    tile_x, tile_y = self.get_tile_coords(*pos)
    chunk_x, chunk_y = self.get_chunk_coords(tile_x, tile_y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)

    rel_coords = self.get_rel_tile_coords

    if tag in self.chunks and layer in self.chunks[tag]['tiles']:
      for tile_data in self.chunks[tag]['tiles'][layer]:
        if tile_data[0:2] == list(rel_coords):
          return [], []

    left, right, top, bot = self.get_bounds(rect)

    if not (left <= tile_x <= right) or not (top <= tile_y <= bot):
      return

    open_l = [(tile_x, tile_y)]
    closed_l = []
    new_tiles = []
    
    for tile_data in self.chunks[tag]['tiles'][layer]:
      closed_l.append(tile_data[0:2])

    for tag in self.get_chunks(rect):
      if layer not in self.chunks[tag]:
        continue

      for rel_tile_data in self.chunks[tag]['tiles'][layer]:
        chunk_x, chunk_y = self.deformat_chunk_tag(tag)
        rel_tile_x, rel_tile_y = rel_tile_data[0:2]

        closed_l.append((rel_tile_x + chunk_x * self.CHUNK_SIZE, 
                          rel_tile_y + chunk_y * self.CHUNK_SIZE))


    if (tile_x, tile_y) not in closed_l:
      new_tiles.append((tile_x, tile_y))

    while len(open_l) > 0:
      curr_x, curr_y = open_l.pop(0)

      for nx, ny in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        n_pos = curr_x + nx, curr_y + ny
        
        if n_pos in closed_l or not is_inbounds(n_pos, left, right, top, bot):
          continue

        if n_pos not in open_l:
          open_l.append(n_pos)

        if n_pos not in new_tiles:
          new_tiles.append(n_pos)

      closed_l.append((curr_x, curr_y))

    for new_x, new_y in new_tiles:
      self.add_tile(new_x, new_y, layer, *sheet_data)

  # remove stuff within a specified rect
  def cull(self, e_type : str, layer : str, rect : list) -> list:
    bound_chunks = self.get_chunks(rect, skip_empty=True)

    if e_type == 'tiles':

      cull_tiles = []
      
      left, right, top, bot = self.get_bounds(rect)
      for tag in bound_chunks:
        if layer not in self.chunks[tag]['tiles']:
          continue

        cx, cy = self.deformat_chunk_tag(tag)
        for tile_data in self.chunks[tag]['tiles'][layer]:
          rel_x, rel_y = tile_data[0:2]

          glob_x = rel_x + cx * self.CHUNK_SIZE
          glob_y = rel_y + cy * self.CHUNK_SIZE

          if left <= glob_x <= right and top <= glob_y <= bot:
            cull_tiles.append((glob_x, glob_y))

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
      if layer not in self.chunks[chunk_tag]:
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
