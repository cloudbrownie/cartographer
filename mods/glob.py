from mods.window import Window
from mods.inputs import Inputs
from mods.chunks import Chunks
from mods.sheets import Sheets
from mods.clock import Clock
from mods.font import Font

class Glob:
  def __init__(self, w_width, w_height):
    self.COLORS = {
      'main':(26, 26, 29),
      'accent':(195, 7, 63)
    }

    self.window = Window(self, w_width, w_height)
    self.inputs = Inputs(self)
    self.font = Font('mods/font.ttf', 20)
    self.chunks = Chunks()
    self.clock = Clock()

    self.cam_zoom = 1
    self.cam_size = [w_width * 0.8, w_height]
    self.scroll_target = [-self.cam_size[0] / 2, -self.cam_size[1] / 2]
    self.scroll = [-self.cam_size[0] / 2, -self.cam_size[1] / 2]

    self.toolbar_width = w_width * 0.2

    self.cam_scroll_speed = 10

  def update(self) -> None:

    self.scroll[0] += (self.scroll_target[0] - self.scroll[0]) / 5 * self.clock.dt
    self.scroll[1] += (self.scroll_target[1] - self.scroll[1]) / 5 * self.clock.dt