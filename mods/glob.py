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

    self.chunks = Chunks()
    self.sheets = Sheets()
    font_size = 20
    self.window = Window(self, w_width, w_height, font_size)
    self.font = Font('mods/font.ttf', font_size)
    self.input = Input(self)
    self.clock = Clock()

    self.cam_zoom = 1
    self.cam_size = [w_width * 0.8, w_height]
    self.scroll_t = [-self.cam_size[0] / 2, -self.cam_size[1] / 2]
    self.scroll = [-self.cam_size[0] / 2, -self.cam_size[1] / 2]

    self.tbar_width = w_width * 0.2

    self.cam_speed = 10

  # called each frame to update global stuff
  def update(self) -> None:

    # update the scroll value
    self.scroll[0] += (self.scroll_t[0] - self.scroll[0]) / 5 * self.clock.dt
    self.scroll[1] += (self.scroll_t[1] - self.scroll[1]) / 5 * self.clock.dt
