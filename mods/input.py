from ast import mod
import pygame, sys

from pygame.locals import *
from math import floor, ceil

class Input:
  # init
  def __init__(self, glob):

    pygame.event.set_blocked(None)
    pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, \
      MOUSEBUTTONUP, MOUSEWHEEL])

    self.glob = glob

    self.sel_rect = []
    self.SEL_RECT_THRESOLD = 64

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

    self.selected_tiles = []
    self.auto_tiling = False

    self.mouse_scroll = False

  # returns the pen position relative to camera
  @property
  def pen_pos(self) -> tuple[float, float]:
    scroll = self.glob.scroll
    ratio = self.glob.window.camera_ratio
    zoom = self.glob.cam_zoom
    mx, my = self.mouse_pos
    x = round((mx - self.glob.tbar_width) * ratio[0] * zoom + scroll[0], 2)
    y = round(my * ratio[1] * zoom + scroll[1])

    if self.entity_type != 'tiles' or self.tool == 'select':
      return x, y

    t_size = self.glob.chunks.TILE_SIZE
    return x // t_size, y // t_size
  # returns the current entity type
  @property
  def entity_type(self) -> str:
    return self.e_types[self.e_i]

  # returns the current tool
  @property
  def tool(self) -> str:
    return self.tools[self.tool_i]

  # returns the normalized selection rect
  @property
  def selection_rect(self) -> list:
    if len(self.sel_rect) < 2:
      return 0, 0, 0, 0

    if len(self.sel_rect) == 1:
      p2 = self.pen_pos
    else:
      p2 = self.sel_rect[1]

    left, top, right, bot = *self.sel_rect[0], *p2
    if right < left:
      left, right = right, left
    if bot < top:
      top, bot = bot, top

    w = right - left
    h = bot - top
    if w * h < self.SEL_RECT_THRESOLD:
      return 0, 0, 0, 0

    return left, top, w, h

  # returns if the current selection rect is valid
  def has_valid_sel_rect(self) -> bool:
    w, h = self.selection_rect[2:4]
    return w * h >= self.SEL_RECT_THRESOLD

  # cycles through the entity types
  def cycle_entity_type(self, value : int) -> None:
    self.e_i += value
    self.e_i %= len(self.e_types)

  # called each frame to handle all events and inputs
  def handle(self) -> None:

    mx, my = pygame.mouse.get_pos()
    self.mouse_pos = mx, my

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
          if self.has_valid_sel_rect():
            self.sel_rect = []
          else:
            pygame.quit()
            sys.exit()

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
            self.layer -= vals[event.key]

        elif event.key in [K_1, K_2, K_3]:
          self.tool_i = event.key - K_1

        elif event.key == K_f and ctrl and self.entity_type == 'tiles' and \
            self.glob.window.sel_tex:
          if self.has_valid_sel_rect() and len(self.sel_rect) > 1:
            rect = self.selection_rect
          else:
            rect = self.glob.window.camera_rect
          pos = self.pen_pos
          curr_layer = str(self.layer)
          sheet_name = self.glob.window.sel_sheet
          sheet_coords = self.glob.window.curr_tex_data
          self.glob.start_flood(pos, curr_layer, rect, sheet_name, sheet_coords)
          self.selected_tiles.clear()

        elif event.key == K_d and ctrl and self.entity_type == 'tiles':

          if self.has_valid_sel_rect() and len(self.sel_rect) > 1:
            rect = self.selection_rect
          else:
            rect = self.glob.window.camera_rect
          self.glob.start_cull(self.entity_type, str(self.layer), rect)
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
            self.glob.start_auto_tile(self.selected_tiles, str(self.layer))
          else:
            self.auto_tiling = not self.auto_tiling

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

            if self.tool == 'select':
              self.sel_rect = [self.pen_pos]

            elif ctrl and shift and self.entity_type == 'tiles':
              px, py = self.pen_pos
              curr_layer = str(self.layer)
              rect = self.glob.window.camera_rect
              self.selected_tiles = self.glob.chunks.mask_select(px, py, \
                curr_layer, rect)
            else:
              self.holding = True
              self.selected_tiles.clear()

        elif event.button == 2:
          self.mouse_scroll = mx > self.glob.tbar_width
          pygame.mouse.get_rel()

        elif event.button == 3:

          if self.glob.window.sel_tex:
            self.glob.window.sel_tex = None

      elif event.type == MOUSEBUTTONUP:

        if event.button == 1:

          self.holding = False
          self.last_pos = None
          self.prev_texture = None
          self.glob.prev_chunk_states.append(self.glob.chunks.copy())
          
          if mx > self.glob.tbar_width and self.tool == 'select':
            self.sel_rect.append(self.pen_pos)

            if not self.has_valid_sel_rect:
              self.sel_rect = []
            elif self.entity_type == 'tiles':
              left, top, right, bot = *self.sel_rect[0], *self.sel_rect[1]
              t_size = self.glob.chunks.TILE_SIZE
              left = floor(left / t_size) * t_size
              top = floor(top / t_size) * t_size
              right = ceil(right / t_size) * t_size - 1
              bot = ceil(bot / t_size) * t_size - 1
              self.sel_rect = [(left, top), (right, bot)]

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

      texture = self.glob.window.sel_tex
      if self.tool == 'draw' and texture:
        
        if self.entity_type == 'tiles' and ((px, py) != self.last_pos or \
            texture != self.prev_texture):
    
          sheet = self.glob.window.sel_sheet
          sheet_coords = self.glob.window.curr_tex_data
          curr_layer = str(self.layer)
              
          add_tile = self.glob.chunks.add_tile(px, py, curr_layer, sheet,
            sheet_coords, self.auto_tiling)

          self.last_pos = px, py
          self.prev_texture = texture
        
        elif self.entity_type == 'decor':

          sheet = self.glob.window.sel_sheet
          row, col = self.glob.window.curr_tex_data
          curr_layer = str(self.layer)
          surf = self.glob.sheets.sheets[sheet][row][col]
          w, h = surf.get_size()
          x = px - w / 2
          y = py - h / 2

          add_decor = self.glob.chunks.add_decor(x, y, curr_layer, sheet, 
            (row, col), (w, h))
          self.holding = False

      elif self.tool == 'erase':

        if self.entity_type == 'tiles' and (px, py) != self.last_pos:

          curr_layer = str(self.layer)
          del_tile = self.glob.chunks.remove_tile(px, py, curr_layer, \
            self.auto_tiling)
          self.last_pos = px, py

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