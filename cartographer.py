import pygame, sys

from pygame.locals import *

from mods.window import Window
from mods.glob import Glob

glob = Glob(1000, 700)

while 1:

  glob.inputs.handle()
  glob.window.render()