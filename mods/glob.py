from mods.window import Window
from mods.inputs import Inputs
from mods.chunks import Chunks
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