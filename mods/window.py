import pygame

from pygame.draw import *

from math import floor

class Window:
  # init
  def __init__(self, glob, width, height, font_size):
    self.glob = glob

    pygame.init()
    
    self.window = pygame.display.set_mode((width, height))
    self.width = width
    self.height = height

    self.camera = pygame.Surface((width * 0.8, height))

    self.tbar_scroll = 0

    n_sheets = len(self.glob.sheets.sheets)
    self.font_size = font_size
    self.tbar_bounds = (0, self.font_size * n_sheets)

    self.hov_sheet = None
    self.sel_sheet = None

  # called each frame to render stuff to the window
  def render(self) -> None:

    # grab globals
    scroll = self.glob.scroll
    zoom = self.glob.cam_zoom
    main_c = self.glob.COLORS['main']
    accent_c = self.glob.COLORS['accent']
    a_comp_c = self.glob.COLORS['a_comp']

    # camera stuff -------------------------------------------------------------
    self.camera.fill(main_c)

    # origin indicator
    line(self.camera, accent_c, (-10 - scroll[0], -scroll[1]), 
                                        (10 - scroll[0], -scroll[1]), 3 * zoom)
    line(self.camera, accent_c, (-scroll[0], -10 - scroll[1]), 
                                        (-scroll[0], 10 - scroll[1]), 3 * zoom)

    # render info
    info = f'''
    {self.glob.window.sel_sheet}
    {self.glob.input.pen_pos}
    {self.glob.scroll}
    '''

    self.glob.font.render_txt(info, self.camera, (0, 0))

    # window stuff -------------------------------------------------------------
    self.window.fill(main_c)
    self.window.fill(accent_c, [0, 0, self.glob.tbar_width, self.height])

    # sheet pos
    my = self.glob.input.mouse_pos[1] + self.tbar_scroll
    offset = 10
    self.hov_sheet = None

    # sheet name stuff
    for i, f in enumerate(self.glob.sheets.sheets):

      y_pos = self.font_size * i + offset
      x_pos = 10

      hover_y = my

      if f == self.sel_sheet:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
      elif 0 <= hover_y - y_pos <= self.font_size:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
        self.hov_sheet = f

      surf = self.glob.font.render_txt(f, self.window, (x_pos, y_pos))

    # divider
    start_p = self.glob.tbar_width * 0.1, self.height * 0.2
    end_p = self.glob.tbar_width * 0.9, self.height * 0.2
    line(self.window, a_comp_c, start_p, end_p, 3)

    # assets
    if self.sel_sheet:
      
      sheet = self.glob.sheets.sheets[self.sel_sheet]
      sheet_coords = self.glob.sheets.sheet_coords[self.sel_sheet]

      res_x = 10
      res_y = 10

      x = res_x
      y = res_y + self.height * 0.21
      for row in sheet_coords:

        height = 0
        for coords in row:
          
          surf = self.glob.sheets.scaled_surf(sheet, coords, 3)
          self.window.blit(surf, (x, y))

          x += surf.get_width() + res_x
          height = max(height, surf.get_height())
        
        y += height + res_y
        x = res_x

    self.window.blit(self.camera, (self.glob.tbar_width, 0))
    pygame.display.update()