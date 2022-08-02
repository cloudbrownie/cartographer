try:
  from mods.window import Window
  from mods.inputs import Inputs
  from mods.chunks import Chunks
except:
  from window import Window
  from inputs import Inputs
  from chunks import Chunks

class Glob:
  def __init__(self, w_width, w_height):
    self.window = Window(self, w_width, w_height)
    self.inputs = Inputs(self)

    self.COLORS = {
      'main':(26, 26, 29),
      'accent':(195, 7, 63)
    }
