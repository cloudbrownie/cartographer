import pygame

from pygame.draw import *

class Window:
  # init
  def __init__(self, glob, width, height):
    self.glob = glob

    pygame.init()
    
    self.window = pygame.display.set_mode((width, height))
    self.width = width
    self.height = height

    self.camera = pygame.Surface((width * 0.8, height))

  # called each frame to render stuff to the window
  def render(self) -> None:

    # grab globals
    scroll = self.glob.scroll
    zoom = self.glob.cam_zoom
    main_c = self.glob.COLORS['main']
    accent_c = self.glob.COLORS['accent']

    # camera stuff -------------------------------------------------------------
    self.camera.fill(main_c)

    # origin indicator
    line(self.camera, accent_c, (-10 - scroll[0], -scroll[1]), 
                                        (10 - scroll[0], -scroll[1]), 3 * zoom)
    line(self.camera, accent_c, (-scroll[0], -10 - scroll[1]), 
                                        (-scroll[0], 10 - scroll[1]), 3 * zoom)

    # render info
    info = f'''
    {self.glob.input.pen_pos}
    {self.glob.scroll}
    '''

    self.glob.font.render_txt(info, self.camera, (0, 0))

    # window stuff -------------------------------------------------------------
    self.window.fill(main_c)
    self.window.fill(accent_c, [0, 0, self.glob.tbar_width, self.height])

    self.glob.font.render_txt('test', self.window, (10, 10))

    self.window.blit(self.camera, (self.glob.tbar_width, 0))
    pygame.display.update()