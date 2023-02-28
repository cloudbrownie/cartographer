import math

neighbors = ((0, -1), (1, 0), (0, 1), (-1, 0))

class TileMap:
  def __init__(self, tile_size: int):
    self.tile_size = tile_size
    self.tiles = {}
    self.off_grid = {}
    self.layers = []

  # adds a tile to the tile map system
  def add_tile(self, pos: tuple, type: str, asset: tuple, layer: str) -> None:
    pos = tuple(pos)
    raw = pos[0] * self.tile_size, pos[1] * self.tile_size

    tile_info = {'pos':pos,
                'type':type,
                'asset':asset,
                'raw':[raw, asset]}

    if pos not in self.tiles:
      self.tiles[pos] = {layer:tile_info}
    else:
      self.tiles[pos][layer] = tile_info

    if layer not in self.layers:
      self.layers.append(layer)
      self.layers.sort()

  # removes a tile from the tile map system
  def remove_tile(self, pos: tuple, layer: str=None) -> dict:
    pos = tuple(pos)
    if pos not in self.tiles:
      return

    if layer and layer in self.tiles[pos]:
      data = self.tiles[pos][layer]
      del self.tiles[pos][layer]
      return data

  # returns all tiles visible within the given rect
  def get_visible(self, pos: tuple, size: int) -> list:
    layer_data = {l : [] for l in self.layers}

    pos = (int(round(pos[0] / self.tile_size - 0.5, 0)),
          int(round(pos[1] / self.tile_size - 0.5, 0)))
    for x in range(math.ceil(size[0] / self.tile_size) + 1):
      for y in range(math.ceil(size[1] / self.tile_size) + 1):
        tile_pos = x + pos[0], y + pos[1]
        if tile_pos in self.tiles:
          for tile in self.tiles[tile_pos]:
            layer_data[tile].append(self.tiles[tile_pos][tile]['raw'])

    return [layer_data[l] for l in self.layers]

  # returns all neighboring tiles to a specific spot
  def get_neighbors(self, pos: tuple, layer: str=None) -> list:

    if pos not in self.tiles or layer not in self.tiles[layer]:
      return []

    map_neighbors = []
    for x, y in neighbors:
      new_pos = pos[0] + x, pos[1] + y
      if self.tiles[new_pos] and layer in self.tiles[new_pos]:
        map_neighbors.append(self.tiles[new_pos][layer]['raw'])

    return map_neighbors

  # returns a tile's surrounding bitsum
  def calculate_bitsum(self, pos: tuple, layer: str, sset: bool=False) -> int:
    bitsum = 0
    neighbor_weight = 1
    for x, y in neighbors:
      new_pos = pos[0] + x, pos[1] + y
      if self.get_tile(new_pos, layer):
        bitsum += neighbor_weight
      neighbor_weight *= 2

    if sset:
      asset_data = self.tiles[pos][layer]['asset']
      new_asset_data = asset_data[0], bitsum, asset_data[2]
      self.tiles[pos][layer]['asset'] = new_asset_data

      raw_asset_data = self.tiles[pos][layer]['raw'][1]
      new_raw_asset_data = raw_asset_data[0], bitsum, raw_asset_data[2]
      self.tiles[pos][layer]['raw'][1] = new_raw_asset_data

    return bitsum

  # auto tiles a tile and its surrounding neighbors
  def auto_tile(self, pos: tuple, layer: str) -> None:
    self.calculate_bitsum(pos, layer, True)

    for x, y in neighbors:
      new_pos = pos[0] + x, pos[1] + y
      if new_pos in self.tiles:
        self.calculate_bitsum(new_pos, layer, True)

  def get_tile(self, pos: tuple, layer: str) -> tuple:
    if pos in self.tiles and layer in self.tiles[pos]:
      return self.tiles[pos][layer]['raw']
