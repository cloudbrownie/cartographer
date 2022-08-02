import pygame, sys

from pygame.locals import *

class Inputs:
  def __init__(self, glob):

    self.glob = glob

    self.sel_rect = {

    }

    self.mods = {
      pygame.K_LSHIFT:False,
      pygame.K_LCTRL:False,
    }

  def handle(self):

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()