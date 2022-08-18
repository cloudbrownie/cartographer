from mods.chunks import Chunks
from mods.sheets import Sheets
from mods.window import Window
from mods.input import Input
from mods.clock import Clock
from mods.font import Font

def hex_to_rgb(hex_code : str) -> tuple:
  if '#' in hex_code:
    hex_code.replace('#', '')
  rgb = []
  for i in range(3):
    rgb.append(int(hex_code[i*2:2+i*2], 16))

  return tuple(rgb)

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
    self.zoom_vals = [0.25, 0.5, 1, 2, 4]
    self.cam_scale_size = w_width * 0.8, w_height
    self.cam_zoom = self.zoom_vals[self.cam_zoom_i]
    self.cam_zoom_t = self.cam_zoom

    self.base_cam_size = w_width * 0.8 / 2, w_height / 2
    self.curr_cam_size = self.base_cam_size
    self.scroll_t = [-self.curr_cam_size[0] / 2, -self.curr_cam_size[1] / 2]
    self.scroll = [-self.curr_cam_size[0] / 2, -self.curr_cam_size[1] / 2]
    self.SCROLL_TOL = 0.01
    self.ZOOM_TOL = 0.001
    self.cam_speed = 10

    self.chunks = Chunks()
    self.sheets = Sheets()
    font_size = 20
    self.window = Window(self, w_width, w_height, font_size)
    self.font = Font('mods/font.ttf', font_size)
    self.input = Input(self)
    self.clock = Clock()

    self.tbar_width = w_width * 0.2

    print(self.chunks.chunks)
    for i in range(8):
      self.chunks.add_tile(0, 64 - 16 * i, '0', 'grass.png', (3, 0))
    print(self.chunks.chunks)

  # update camera zoom value
  def adjust_cam_zoom(self, val : int) -> None:
    self.cam_zoom_i += val
    self.cam_zoom_i %= len(self.zoom_vals)
    self.cam_zoom_i = max(self.cam_zoom_i, 0)
    self.cam_zoom_t = self.zoom_vals[self.cam_zoom_i]

  # returns the current texture zoom value
  @property
  def tex_zoom(self) -> float:
    return self.zoom_vals[self.tex_zoom_i]

  # called each frame to update global stuff
  def update(self) -> None:

    # update the scroll value
    if self.scroll[0] != self.scroll_t[0]:
      self.scroll[0] += (self.scroll_t[0] - self.scroll[0]) / 5 * self.clock.dt
      if abs(self.scroll[0] - self.scroll_t[1]) <= self.SCROLL_TOL:
        self.scroll[0] = self.scroll_t[0]

    if self.scroll[1] != self.scroll_t[1]:
      self.scroll[1] += (self.scroll_t[1] - self.scroll[1]) / 5 * self.clock.dt
      if abs(self.scroll[0] - self.scroll_t[1]) <= self.SCROLL_TOL:
        self.scroll[1] = self.scroll_t[1]

    self.window.camera_rect.topleft = self.scroll

    # adjust camera size
    if self.cam_zoom != self.cam_zoom_t:
      self.cam_zoom += (self.cam_zoom_t - self.cam_zoom) / 15 * self.clock.dt 
      if abs(self.cam_zoom - self.cam_zoom_t) <= self.ZOOM_TOL:
        self.cam_zoom = self.cam_zoom_t
      self.window.update_camera_size()