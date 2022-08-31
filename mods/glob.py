from mods.chunks import Chunks
from mods.sheets import Sheets
from mods.window import Window
from mods.input import Input
from mods.clock import Clock
from mods.font import Font

from multiprocessing import Process, Queue
from time import time
from pickle import loads

from mods.chunks import is_inbounds

def hex_to_rgb(hex_code : str) -> tuple:
  if '#' in hex_code:
    hex_code.replace('#', '')
  rgb = []
  for i in range(3):
    rgb.append(int(hex_code[i*2:2+i*2], 16))

  return tuple(rgb)

DONE = 1

# flooding function
def flood(pos : tuple, layer : str, chunks : Chunks, q : Queue, \
    rect : list) -> None:
  tile_x, tile_y = pos
  chunk_x, chunk_y = chunks.chunk_pos(*pos)
  tag = chunks.get_chunk_tag(chunk_x, chunk_y)

  rel_coords = chunks.rel_tile_pos(tile_x, tile_y)

  if tag in chunks.chunks and layer in chunks.chunks[tag]['tiles']:
    for tile_data in chunks.chunks[tag]['tiles'][layer]:
      if tile_data[0:2] == rel_coords:
        return 

  left, right, top, bot = chunks.get_bounds(rect)

  if not (left <= tile_x <= right) or not (top <= tile_y <= bot):
    return

  open_l = [(tile_x, tile_y)]
  closed_l = []

  if tag in chunks.chunks:
    for tile_data in chunks.chunks[tag]['tiles'][layer]:
      closed_l.append(tile_data[0:2])

  for o_tag in chunks.get_chunks(rect):
    if layer not in chunks.chunks[o_tag]['tiles']:
      continue

    for rel_tile_data in chunks.chunks[o_tag]['tiles'][layer]:
      chunk_x, chunk_y = chunks.deformat_chunk_tag(o_tag)
      rel_tile_x, rel_tile_y = rel_tile_data[0:2]

      o_tile_x = rel_tile_x + chunk_x * chunks.CHUNK_SIZE
      o_tile_y = rel_tile_y + chunk_y * chunks.CHUNK_SIZE

      closed_l.append((o_tile_x, o_tile_y))

  if (tile_x, tile_y) in closed_l:
    return

  q.put((tile_x, tile_y))
  while len(open_l) > 0:
    curr_x, curr_y = open_l.pop(0)

    for nx, ny in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
      n_pos = curr_x + nx, curr_y + ny

      if n_pos in closed_l or not is_inbounds(n_pos, left, right, top, bot):
        continue

      if n_pos not in open_l:
        open_l.append(n_pos)

    closed_l.append((curr_x, curr_y))
    q.put_nowait((curr_x, curr_y))

  q.put(DONE)

# culling function
def cull(e_type : str, layer : str, chunks : Chunks, q : Queue, \
    rect : list) -> None:
  bound_chunks = chunks.get_chunks(rect, skip_empty=True)

  if e_type == 'tiles':

    left, right, top, bot = chunks.get_bounds(rect)
    for tag in bound_chunks:
      if layer not in chunks.chunks[tag]['tiles']:
        continue

      cx, cy = chunks.deformat_chunk_tag(tag)
      for tile_data in chunks.chunks[tag]['tiles'][layer]:
        rel_x, rel_y = tile_data[0:2]

        glob_x = rel_x + cx * chunks.CHUNK_SIZE
        glob_y = rel_y + cy * chunks.CHUNK_SIZE

        if left <= glob_x <= right and top <= glob_y <= bot:
          q.put((glob_x, glob_y))

  q.put(DONE)

# auto tiling function
def auto_tile(tiles : list, layer : str, chunks : Chunks, q : Queue) -> None:

  for x, y in tiles:
    tile = chunks.get_tile(x, y, layer)
    bitsum = chunks.calculate_bitsum(x, y, tile, layer)

    q.put((x, y, bitsum))
  
  q.put(DONE)

