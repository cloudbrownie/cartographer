import pygame, sys

from pygame.locals import *

from mods.window import Window
from mods.glob import Glob

glob = Glob(1000, 700)

pygame.event.set_blocked(None)
pygame.event.set_allowed([QUIT, KEYDOWN])

while 1:

  glob.inputs.handle()
  glob.window.render()