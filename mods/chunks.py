
class Chunks:
  # init everything
  def __init__(self):
    self.chunks = {}

    self.sheet_refs = {}
    self.sheet_id = 0

    self.chunk_size = 8
    self.tile_size = 16
    self.chunk_px = self.chunk_size * self.tile_size

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

  # adds a decor layer to a chunk
  def add_decor_layer(self, tag : str, layer : str) -> None:
    self.chunks[tag]['decor'][layer] = []

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

  # converts glob pos to chunk coord
  def get_chunk_coords(self, x : float, y : float) -> tuple:
    return x // self.chunk_px, y // self.chunk_px

  # converts glob pos to tile coord 
  def get_tile_coords(self, x : float, y : float) -> tuple:
    return x // self.tile_size, y // self.tile_size

  # converts tile coord to chunk rel tile coords
  def get_rel_tile_coords(self, x : float, y : float) -> tuple:
    x %= self.chunk_size
    y %= self.chunk_size

    return max(x, self.chunk_size + x), max(y, self.chunk_size + y)

  # formats x and y coords into a chunk tag
  def get_chunk_tag(self, x : float, y : float) -> str:
    return f'{int(x)},{int(y)}'

  # returns x and y coords from formatted chunk tag
  def deformat_chunk_tag(self, tag : str) -> tuple:
    x, y = tag.split(',')
    return int(x), int(y)

  # get a tile in a layer in a chunk using rel tile coords
  def get_tile_in_chunk(self, x : float, y : float, layer : str, tag : str) -> tuple:
    for tile in self.chunks[tag]['tiles'][layer]:
      if tile[0:2] == [x, y]:
        return tile

  # check if current tile data exists already
  def check_duplicate_tile(self, tag : str, layer : str, tile_data : tuple) -> bool:
    return tile_data in self.chunks[tag]['tiles'][layer]

  # adds a tile to a layer in a chunk
  def add_tile(self, x : float, y : float, layer : str, sheetname : str, sheet_coords : tuple) -> tuple:
    tile_coords = self.get_tile_coords(x, y)

    rel_coords = self.get_rel_tile_coords(*tile_coords)
    tag = self.get_chunk_tag(x, y)
    sheet_id = self.get_sheet_id(sheetname)
    tile_data = *rel_coords, sheet_id, sheet_coords

    if tag not in self.chunks:
      self.add_chunk(tag)
      self.add_tile_layer(tag, layer)

      self.chunks[tag]['tiles'][layer] = [tile_data]

      return tile_coords

    if layer not in self.chunks[tag]['tiles']:
      self.add_tile_layer(tag, layer)
      self.chunks[tag]['tiles'][layer] = [tile_data]

    elif not self.check_duplicate_tile(tag, layer, tile_data):
      self.chunks[tag]['tiles'][layer].append(tile_data)

    return tile_coords

  # removes a tile from a layer in a chunk
  def remove_tile(self, x : float, y : float, layer : str) -> None:
    tag = self.get_chunk_tag(x, y)

    if tag not in self.chunks or layer not in self.chunks[tag]['tiles']:
      return

    tile_coords = self.get_tile_coords(x, y)
    rel_coords = list(self.get_rel_tile_coords(*tile_coords))
    r_tile_coords = None
    for tile_data, i in enumerate(self.chunks[tag]['tiles'][layer]):
      if tile_data[0:2] == rel_coords:
        r_tile_coords = rel_coords
        self.chunks[tag]['tiles'][layer].pop(i)
        break

    return r_tile_coords


  def add_decor(self):
    return


  def remove_decor(self):
    return

  # return a list of chunks from chunk list that are within a specified rect
  def get_chunks(self, rect : tuple, skip_empty : bool = True) -> list:
    chunks = []

    left, right, top, bottom = self.get_bounds(rect)
    
    for i in range(left, right):
      for j in range(top, bottom):

        tag = self.get_chunk_tag(i, j)

        if tag not in self.chunks and skip_empty:
          continue

        chunks.append(tag)

    return chunks

  # return a bounding rect list
  def get_bounds(self, rect : list) -> list:
    left, top = self.get_tile_coords(rect[0], rect[1])
    right, bottom = self.get_tile_coords(rect[0] + rect[2], rect[1] + rect[3])
    return left, right, top, bottom

  # flood files an area with tiles
  def flood(self, pos : tuple, layer : str, sheet_data : tuple, rect : list) -> list:
    tile_x, tile_y = self.get_tile_coords(*pos)
    chunk_x, chunk_y = self.get_chunk_coords(tile_x, tile_y)
    tag = self.get_chunk_tag(chunk_x, chunk_y)

    rel_coords = self.get_rel_tile_coords

    if tag in self.chunks and layer in self.chunks[tag]['tiles']:
      for tile_data in self.chunks[tag]['tiles'][layer]:
        if tile_data[0:2] == list(rel_coords):
          return [], []

    left, right, top, bottom = self.get_bounds(rect)

    if not (left <= tile_x <= right) or not (top <= tile_y <= bottom):
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

        closed_l.append((rel_tile_x + chunk_x * self.chunk_size, rel_tile_y + chunk_y * self.chunk_size))


    if (tile_x, tile_y) not in closed_l:
      new_tiles.append((tile_x, tile_y))

    while len(open_l) > 0:
      curr_x, curr_y = open_l.pop(0)

      for nx, ny in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        n_pos = curr_x + nx, curr_y + ny
        
        if n_pos in closed_l or not (left <= n_pos[0] <= right) or not (top <= n_pos[1] <= bottom):
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
      
      left, right, top, bottom = self.get_bounds(rect)
      for tag in bound_chunks:
        if layer not in self.chunks[tag]['tiles']:
          continue

        cx, cy = self.deformat_chunk_tag(tag)
        for tile_data in self.chunks[tag]['tiles'][layer]:
          rel_x, rel_y = tile_data[0:2]

          glob_x = rel_x + cx * self.chunk_size
          glob_y = rel_y + cy * self.chunk_size

          if left <= glob_x <= right and top <= glob_y <= bottom:
            cull_tiles.append((glob_x, glob_y))

  # returns a list of connected tiles on point
  def mask_select(self, x : float, y : float, layer : str, rect : list) -> list:
    tile_x, tile_y = self.get_tile_coords(x, y)

    open_l = [(tile_x, tile_y)]
    closed_l = []

    if not rect:
      left = bottom = float('-inf')
      right = top = float('inf')
    else:
      left, right, top, bottom = self.get_bounds(rect)

    while len(open_l) > 0:
      curr_x, curr_y = open_l.pop(0)

      for nx, ny in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        n_pos = curr_x + nx, curr_y + ny

        if n_pos in closed_l or not (left <= n_pos[0] <= right) or not (top <= n_pos[1] <= bottom):
          continue

        if n_pos not in open_l:
          open_l.append(n_pos)

      closed_l.append((curr_x, curr_y))

    return closed_l

  def auto_tile(self, tiles : list, sheet_config : dict) -> None:
    return

if __name__ == '__main__':
  a = [1, 2, 3, 4, 5]
  b = [1, 2]

  print(a[0:2] == b)

  t = Chunks()

  print(t.chunk_px)
  vis_chunks = t.get_chunks((0, 0, 256, 256))

  for cx, cy in vis_chunks:
    print(cx * t.chunk_px, cy * t.chunk_px)

  print(t.get_tile_coords(256, 256))

  x = y = float('inf')
  print(x == y, x is y)