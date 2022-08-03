import pygame, sys

from pygame.locals import *

class Inputs:
  # init
  def __init__(self, glob):

    pygame.event.set_blocked(None)
    pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])

    self.glob = glob

    self.sel_box = [None, None]

    self.mods = {
      pygame.K_LSHIFT : False,
      pygame.K_LCTRL : False,
    }

    self.mouse_pos = 0, 0

    self.cursor = pygame.Rect(0, 0, 5, 5)

    self.tools = ['draw', 'erase', 'select']
    self.tool_i = 0

    self.e_types = ['tiles', 'decor']
    self.e_i = 0

    self.layer = 0
    self.holding = False

    self.arrow_bools = {
      pygame.K_UP : False,
      pygame.K_DOWN : False,
      pygame.K_LEFT : False,
      pygame.K_RIGHT : False
    }

    self.arrow_vals = {
      pygame.K_UP : (0, -1),
      pygame.K_DOWN : (0, 1),
      pygame.K_LEFT : (-1, 0),
      pygame.K_RIGHT : (1, 0)
    }

  # returns the pen position relative to camera
  @property
  def pen_pos(self) -> tuple[float, float]:
    mx = (self.mouse_pos[0] - self.glob.toolbar_width) * self.glob.cam_zoom + self.glob.scroll[0]
    my = self.mouse_pos[1] * self.glob.cam_zoom + self.glob.scroll[1]

    if self.e_types[self.e_i] != 'tiles' or self.tools[self.tool_i] != 'draw':
      return mx, my

    return mx // self.glob.chunks.tile_size, my // self.glob.chunks.tile_size

  def handle(self) -> None:

    self.mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()

        elif event.key in self.arrow_bools.keys():
          self.arrow_bools[event.key] = True

      elif event.type == pygame.KEYUP:

        if event.key in self.arrow_bools.keys():
          self.arrow_bools[event.key] = False


    for key in self.arrow_bools:
      if self.arrow_bools[key]:
        self.glob.scroll_target[0] += self.arrow_vals[key][0] * self.glob.cam_scroll_speed * self.glob.clock.dt
        self.glob.scroll_target[1] += self.arrow_vals[key][1] * self.glob.cam_scroll_speed * self.glob.clock.dt
