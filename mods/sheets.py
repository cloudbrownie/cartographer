import pygame, os

class Sheets:
  # init
  def __init__(self):

    # store all sheets in a dict
    self.sheets = {

    }

    # grab all .png files in the input dir
    files = [f for f in os.listdir('input/') if f.endswith('.png')]

    # grab each asset from each sheet and store the coords in a dict
    for f in files:
      sheet_surf = pygame.image.load(f'input/{f}')
      sheet_surf.set_colorkey((0, 0, 0))

      assets = []

      # find each asset
      for i in range(sheet_surf.get_height()):
        if sheet_surf.get_at((0, i)) == (166, 255, 0, 255):
          row = []
          for j in range(sheet_surf.get_width()):
            if sheet_surf.get_at((j, i)) == (255, 41, 250, 255):

              w, h = 0, 0
              for x in range(j + 1, sheet_surf.get_width()):
                if sheet_surf.get_at((x, i)) == (0, 255, 255, 255):
                  w = x - j - 1
                  break

              for y in range(i + 1, sheet_surf.get_height()):
                if sheet_surf.get_at((j, y)) == (0, 255, 255, 255):
                  h = y - i - 1
                  break

              row.append((j + 1, i + 1, w, h))
          assets.append(row)

      
