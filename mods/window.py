from django.shortcuts import render
import pygame

from pygame.draw import *
from pygame.transform import scale

class Window:
  # init
  def __init__(self, glob, width, height, font_size):
    self.glob = glob

    pygame.init()
    
    self.window = pygame.display.set_mode((width, height))
    self.width = width
    self.height = height
    self.div_height = height * 0.2

    self.camera = pygame.Surface(self.glob.cam_size)

    self.tbar_scroll = 0

    n_sheets = len(self.glob.sheets.sheets)
    self.font_size = font_size
    self.tbar_bounds = (0, self.font_size * n_sheets)

    self.hov_sheet = None
    self.sel_sheet = None

    self.hov_tex = None
    self.sel_tex = None

  # called each frame to render stuff to the window
  def render(self) -> None:

    # grab globals
    scroll = self.glob.scroll
    zoom = self.glob.cam_zoom
    main_c = self.glob.COLORS['main']
    accent_c = self.glob.COLORS['accent']
    a_comp_c = self.glob.COLORS['a_comp']
    self.window.fill(main_c)

    # camera stuff -------------------------------------------------------------
    self.camera.fill(main_c)

    # origin indicator
    ind_len = 10 * zoom
    line(self.camera, accent_c, (-ind_len - scroll[0], -scroll[1]), 
                                    (ind_len - scroll[0], -scroll[1]), 3 * zoom)
    line(self.camera, accent_c, (-scroll[0], -ind_len - scroll[1]), 
                                    (-scroll[0], ind_len - scroll[1]), 3 * zoom)

    cam_size = self.glob.orig_cam_size
    self.window.blit(scale(self.camera, cam_size), (self.glob.tbar_width, 0))

    # window stuff -------------------------------------------------------------
    self.window.fill(accent_c, [0, 0, self.glob.tbar_width, self.height])

    px, py = self.glob.input.pen_pos

    # render info
    info = f'''
    {self.glob.window.sel_sheet}
    {px}, {py}
    {scroll[0] : .1f}, {scroll[1] : .1f}
    '''

    info_loc = self.glob.tbar_width, 0
    info_surf = self.glob.font.render_txt(info, self.window, info_loc)

    # render the selected texture
    if self.sel_tex:
      height = info_surf.get_height()

      self.window.blit(self.sel_tex, (self.glob.tbar_width + 10, height))

    # sheet pos
    mx, my = self.glob.input.mouse_pos
    my += self.tbar_scroll
    offset = 10
    self.hov_sheet = None

    # sheet name stuff
    for i, f in enumerate(self.glob.sheets.sheets):

      y_pos = self.font_size * i + offset
      x_pos = 10

      hover_y = my
      y_dif = hover_y - y_pos

      if f == self.sel_sheet:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
      elif mx <= self.glob.tbar_width and 0 <= y_dif<= self.font_size:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
        self.hov_sheet = f

      surf = self.glob.font.render_txt(f, self.window, (x_pos, y_pos))

    # divider
    start_p = self.glob.tbar_width * 0.1, self.div_height
    end_p = self.glob.tbar_width * 0.9, self.div_height
    line(self.window, a_comp_c, start_p, end_p, 3)

    # assets
    self.hov_tex = None
    if self.sel_sheet:
      
      tex_zoom = self.glob.tex_zoom
      sheet_coords = self.glob.sheets.sheet_coords[self.sel_sheet]

      res_x = 10
      res_y = 10

      x = res_x
      y = res_y + self.div_height * 1.1
      for row in sheet_coords:

        height = 0
        for coords in row:

          surf = self.glob.sheets.get_surf(self.sel_sheet, coords, tex_zoom)
          rect = pygame.Rect(x, y, surf.get_width(), surf.get_height())

          if rect.collidepoint(mx, my):
            self.hov_tex = surf

          if self.hov_tex == surf:
            x += 10

          self.window.blit(surf, (x, y))

          x += surf.get_width() + res_x
          height = max(height, surf.get_height())
        
        y += height + res_y
        x = res_x

    pygame.display.update()