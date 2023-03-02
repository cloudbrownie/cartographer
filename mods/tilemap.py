import math
import time
import pygame

neighbors = ((0, -1), (1, 0), (0, 1), (-1, 0))
entity_id = 1

class TileMap:
  def __init__(self, tile_size: int):
    self.tile_size = tile_size
    self.tiles = {}
    self.off_grid = {}
    self.layers = []

  # adds a tile to the tile map system (pos is assuemd to already be tiled)
  def add_tile(self, pos: tuple, _type: str, asset: tuple, layer: str,
               autotile: bool=False) -> None:
    pos = tuple(pos)
    raw = pos[0] * self.tile_size, pos[1] * self.tile_size

    tile_info = {'pos':pos,
                'type':_type,
                'asset':asset,
                'raw':[raw, asset]}

    if pos not in self.tiles:
      self.tiles[pos] = {layer:tile_info}
    else:
      self.tiles[pos][layer] = tile_info

    if autotile:
      self.auto_tile(pos, layer, True)

    if layer not in self.layers:
      self.layers.append(layer)
      self.layers.sort()

  # removes a tile from the tile map system
  def remove_tile(self, pos: tuple, layer: str, autotile: bool=False) -> dict:
    pos = tuple(pos)
    if pos not in self.tiles:
      return
    if layer not in self.tiles[pos]:
      return

    data = self.tiles[pos][layer]
    del self.tiles[pos][layer]

    if not self.tiles[pos]:
      del self.tiles[pos]

    if autotile:
      self._update_neighbor_bitsums(pos, layer)

    return data

  # adds an object into the off_grid dictionary
  def add_off_grid(self, pos: tuple, _type: str, asset: tuple,
                   layer: str) -> dict:
    pos = tuple(pos)

    off_grid_info = {'pos':pos,
                     'type':_type,
                     'asset':asset,
                     'raw':[pos, asset]}

    if layer not in self.off_grid:
      self.off_grid[layer] = []
    self.off_grid[layer].append(off_grid_info)

    if _type == 'entities':
      unique_id = int(time.time() * 100 + entity_id * 10000)
      self.off_grid[layer][-1]['id'] = unique_id
      entity_id += 1

    if layer not in self.layers:
      self.layers.append(layer)
      self.layers.sort()

  def remove_off_grid(self, rect: pygame.Rect, layer: str) -> dict:
    if layer not in self.tiles:
      return


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
  def auto_tile(self, pos: tuple, layer: str, sset: bool=True) -> None:
    self.calculate_bitsum(pos, layer, sset)
    self._update_neighbor_bitsums(pos, layer)

  def get_tile(self, pos: tuple, layer: str) -> tuple:
    if pos in self.tiles and layer in self.tiles[pos]:
      return self.tiles[pos][layer]['raw']

  def _update_neighbor_bitsums(self, pos: tuple, layer: str) -> None:
    for x, y in neighbors:
      neighbor = pos[0] + x, pos[1] + y
      if neighbor in self.tiles and layer in self.tiles[neighbor]:
        self.calculate_bitsum(neighbor, layer, True)

  def get_tiles(self, rect: pygame.Rect, layer: str, f: callable=None,
                inclusive: bool=True) -> list:
    tiles = []
    if inclusive:
      pos = (int(round(rect.x / self.tile_size - 0.5, 0)),
             int(round(rect.y / self.tile_size - 0.5, 0)))
      ranges = (math.ceil(rect.w / self.tile_size) + 1,
                math.ceil(rect.h / self.tile_size) + 1)
    else:
      pos = int(rect.x / self.tile_size), int(rect.y / self.tile_size)
      ranges = (math.ceil(rect.w / self.tile_size),
                math.ceil(rect.h / self.tile_size))
    for x in range(ranges[0]):
      for y in range(ranges[1]):
        curr_pos = pos[0] + x, pos[1] + y
        if curr_pos in self.tiles and layer in self.tiles[curr_pos]:
          if f:
            tiles.append(f(self.tiles[curr_pos][layer]))
          else:
            tiles.append(self.tiles[curr_pos][layer]['raw'])

    return tiles

  def flood(self, pos: tuple, layer: str, rect: pygame.Rect,
            asset: tuple, autotile: bool=False) -> int:

    open_l = [pos]
    closed_l = self.get_tiles(rect, layer, lambda x: x['pos'])
    new_tiles = []

    if pos in closed_l:
      return

    while len(open_l) > 0:
      curr = open_l.pop(0)

      for x, y in neighbors:
        neighbor = curr[0] + x, curr[1] + y
        rect_pos = (neighbor[0] * self.tile_size + self.tile_size / 2,
                    neighbor[1] * self.tile_size + self.tile_size / 2)
        if neighbor in closed_l or not rect.collidepoint(rect_pos):
          continue

        if neighbor not in open_l:
          open_l.append(neighbor)

      closed_l.append(curr)
      new_tiles.append(curr)

    for tile_pos in new_tiles:
      self.add_tile(tile_pos, 'tile', asset, layer)

      if autotile:
        self.auto_tile(tile_pos, layer, True)

    return len(new_tiles)

  def cull(self, layer: str, rect: pygame.Rect, autotile: bool=False) -> int:
    tiles = self.get_tiles(rect, layer, lambda x: x['pos'], False)
    for tile_pos in tiles:
      self.remove_tile(tile_pos, layer, autotile)