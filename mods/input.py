from ast import mod
import pygame, sys

from pygame.locals import *
from math import floor, ceil

RECT_THRESHOLD = 64

class Input:
  # init
  def __init__(self, glob):

    pygame.event.set_blocked(None)
    pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, \
      MOUSEBUTTONUP, MOUSEWHEEL])

    self.glob = glob

    self.last_pos = None
    self.selection = None

    self.mouse_pos = 0, 0

    self.cursor = pygame.Rect(0, 0, 5, 5)

    self.tools = ['draw', 'erase', 'select']
    self.tool_i = 0

    self.e_types = ['tiles', 'decor']
    self.e_i = 0

    self._layer = 0
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

    self.selected_tiles = []
    self.auto_tiling = False

    self.mouse_scroll = False

  # returns the pen position relative to camera
  @property
  def pen_pos(self) -> tuple[float, float]:
    x, y = self.canvas_pos

    if self.entity_type != 'tiles' or self.tool == 'select':
      return x, y

    t_size = self.glob.TILE_SIZE
    return x // t_size, y // t_size

  @property
  def canvas_pos(self) -> tuple[float, float]:
    scroll = self.glob.scroll
    ratio = self.glob.window.camera_ratio
    zoom = self.glob.cam_zoom
    mx, my = self.mouse_pos
    x = (mx - self.glob.tbar_width) * ratio[0] * zoom + scroll[0]
    y = my * ratio[1] * zoom + scroll[1]
    return x, y

  @property
  def layer(self) -> str:
    return str(self._layer)

  # returns the current entity type
  @property
  def entity_type(self) -> str:
    return self.e_types[self.e_i]

  # returns the current tool
  @property
  def tool(self) -> str:
    return self.tools[self.tool_i]

  # generates selection rect
  def generate_rect(self, pos: tuple, tiled: bool) -> pygame.Rect:
    if not self.last_pos:
      return None

    x = min(self.last_pos[0], pos[0])
    y = min(self.last_pos[1], pos[1])
    w = max(self.last_pos[0], pos[0]) - x
    h = max(self.last_pos[1], pos[1]) - y

    if tiled:
      tile_size = self.glob.tilemap.tile_size
      x = floor(x / tile_size) * tile_size
      y = floor(y / tile_size) * tile_size
      w = ceil(w / tile_size) * tile_size - 1
      h = ceil(h / tile_size) * tile_size - 1

    return pygame.Rect(x, y, w, h)

  # cycles through the entity types
  def cycle_entity_type(self, value : int) -> None:
    self.e_i += value
    self.e_i %= len(self.e_types)

  # called each frame to handle all events and inputs
  def handle(self) -> None:

    mx, my = pygame.mouse.get_pos()
    self.mouse_pos = mx, my
    self.cursor.centerx = mx
    self.cursor.centery = my

    keys = pygame.key.get_pressed()
    ctrl = keys[K_LCTRL] or keys[K_RCTRL]
    shift = keys[K_LSHIFT] or keys[K_RSHIFT]

    # handle each event
    for event in pygame.event.get():
      if event.type == QUIT:
        pygame.quit()
        sys.exit()

      elif event.type == KEYDOWN:

        if event.key == K_ESCAPE:
          if self.glob.window.sel_tex:
            self.glob.window.sel_tex = None
          if self.selected_tiles:
            self.selected_tiles.clear()
          if self.selection:
            self.selection = None

        elif event.key in self.arrow_bools.keys() and not ctrl and not shift:
          self.arrow_bools[event.key] = True

        elif event.key in [K_UP, K_DOWN]:
          vals = {
            K_UP: -1,
            K_DOWN: 1
          }
          if ctrl:
            self.glob.adjust_cam_zoom(vals[event.key])

          elif shift:
            self._layer -= vals[event.key]

        elif event.key in [K_1, K_2, K_3]:
          self.tool_i = event.key - K_1

        elif event.key == K_f and ctrl and self.entity_type == 'tiles' and \
            self.glob.window.sel_tex:
          if self.selection:
            rect = self.selection
          else:
            rect = self.glob.window.camera_rect

          sheet = self.glob.window.sel_sheet
          row, col = self.glob.window.curr_tex_data

          self.glob.tilemap.flood(self.pen_pos, self.layer, rect,
                                  (sheet, row, col), self.auto_tiling)
          self.selected_tiles.clear()

        elif event.key == K_d and ctrl and self.entity_type == 'tiles':

          if self.selection:
            rect = self.selection
          else:
            rect = self.glob.window.camera_rect
          self.glob.tilemap.cull(self.layer, rect, self.auto_tiling)
          self.selected_tiles.clear()

        elif event.key == K_h:

          w, h = self.glob.curr_cam_size
          self.glob.scroll_t = [-w / 2, -h / 2]

        elif event.key == K_TAB:
          if shift:
            self.glob.window.cycle_sheets(-1)
          else:
            self.glob.window.cycle_sheets(1)

        elif event.key == K_a and ctrl:
          if self.selected_tiles:
            for pos in self.glob.tilemap.tilify(self.selected_tiles):
              self.glob.tilemap.auto_tile(pos, self.layer, True)
            self.glob.window.generate_mask()
          else:
            self.auto_tiling = not self.auto_tiling

        elif event.key == K_b:
          self.selected_tiles = None

        elif event.key == K_z and ctrl:
          self.glob.undo()

        elif event.key == K_l:
          if shift:
            self.glob.window.cycle_view_mode(-1)
          else:
            self.glob.window.cycle_view_mode(1)

        elif event.key == K_e:
          if shift:
            self.cycle_entity_type(-1)
          else:
            self.cycle_entity_type(1)

        elif event.key == K_g:
          self.glob.window.show_grid = not self.glob.window.show_grid

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

            self.selected_tiles.clear()
            if ctrl and not shift:
              self.selected_tiles = self.glob.tilemap.select(self.pen_pos,
                                                             self.layer)
              self.glob.window.generate_mask()

            elif ctrl and shift:
              tile = self.glob.tilemap.get_tile(self.pen_pos, self.layer)
              if tile:
                self.selected_tiles.append(tile)
                self.glob.window.generate_mask()


            if self.tool == 'select':
              px, py = pygame.mouse.get_pos()
              self.last_pos = self.canvas_pos

            else:
              self.holding = True

        elif event.button == 2:
          self.mouse_scroll = mx > self.glob.tbar_width
          pygame.mouse.get_rel()

        elif event.button == 3:

          if self.glob.window.sel_tex:
            self.glob.window.sel_tex = None

      elif event.type == MOUSEBUTTONUP:

        if event.button == 1:

          self.holding = False
          self.prev_texture = None

          if mx > self.glob.tbar_width and self.tool == 'select':
            self.selection = self.generate_rect(self.canvas_pos,
                                                self.entity_type == 'tiles')
            if self.selection.w * self.selection.h < RECT_THRESHOLD:
              self.selection = None
            else:
              self.selected_tiles.clear()
              self.selected_tiles = self.glob.tilemap.get_tiles(self.selection,
                                                                self.layer,
                                                                inclusive=False)
              self.glob.window.generate_mask()

          self.last_pos = None

        elif event.button == 2:
          self.mouse_scroll = False

      elif event.type == MOUSEWHEEL:

        if mx < self.glob.tbar_width:
          self.glob.window.add_texture_scroll(event.y)

        elif mx > self.glob.tbar_width:
          self.glob.adjust_cam_zoom(-event.y)

    # if holding and drawing, add to the chunk's stuff
    if self.holding:
      px, py = self.pen_pos
      layer = self.layer

      texture = self.glob.window.sel_tex
      if self.tool == 'draw' and texture:

        if self.entity_type == 'tiles' and ((px, py) != self.last_pos or \
            texture != self.prev_texture):

          sheet = self.glob.window.sel_sheet
          row, col = self.glob.window.curr_tex_data

          # new method for adding tiles to tilemap
          self.glob.tilemap.add_tile(self.pen_pos, 'tile', (sheet, row, col),
                                     layer, self.auto_tiling)

          self.last_pos = px, py
          self.prev_texture = texture

        '''
        elif self.entity_type == 'decor':

          sheet = self.glob.window.sel_sheet
          row, col = self.glob.window.curr_tex_data
          surf = self.glob.sheets.sheets[sheet][row][col]
          w, h = surf.get_size()
          x = px - w / 2
          y = py - h / 2

          add_decor = self.glob.chunks.add_decor(x, y, _layer, sheet,
            (row, col), (w, h))
          self.holding = False
        '''

      elif self.tool == 'erase':

        if self.entity_type == 'tiles' and (px, py) != self.last_pos:

          self.glob.tilemap.remove_tile(self.pen_pos, layer, self.auto_tiling)

          self.last_pos = px, py

        '''
        elif self.entity_type == 'decor':

          sheet = self.glob.window.sel_sheet
          del_decor = self.glob.chunks.remove_decor(px, py, _layer)
        '''

    # move the scroll target with the arrows
    for key in self.arrow_bools:
      if self.arrow_bools[key]:
        dt = self.glob.clock.dt
        cam_speed = self.glob.cam_speed
        zoom = self.glob.cam_zoom
        self.glob.scroll_t[0] += self.arrow_vals[key][0] * cam_speed * dt * zoom
        self.glob.scroll_t[1] += self.arrow_vals[key][1] * cam_speed * dt * zoom

    # move scroll traget with the mouse if mouse scrolling
    if self.mouse_scroll:
      dx, dy = pygame.mouse.get_rel()
      dx *= self.glob.cam_zoom * self.glob.window.camera_ratio[0]
      dy *= self.glob.cam_zoom * self.glob.window.camera_ratio[1]

      self.glob.scroll_t[0] -= dx
      self.glob.scroll_t[1] -= dy
      self.glob.scroll[0] -= dx
      self.glob.scroll[1] -= dy