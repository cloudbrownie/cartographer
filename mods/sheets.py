import pygame, os
import json

from pygame import Surface

TRANSPARENT_COLOR = 0, 0, 0

class Sheets:
  # init
  def __init__(self):

    # store all sheets in a dict
    self.sheets = {

    }

    self.sheet_configs = {

    }

    # grab all .png files in the input dir
    sheet_files = [f[:-4] for f in os.listdir('input/') if f.endswith('.png')]
    config_files = [f[:-5] for f in os.listdir('input/') if f.endswith('.json')]

    # grab each texture from each sheet and store the coords in a dict
    for f in sheet_files:
      sheet_surf = pygame.image.load(f'input/{f}.png')
      sheet_surf.set_colorkey(TRANSPARENT_COLOR)
      textures = []

      # find each asset
      for i in range(sheet_surf.get_height()):
        if sheet_surf.get_at((0, i)) == (255, 41, 250, 255):
          row = []
          for j in range(sheet_surf.get_width()):
            if sheet_surf.get_at((j, i)) == (255, 41, 250, 255):

              w, h = 0, 0
              for x in range(j + 1, sheet_surf.get_width()):
                if sheet_surf.get_at((x, i)) == (0, 255, 255, 255):
                  w = x - j - 1
                  break

              for y in range(i + 1, sheet_surf.get_height()):
                if sheet_surf.get_at((x, y)) == (0, 255, 255, 255):
                  h = y - i - 1
                  break

              surf = Surface((w, h))
              surf.set_colorkey(TRANSPARENT_COLOR)
              surf.blit(sheet_surf, (0, 0), (j + 1, i + 1, w, h))
              row.append(surf)
          textures.append(row)

        self.sheets[f] = textures

      # try to find configuration files
      if f in config_files:
        with open(f'input/{f}.json') as file_data:
          self.sheet_configs[f] = json.load(file_data)

  # returns a lsit of all stored sheets
  @property
  def sheet_names(self) -> list[str]:
    return [sheet for sheet in self.sheets]

  # returns surface given a sheet name with a row and col value
  def get_asset(self, sheet, row, col) -> Surface:
    return self.sheets[sheet][row][col]

  def get_config_info(self, sheet, row, col) -> tuple:
    if sheet in self.sheet_configs:
      return self.sheet_configs[sheet][row][col]
    return 0, 0