class Glob:
  # init
  def __init__(self, w_width, w_height):
    self.COLORS = {
      'main':hex_to_rgb('1a1a1d'),
      'accent':hex_to_rgb('c3073f'),
      'a_comp':hex_to_rgb('950740')
    }

    self.cam_zoom_i = 2
    self.tex_zoom_i = 3
    self.zoom_vals = [0.25, 0.5, 1, 2, 4, 8]
    self.cam_scale_size = w_width * 0.8, w_height
    self.cam_zoom = self.zoom_vals[self.cam_zoom_i]
    self.cam_zoom_t = self.cam_zoom

    self.base_cam_size = w_width * 0.8 / 2, w_height / 2
    self.curr_cam_size = self.base_cam_size
    self.scroll_t = [-self.curr_cam_size[0] / 2, -self.curr_cam_size[1] / 2]
    self.scroll = [-self.curr_cam_size[0] / 2, -self.curr_cam_size[1] / 2]
    self.SCROLL_TOL = 0.01
    self.ZOOM_TOL = 0.01
    self.cam_speed = 10

    self.chunks = Chunks()
    self.sheets = Sheets()
    font_size = 20
    self.window = Window(self, w_width, w_height, font_size)
    self.font = Font('mods/font.ttf', font_size)
    self.input = Input(self)
    self.clock = Clock()

    self.tbar_width = w_width * 0.2
    self.last_chunk_prune = 0
    self.CHUNK_PRUNE_TIME = 30

    # TODO: share mem between all processes.
    # these processes end up doing work without acknowledging each other's work 
    # and end up wasting time.
    self.chunk_processes = {
      'flood':[],
      'cull':[],
      'auto-tile':[]
    }

    self.prev_chunk_states = []

  # creates a process for flood filling in the chunk system
  def start_flood(self, pos : tuple, layer : str, rect : list, \
      sheet_name : str, sheet_coords : tuple) -> None:
    queue = Queue()

    process = Process(target=flood, args=(pos, layer, self.chunks, queue, rect))
    process.daemon = True
    process.start()

    process_data = process, queue, layer, sheet_name, sheet_coords, \
      self.input.auto_tiling
    self.chunk_processes['flood'].append(process_data)

    self.prev_chunk_states.append(self.chunks.copy())

  # creates a process for culling tiles in the chunk system
  def start_cull(self, e_type : str, layer : str, rect : list) -> None:
    queue = Queue()

    process = Process(target=cull, args=(e_type, layer, self.chunks, queue, \
      rect))
    process.daemon = True
    process.start()

    process_data = process, queue, layer
    self.chunk_processes['cull'].append(process_data)

    self.prev_chunk_states.append(self.chunks.copy())

  # creates a process for auto tiling a list of tiles
  def start_auto_tile(self, tiles : list, layer : str) -> None:
    queue = Queue()

    process = Process(target=auto_tile, args=(tiles, layer, self.chunks, queue))
    process.daemon = True
    process.start()

    process_data = process, queue, layer
    self.chunk_processes['auto-tile'].append(process_data)

    self.prev_chunk_states.append(self.chunks.copy())

  # update camera zoom value
  def adjust_cam_zoom(self, val : int) -> None:
    self.cam_zoom_i += val
    self.cam_zoom_i = min(self.cam_zoom_i, len(self.zoom_vals) - 1)
    self.cam_zoom_i = max(self.cam_zoom_i, 0)
    self.cam_zoom_t = self.zoom_vals[self.cam_zoom_i]

  # returns the current texture zoom value
  @property
  def tex_zoom(self) -> float:
    return self.zoom_vals[self.tex_zoom_i]

  # reverts to previous chunk state if one exists
  def undo(self) -> None:
    if len(self.prev_chunk_states) > 0:
      pickle = self.prev_chunk_states.pop()
      unpickled = loads(pickle)

      self.chunks.chunks = unpickled

      self.window.render_cache.clear()

  # called each frame to update global stuff
  def update(self) -> None:

    # update the scroll value
    if self.scroll[0] != self.scroll_t[0]:
      d_scroll = (self.scroll_t[0] - self.scroll[0]) / 5
      d_scroll = min(d_scroll, d_scroll * self.clock.dt)
      self.scroll[0] += d_scroll
      if abs(self.scroll[0] - self.scroll_t[1]) <= self.SCROLL_TOL:
        self.scroll[0] = self.scroll_t[0]

    if self.scroll[1] != self.scroll_t[1]:
      d_scroll = (self.scroll_t[1] - self.scroll[1]) / 5
      d_scroll = min(d_scroll, d_scroll * self.clock.dt)
      self.scroll[1] += d_scroll
      if abs(self.scroll[0] - self.scroll_t[1]) <= self.SCROLL_TOL:
        self.scroll[1] = self.scroll_t[1]

    self.window.camera_rect.topleft = self.scroll

    # adjust camera size
    if self.cam_zoom != self.cam_zoom_t:
      self.cam_zoom += (self.cam_zoom_t - self.cam_zoom) / 15 * self.clock.dt 
      if abs(self.cam_zoom - self.cam_zoom_t) <= self.ZOOM_TOL:
        self.cam_zoom = self.cam_zoom_t
      self.window.update_camera_size()

    # adjust the texture scroll
    if self.window.tex_scroll != self.window.tex_scroll_t:
      self.window.update_texture_scroll()

    # prune the chunks regularly
    if time() - self.last_chunk_prune >= self.CHUNK_PRUNE_TIME:
      self.chunks.prune()
      self.last_chunk_prune = time()

    # add tiles from flood processes
    for i, process_data in enumerate(self.chunk_processes['flood']):
      
      process, queue, layer, sheet_name, sheet_coords, auto_tile = process_data

      while not queue.empty():
        queue_item = queue.get_nowait()
        if queue_item == DONE:      
          self.chunk_processes['flood'].pop(i)
          process.terminate()
          queue.close()
          queue.join_thread()
          break
        else:
          self.chunks.add_tile(*queue_item, layer, sheet_name, sheet_coords, \
            auto_tile)

    # remove tiles from cull process
    for i, process_data in enumerate(self.chunk_processes['cull']):
      
      process, queue, layer = process_data

      n_items = queue.qsize()
      for _ in range(min(n_items, 2560)):
        queue_item = queue.get()
        if queue_item == DONE:
          self.chunk_processes['cull'].pop(i)
          process.terminate()
          queue.close()
          queue.join_thread()
          break
        else:
          self.chunks.remove_tile(*queue_item, layer)

    # change bitsums from auto tile
    for i, process_data in enumerate(self.chunk_processes['auto-tile']):

      process, queue, layer = process_data

      while not queue.empty():
        queue_item = queue.get_nowait()
        if queue_item == DONE:
          self.chunk_processes['auto-tile'].pop(i)
          process.terminate()
          queue.close()
          queue.join_thread()
          self.input.selected_tiles.clear()
          break
        else:
          x, y, bitsum = queue_item
          tile = self.chunks.get_tile(x, y, layer)
          tile[3] = bitsum
          chunk_pos = self.chunks.chunk_pos(x, y)
          tag = self.chunks.get_chunk_tag(*chunk_pos)
          self.chunks.re_render.add(tag)

