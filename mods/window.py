import pygame

class Window:
  def __init__(self, glob, width, height):
    self.glob = glob

    pygame.init()
    
    self.window = pygame.display.set_mode((width, height))
    self.width = width
    self.height = height

  def render(self):

    self.window.fill(self.glob.COLORS['main'])
    self.window.fill(self.glob.COLORS['accent'], [0, 0, self.width * 0.2, self.height])


    pygame.display.update()