import pygame, sys

from pygame.locals import *

class Input:
  # init
  def __init__(self, glob):

    pygame.event.set_blocked(None)
    pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP])

    self.glob = glob

    self.sel_box = [None, None]

    self.mouse_pos = 0, 0

    self.cursor = pygame.Rect(0, 0, 5, 5)

    self.tools = ['draw', 'erase', 'select']
    self.tool_i = 0

    self.e_types = ['tiles', 'decor']
    self.e_i = 0

    self.layer = 0
    self.holding = False
    self.last_pos = None
    self.prev_texture = None

    self.arrow_bools = {
      K_UP : False,
      K_DOWN : False,
      K_LEFT : False,
      K_RIGHT : False
    }

    self.arrow_vals = {
      K_UP : (0, -1),
      K_DOWN : (0, 1),
      K_LEFT : (-1, 0),
      K_RIGHT : (1, 0)
    }

  # returns the pen position relative to camera
  @property
  def pen_pos(self) -> tuple[float, float]:
    scroll = self.glob.scroll
    ratio = self.glob.window.camera_ratio
    zoom = self.glob.cam_zoom
    mx, my = self.mouse_pos
    x = (mx - self.glob.tbar_width) * ratio[0] * zoom + scroll[0]
    y = my * ratio[1] * zoom + scroll[1]

    if self.entity_type != 'tiles' or self.tool != 'draw':
      return x, y

    t_size = self.glob.chunks.TILE_SIZE
    return x // t_size * t_size, y // t_size * t_size

  # returns the current entity type
  @property
  def entity_type(self) -> str:
    return self.e_types[self.e_i]

  # returns the current tool
  @property
  def tool(self) -> str:
    return self.tools[self.tool_i]

  # returns if the input is currently drawing
  def is_drawing(self) -> bool:
    return self.tool == 'draw'

  # called each frame to handle all events and inputs
  def handle(self) -> None:

    mx, my = pygame.mouse.get_pos()
    self.mouse_pos = mx, my

    keys = pygame.key.get_pressed()
    ctrl = keys[K_LCTRL]

    # handle each event
    for event in pygame.event.get():
      if event.type == QUIT:
        pygame.quit()
        sys.exit()

      elif event.type == KEYDOWN:

        if event.key == K_ESCAPE:
          pygame.quit()
          sys.exit()

        elif event.key in self.arrow_bools.keys() and not ctrl:
          self.arrow_bools[event.key] = True

        elif event.key in [K_UP, K_DOWN] and ctrl:
          vals = {
            K_UP: -1,
            K_DOWN: 1
          }

          self.glob.adjust_cam_zoom(vals[event.key])

      elif event.type == KEYUP:

        if event.key in self.arrow_bools.keys():
          self.arrow_bools[event.key] = False

      elif event.type == MOUSEBUTTONDOWN:

        if event.button == 1:

          if mx <= self.glob.tbar_width:
            window = self.glob.window
          
            if my <= window.div_height and window.hov_sheet:
              window.set_selected_sheet(window.hov_sheet)

            elif my >= window.div_height and window.hov_tex:
              window.set_selected_texture(window.hov_tex)

          elif mx > self.glob.tbar_width:

            self.holding = True

        elif event.button == 3:

          if self.glob.window.sel_tex:
            self.glob.window.sel_tex = None

      elif event.type == MOUSEBUTTONUP:

        if event.button == 1:

          if mx > self.glob.tbar_width:
            self.holding = False

    # if holding and drawing, add to the chunk's stuff
    if self.holding:
      px, py = self.pen_pos

      texture = self.glob.window.sel_tex
      if self.is_drawing and texture:
        
        if self.entity_type == 'tiles' and ((px, py) != self.last_pos or 
                                                  texture != self.prev_texture):
    
          sheet = self.glob.window.sel_sheet
          sheet_coords = self.glob.window.curr_tex_data
          curr_layer = str(self.layer)

          self.glob.chunks.add_tile(px, py, curr_layer, sheet, sheet_coords)

          self.last_pos = px, py
          self.prev_texture = texture

    # move the scroll target with the arrows
    for key in self.arrow_bools:
      if self.arrow_bools[key]:
        dt = self.glob.clock.dt
        cam_speed = self.glob.cam_speed
        zoom = self.glob.cam_zoom
        self.glob.scroll_t[0] += self.arrow_vals[key][0] * cam_speed * dt * zoom
        self.glob.scroll_t[1] += self.arrow_vals[key][1] * cam_speed * dt * zoom
