import math

class TileMap:
  def __init__(self, tile_size):
    self.tile_size = tile_size
    self.tiles = {}
    self.off_grid = {}
    self.layers = []

  def add_tile(self, pos, tile_type, asset_info, layer):
    pos = tuple(pos)
    raw = pos[0] * self.tile_size, pos[1] * self.tile_size

    tile_info = {'pos':pos,
                'type':tile_type,
                'asset':asset_info,
                'raw':[raw, asset_info]}

    if pos not in self.tiles:
      self.tiles[pos] = {layer:tile_info}
    elif layer not in self.tiles[pos]:
      self.tiles[pos][layer] = tile_info
    else:
      self.tiles[pos][layer].append(tile_info)

    if layer not in self.layers:
      self.layers.append(layer)
      self.layers.sort()

  def remove_tile(self, pos, layer=None):
    pos = tuple(pos)
    if pos not in self.tiles:
      return

    if layer and layer in self.tiles[pos]:
      data = self.tiles[pos][layer]
      del self.tiles[pos][layer]
      return data

  def get_visible(self, pos, size):
    layer_data = {l : [] for l in self.layers}

    pos = int(pos[0] / self.tile_size), int(pos[1] / self.tile_size)
    for x in range(math.ceil(size[0] / self.tile_size) + 1):
      for y in range(math.ceil(size[1] / self.tile_size) + 1):
        tile_pos = x + pos[0], y + pos[1]
        if tile_pos in self.tiles:
          for tile in self.tiles[pos]:
            layer_data[tile].append(self.tiles[pos][tile]['raw'])