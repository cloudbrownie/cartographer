import pygame, os

from pygame import Surface

TRANSPARENT_COLOR = 0, 0, 0

class Sheets:
  # init
  def __init__(self):

    # store all sheets in a dict
    self.sheets = {

    }

    self.sheet_coords = {

    }

    self.sheet_configs = {
      
    }

    # grab all .png files in the input dir
    files = [f for f in os.listdir('input/') if f.endswith('.png')]

    # grab each texture from each sheet and store the coords in a dict
    for f in files:
      sheet_surf = pygame.image.load(f'input/{f}')
      sheet_surf.set_colorkey(TRANSPARENT_COLOR)

      self.sheets[f] = {
        '1' : sheet_surf
      }

      textures = []

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
          textures.append(row)
        
        self.sheet_coords[f] = textures

  # returns a lsit of all stored sheets
  @property
  def sheet_names(self) -> list[str]:
    return [sheet for sheet in self.sheets]

  # generates a scaled version of the sheet to save time scaling
  def generate_scaled_sheet(self, sheet : str, scale : float) -> None:
    surf = self.sheets[sheet]['1']
    w, h = surf.get_size()
    n_size = w * scale, h * scale

    scale_key = str(scale)
    scaled_surf = Surface(n_size)
    scaled_surf.blit(pygame.transform.scale(surf, n_size), (0, 0))
    scaled_surf.set_colorkey(TRANSPARENT_COLOR)

    self.sheets[sheet][scale_key] = scaled_surf

  def get_surf(self, sheet : str, coords : tuple, scale : float = 1) -> Surface:
    scale_key = str(scale)

    # add scaled surf to sheet dict    
    if scale_key not in self.sheets[sheet]:

      w, h = self.sheets[sheet]['1'].get_size()
      surf = Surface((w* scale, h * scale))

      self.sheets[sheet][scale_key] = surf

    # scale coords
    coords = list(coords)
    for i in range(len(coords)):
      coords[i] *= scale

    return self.sheets[sheet][scale_key].subsurface(coords)
