import math
import time
import pygame

from mods.kd import KDTree

neighbors = ((0, -1), (1, 0), (0, 1), (-1, 0))
entity_id = 1

class TileMap:
  def __init__(self, tile_size: int):
    self.tile_size = tile_size
    self.tiles = {}
    self.off_grid = {}
    self.layers = []
    self.entities = {}

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

    # entities are just spatial hashed during map creation
    if _type == 'entities':
      unique_id = int(time.time() * 100 + entity_id * 10000)
      if layer not in self.entities:
        self.entities[layer] = []
      off_grid_info['id'] = unique_id
      self.entities[layer].append(off_grid_info)
      entity_id += 1

    else:
      if layer not in self.off_grid:
        self.off_grid[layer] = KDTree(90)
      self.off_grid[layer].put(pos, off_grid_info)

    if layer not in self.layers:
      self.layers.append(layer)
      self.layers.sort()

  # removes an object from the off_grid dictionary
  def remove_off_grid(self, rect: pygame.Rect, layer: str) -> list:
    if layer not in self.tiles:
      return

    remove = []
    for i, tile in sorted(enumerate(self.off_grid[layer]), reverse=True):
      tile_rect = pygame.Rect(tile['raw'][0][0], tile['raw'][0][1],
                              self.tile_size, self.tile_size)
      if rect.colliderect(tile_rect):
        remove.append(self.off_grid[layer][i])
        self.off_grid[layer].pop(i)

    return remove

  # returns all tiles visible within the given rect
  def get_visible(self, pos: tuple, size: int) -> list:
    layer_data = {l : [] for l in self.layers}

    # gather tiles
    tiled_pos = (int(round(pos[0] / self.tile_size - 0.5, 0)),
          int(round(pos[1] / self.tile_size - 0.5, 0)))
    for x in range(math.ceil(size[0] / self.tile_size) + 1):
      for y in range(math.ceil(size[1] / self.tile_size) + 1):
        tile_pos = x + tiled_pos[0], y + tiled_pos[1]
        if tile_pos in self.tiles:
          for tile in self.tiles[tile_pos]:
            layer_data[tile].append(self.tiles[tile_pos][tile]['raw'])

    query_rect = pygame.Rect(pos, size)

    # gather decor
    for layer in self.off_grid:
      query = self.off_grid[layer].range(query_rect)
      for decor in query:
        layer_data[layer].append(decor['raw'])

    # gather entities
    for layer in self.entities:
      for entity in self.entities[layer]:
        if query_rect.collidepoint(entity['pos']):
          layer_data[layer].append(entity['raw'])

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

  # returns a tiles raw data
  def get_tile(self, pos: tuple, layer: str) -> tuple:
    if pos in self.tiles and layer in self.tiles[pos]:
      return self.tiles[pos][layer]['raw']

  # private method used for updating neighbor bitsums for autotiling
  # (assumes tile can be autotiled)
  def _update_neighbor_bitsums(self, pos: tuple, layer: str) -> None:
    for x, y in neighbors:
      neighbor = pos[0] + x, pos[1] + y
      if neighbor in self.tiles and layer in self.tiles[neighbor]:
        self.calculate_bitsum(neighbor, layer, True)

  # returns all tiles within specified rect
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

  # flood fills an area with tiles and can autotile the tiles too
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

  # culls all tiles within a specified rect
  def cull(self, layer: str, rect: pygame.Rect, autotile: bool=False) -> int:
    tiles = self.get_tiles(rect, layer, lambda x: x['pos'], False)
    for tile_pos in tiles:
      self.remove_tile(tile_pos, layer, autotile)

  # returns all tiles connected to the tile at pos
  def select(self, pos: tuple, layer: str) -> list:
    open_l = [pos]
    closed_l = []

    if pos not in self.tiles or layer not in self.tiles[pos]:
      return []

    tiles = []

    while len(open_l) > 0:
      curr = open_l.pop(0)

      for x, y in neighbors:
        neighbor = curr[0] + x, curr[1] + y
        if neighbor in closed_l:
          continue

        if neighbor in self.tiles and layer in self.tiles[neighbor]:
          open_l.append(neighbor)

      closed_l.append(curr)
      tiles.append(self.tiles[curr][layer]['raw'])

    return tiles

  # assumes tiles input is of tile raw data, converts raw data into tiled pos
  def tilify(self, tiles: list) -> list:
    tiled = []
    for (x, y), _ in tiles:
      tiled.append((x // self.tile_size, y // self.tile_size))
    return tiled