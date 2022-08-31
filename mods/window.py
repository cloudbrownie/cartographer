import pygame

from pygame.draw import *
from pygame.transform import scale

# generates a mask of a set of tiles and stores internally
def generate_mask(tiles : list, t_size : float) -> None:
  for i in range(len(tiles)):
    tiles[i] = tiles[i][0] * t_size, tiles[i][1] * t_size

  # find bounds
  left = tiles[0][0]
  top = tiles[0][1]
  right = tiles[0][0]
  bot = tiles[0][1]

  for tile in tiles:
    if tile[0] < left:
      left = tile[0]
    elif tile[0] > right:
      right = tile[0]
    elif tile[1] < top:
      top = tile[1]
    elif tile[1] > bot:
      bot = tile[1]

  w = right - left + t_size
  h = bot - top + t_size

  # make mask
  mask_surf = pygame.Surface((w, h))
  mask_surf.set_colorkey((0, 0, 0))
  for tile_data in tiles:

    x, y = tile_data
    x -= left
    y -= top
    pygame.draw.rect(mask_surf, (255, 255, 255), (x, y, t_size, t_size))

  mask = pygame.mask.from_surface(mask_surf)
  washed_surf = mask.to_surface()
  washed_surf.set_colorkey((0, 0, 0))

  return washed_surf, left, top

