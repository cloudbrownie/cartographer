import pygame


class Window:
  def __init__(self, glob, width, height):
    self.glob = glob

    pygame.init()
    
    self.window = pygame.display.set_mode((width, height))
    self.width = width
    self.height = height

    self.camera = pygame.Surface((width * 0.8, height))

  def render(self) -> None:

    # camera stuff -------------
    self.camera.fill(self.glob.COLORS['main'])
    pygame.draw.line(self.camera, self.glob.COLORS['accent'], (-10 - self.glob.scroll[0], -self.glob.scroll[1]), (10 - self.glob.scroll[0], -self.glob.scroll[1]), 3 * self.glob.cam_zoom)
    pygame.draw.line(self.camera, self.glob.COLORS['accent'], (-self.glob.scroll[0], -10 - self.glob.scroll[1]), (-self.glob.scroll[0], 10 - self.glob.scroll[1]), 3 * self.glob.cam_zoom)

    self.glob.font.render_txt(str(self.glob.inputs.pen_pos), self.camera, (10, 10))
    self.glob.font.render_txt(str(self.glob.scroll), self.camera, (10, 30))

    # window stuff -------------
    self.window.fill(self.glob.COLORS['main'])
    self.window.fill(self.glob.COLORS['accent'], [0, 0, self.glob.toolbar_width, self.height])

    self.glob.font.render_txt('test', self.window, (10, 10))

    self.window.blit(self.camera, (self.glob.toolbar_width, 0))
    pygame.display.update()