class Window:
  # init
  def __init__(self, glob, width, height, font_size):
    self.glob = glob

    pygame.init()
    
    self.window = pygame.display.set_mode((width, height))
    self.width = width
    self.height = height
    self.div_height = height * 0.2

    pygame.display.set_caption('cartographer')

    cw, ch = self.glob.curr_cam_size

    self.camera = pygame.Surface((cw, ch))

    self.camera_rect = pygame.Rect(self.glob.scroll, (cw, ch))

    ocw, och = self.glob.cam_scale_size
    self.camera_ratio = cw / ocw, ch / och

    self.tbar_scroll = 0

    n_sheets = len(self.glob.sheets.sheets)
    self.font_size = font_size
    self.tbar_bounds = self.font_size * n_sheets

    self.hov_sheet = None
    self.sel_sheet = None
    self.curr_sheet = None
    self.curr_sheet_idx = -1

    self.tex_cache = []
    self.tex_scroll = 0
    self.tex_scroll_t = 0
    self.tex_scroll_bound = 0
    self.TEX_SCROLL_TOL = 0.01

    self.hov_tex = None
    self.sel_tex = None
    self.curr_tex_data = None

    self.render_cache = {}

    self.sel_mask = None
    self.sel_mask_coords = 0, 0

  # called each frame to render stuff to the window
  def render(self) -> None:

    # grab globals
    scroll = self.glob.scroll
    zoom = self.glob.cam_zoom
    main_c = self.glob.COLORS['main']
    accent_c = self.glob.COLORS['accent']
    a_comp_c = self.glob.COLORS['a_comp']
    px, py = self.glob.input.pen_pos
    tool = self.glob.input.tool
    cam_rect = *scroll, *self.glob.curr_cam_size

    chunks = self.glob.chunks
    chunk_size = self.glob.chunks.CHUNK_SIZE * self.glob.chunks.TILE_SIZE
    padded_chunk_size = self.glob.chunks.CHUNK_PX
    pad_offset = self.glob.chunks.SURF_PADDING
    t_size = self.glob.chunks.TILE_SIZE

    sheets = self.glob.sheets.sheets
    sheet_config = self.glob.sheets.sheet_configs

    cam_size = self.glob.cam_scale_size

    self.window.fill(main_c)

    # camera stuff -------------------------------------------------------------
    self.camera.fill(main_c)

    # origin indicator
    ind_len = 20
    ind_w = 3
    line(self.camera, accent_c, (-ind_len - scroll[0], -scroll[1]), \
      (ind_len - scroll[0], -scroll[1]), ind_w)
    line(self.camera, accent_c, (-scroll[0], -ind_len - scroll[1]), \
      (-scroll[0], ind_len - scroll[1]), ind_w)

    # draw outline for selected tiles
    if self.glob.input.selected_tiles:
      if not self.sel_mask:
        # generate a mask for the selected tiles
        surf, x, y = generate_mask(list(self.glob.input.selected_tiles), t_size)
        self.sel_mask = surf
        self.sel_mask_coords = x, y

      # blit with offsets in 8 directions      
      for nx, ny in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), 
                                                            (-1, 1), (-1, -1)]:
        blit_x = self.sel_mask_coords[0] + nx * 3 - scroll[0]
        blit_y = self.sel_mask_coords[1] + ny * 3 - scroll[1]
        self.camera.blit(self.sel_mask, (blit_x, blit_y))
    elif not self.glob.input.selected_tiles and self.sel_mask:
      self.sel_mask = None

    # draw all chunks to the camera
    needed_chunks = []
    vis_chunks = chunks.get_chunks(cam_rect)

    # remove non visible chunks from list of chunks to be rendered
    for chunk_tag in list(self.render_cache.keys()):
      if chunk_tag not in vis_chunks:
        del self.render_cache[chunk_tag]

    # add visible but not cached chunks
    for chunk_tag in vis_chunks:
      if chunk_tag not in self.render_cache:
        needed_chunks.append(chunk_tag)

    # add chunks needed to be rerendered
    for chunk_tag in list(chunks.re_render):
      if chunk_tag in vis_chunks:
        needed_chunks.append(chunk_tag)
        chunks.re_render.remove(chunk_tag)

    # cache chunks
    for chunk_tag in needed_chunks:
      layers = {}

      for layer in chunks.chunks[chunk_tag]['tiles']:
        
        layer_surf = pygame.Surface((padded_chunk_size, padded_chunk_size))
        layer_surf.set_colorkey((0, 0, 0))

        for tile_data in chunks.chunks[chunk_tag]['tiles'][layer]:

          x, y, sheet_id, row, col = tile_data
          sheet_name = chunks.sheet_refs[sheet_id]
          x = x * t_size + pad_offset
          y = y * t_size + pad_offset
          if sheet_name in sheet_config:
            off_x, off_y = sheet_config[sheet_name][row][col]
            x += off_x
            y += off_y
          tile_surf = sheets[sheet_name][row][col]

          layer_surf.blit(tile_surf, (x, y))
        
        layers[layer] = layer_surf

      self.render_cache[chunk_tag] = layers

    # render cached chunks
    for chunk in vis_chunks:

      chunk_x, chunk_y = chunks.deformat_chunk_tag(chunk)
      x = chunk_x * chunk_size - scroll[0] - pad_offset
      y = chunk_y * chunk_size - scroll[1] - pad_offset

      for layer in self.render_cache[chunk]:

        surf = self.render_cache[chunk][layer]
        self.camera.blit(surf, (x, y))

    # draw tile highlight at current pen position
    if self.sel_tex and self.glob.input.tool == 'draw':
      hover_surf = self.sel_tex.copy()
      hover_surf.set_alpha(120)
      t_size = self.glob.chunks.TILE_SIZE
      row, col = self.curr_tex_data

      tx = px * t_size - scroll[0]
      ty = py * t_size - scroll[1]
      if self.sel_sheet in sheet_config:
        off_x, off_y = sheet_config[self.sel_sheet][row][col]
        tx -= off_x
        ty -= off_y
      self.camera.blit(hover_surf, (tx, ty))

    # draw the selection rect
    if self.glob.input.sel_rect:
      rect = list(self.glob.input.selection_rect)
      rect[0] -= scroll[0]
      rect[1] -= scroll[1]
      pygame.draw.rect(self.camera, accent_c, rect, 3)

    self.window.blit(scale(self.camera, cam_size), (self.glob.tbar_width, 0))

    # window stuff -------------------------------------------------------------
    self.window.fill(accent_c, [0, 0, self.glob.tbar_width, self.height])

    # render info
    info = f'''
    fps : {self.glob.clock.avgFPS}
    current sheet : {self.sel_sheet if self.sel_sheet else ''}
    pen position : {px}, {py}
    tool : {tool}
    auto-tile : {'on' if self.glob.input.auto_tiling else 'off'}
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

    # render textures
    self.hov_tex = None
    if self.sel_sheet:

      res_x = 10
      res_y = 10

      x = res_x
      y = res_y + self.div_height * 1.1 - self.tex_scroll
      for i, row in enumerate(self.tex_cache):

        height = 0
        for j, surf in enumerate(row):

          w, h = surf.get_size()

          rect = pygame.Rect(x, y, w, h)

          # check if cursor is hovering
          if rect.collidepoint(mx, my) and my > self.div_height:
            self.hov_tex = i, j

          if self.hov_tex == (i, j):
            x += 10

          self.window.blit(surf, (x, y))

          x += w + res_x
          height = max(height, h)
        
        y += height + res_y
        x = res_x

    self.window.fill(accent_c, (0, 0, self.glob.tbar_width, self.div_height))

    # sheet name stuff
    for i, f in enumerate(self.glob.sheets.sheets):

      y_pos = self.font_size * i + offset
      x_pos = 10

      hover_y = my
      y_dif = hover_y - y_pos

      # render sheet names with dashes if needed 
      if f == self.sel_sheet:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
      elif mx <= self.glob.tbar_width and 0 <= y_dif<= self.font_size:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
        self.hov_sheet = f

      self.glob.font.render_txt(f, self.window, (x_pos, y_pos))

    # divider
    start_p = self.glob.tbar_width * 0.1, self.div_height
    end_p = self.glob.tbar_width * 0.9, self.div_height
    line(self.window, a_comp_c, start_p, end_p, 3)

    pygame.display.update()

  # sets the current sheet info 
  def set_selected_sheet(self, sheet : str) -> None:
    self.sel_sheet = sheet
    self.curr_sheet = self.glob.sheets.sheets[self.sel_sheet]
    self.curr_sheet_idx = list(self.glob.sheets.sheets.keys()).index(sheet)
    self.tex_cache.clear()

    tex_zoom = self.glob.tex_zoom
    tot_h = 0

    for row in self.curr_sheet:

      new_row = []

      max_h = 0

      for surf in row:

        w = surf.get_width() * tex_zoom
        h = surf.get_height() * tex_zoom

        scaled_surf = pygame.Surface((w, h))
        scaled_surf.blit(scale(surf, (w, h)), (0, 0))
        scaled_surf.set_colorkey((0, 0, 0))

        new_row.append(scaled_surf)

        if h > max_h:
          max_h = h

      self.tex_cache.append(new_row)
      tot_h += max_h + 10

    self.tex_scroll_bound = tot_h - (self.height - self.div_height * 1.1 - 10)

  # sets the current texture info
  def set_selected_texture(self, data : tuple) -> None:
    self.curr_tex_data = data
    i, j = data

    sheet = self.glob.sheets.sheets[self.sel_sheet]
    self.sel_tex = sheet[i][j]

  # update the camera size
  def update_camera_size(self) -> None:
    
    zoom = self.glob.cam_zoom

    base_w, base_h = self.glob.base_cam_size
    new_w = base_w * zoom
    new_h = base_h * zoom

    self.glob.curr_cam_size = new_w, new_h

    center = self.camera_rect.center
    prev_x, prev_y = self.camera_rect.topleft

    self.camera_rect.width = new_w
    self.camera_rect.height = new_h
    self.camera_rect.center = center

    self.camera = pygame.Surface(self.camera_rect.size)

    self.glob.curr_cam_size = new_w, new_h

    curr_x, curr_y = self.camera_rect.topleft

    x_scroll_dif = curr_x - prev_x
    y_scroll_dif = curr_y - prev_y

    self.glob.scroll[0] += x_scroll_dif
    self.glob.scroll[1] += y_scroll_dif
    self.glob.scroll_t[0] += x_scroll_dif
    self.glob.scroll_t[1] += y_scroll_dif

  # cycle through the sheets
  def cycle_sheets(self, value : int) -> None:
    self.curr_sheet_idx += value
    self.curr_sheet_idx %= len(self.glob.sheets.sheets)

    new_sheet = list(self.glob.sheets.sheets.keys())[self.curr_sheet_idx]
    self.set_selected_sheet(new_sheet)

  # add value to texture scroll
  def add_texture_scroll(self, value : float) -> None:
    self.tex_scroll_t -= value * 30

    if self.tex_scroll_t < 0:
      self.tex_scroll_t = 0

    elif self.tex_scroll_t > self.tex_scroll_bound:
      self.tex_scroll_t = self.tex_scroll_bound

  # update the texture scroll
  def update_texture_scroll(self) -> None:

    ds = self.tex_scroll_t - self.tex_scroll
    ds *= self.glob.clock.dt

    self.tex_scroll += ds
    if abs(self.tex_scroll - self.tex_scroll_t) <= self.TEX_SCROLL_TOL:
      self.tex_scroll = self.tex_scroll_t
