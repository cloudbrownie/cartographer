import pygame

from pygame.draw import *
from pygame.transform import scale

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
    self.tbar_bounds = (0, self.font_size * n_sheets)

    self.hov_sheet = None
    self.sel_sheet = None
    self.curr_sheet = None
    self.tex_cache = []

    self.hov_tex = None
    self.sel_tex = None
    self.curr_tex_data = None

    self.render_cache = {}

    self.sel_mask = None
    self.sel_mask_coords = 0, 0

  # generates a mask of a set of tiles and stores internally
  def generate_mask(self, tiles : list, t_size : float) -> None:
    tiles = list(self.glob.input.selected_tiles)
    for i in range(len(tiles)):
      tiles[i] = tiles[i][0] * t_size, tiles[i][1] * t_size

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

    self.sel_mask = washed_surf
    self.sel_mask_coords = left, top

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


    self.window.fill(main_c)

    # camera stuff -------------------------------------------------------------
    self.camera.fill(main_c)

    # origin indicator
    ind_len = 20
    ind_w = 3
    line(self.camera, accent_c, (-ind_len - scroll[0], -scroll[1]), 
                                    (ind_len - scroll[0], -scroll[1]), ind_w)
    line(self.camera, accent_c, (-scroll[0], -ind_len - scroll[1]), 
                                    (-scroll[0], ind_len - scroll[1]), ind_w)

    cam_size = self.glob.cam_scale_size

    # draw outline for selected tiles
    if self.glob.input.selected_tiles:
      if not self.sel_mask:
        self.generate_mask(self.glob.input.selected_tiles, t_size)
      
      for nx, ny in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), 
                                                            (-1, 1), (-1, -1)]:
        blit_x = self.sel_mask_coords[0] + nx * 3 - scroll[0]
        blit_y = self.sel_mask_coords[1] + ny * 3 - scroll[1]

        self.camera.blit(self.sel_mask, (blit_x, blit_y))

    # draw all chunks to the camera
    needed_chunks = []
    vis_chunks = chunks.get_chunks(cam_rect)
    for chunk_tag in list(self.render_cache.keys()):
      if chunk_tag not in vis_chunks:
        del self.render_cache[chunk_tag]

    for chunk_tag in vis_chunks:
      if chunk_tag not in self.render_cache:
        needed_chunks.append(chunk_tag)

    for i, chunk_tag in enumerate(chunks.re_render):
      if chunk_tag in vis_chunks:
        needed_chunks.append(chunk_tag)
        chunks.re_render.pop(i)

    for chunk_tag in needed_chunks:
      layers = {}

      for layer in chunks.chunks[chunk_tag]['tiles']:
        
        layer_surf = pygame.Surface((padded_chunk_size, padded_chunk_size))
        layer_surf.set_colorkey((0, 0, 0))

        for tile_data in chunks.chunks[chunk_tag]['tiles'][layer]:

          x, y, sheet_id, sheet_coords = tile_data
          x = x * t_size + pad_offset
          y = y * t_size + pad_offset
          sheet_name = chunks.sheet_refs[sheet_id]
          tile_surf = sheets[sheet_name][sheet_coords[0]][sheet_coords[1]]

          layer_surf.blit(tile_surf, (x, y))
        
        layers[layer] = layer_surf

      self.render_cache[chunk_tag] = layers

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

      tx = px * t_size - scroll[0]
      ty = py * t_size - scroll[1]
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
    {self.glob.clock.fps}
    {self.sel_sheet}
    {px}, {py}
    {scroll[0] : .1f}, {scroll[1] : .1f}
    {zoom}
    {tool}
    {self.glob.input.sel_rect}
    {self.glob.curr_cam_size}
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

    # sheet name stuff
    for i, f in enumerate(self.glob.sheets.sheets):

      y_pos = self.font_size * i + offset
      x_pos = 10

      hover_y = my
      y_dif = hover_y - y_pos

      if f == self.sel_sheet:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
      elif mx <= self.glob.tbar_width and 0 <= y_dif<= self.font_size:
        self.glob.font.render_txt('-', self.window, (x_pos, y_pos))
        x_pos = 20
        self.hov_sheet = f

      surf = self.glob.font.render_txt(f, self.window, (x_pos, y_pos))

    # divider
    start_p = self.glob.tbar_width * 0.1, self.div_height
    end_p = self.glob.tbar_width * 0.9, self.div_height
    line(self.window, a_comp_c, start_p, end_p, 3)

    # assets
    self.hov_tex = None
    if self.sel_sheet:

      res_x = 10
      res_y = 10

      x = res_x
      y = res_y + self.div_height * 1.1
      for i, row in enumerate(self.tex_cache):

        height = 0
        for j, surf in enumerate(row):

          w, h = surf.get_size()

          rect = pygame.Rect(x, y, w, h)

          if rect.collidepoint(mx, my):
            self.hov_tex = i, j

          if self.hov_tex == (i, j):
            x += 10

          self.window.blit(surf, (x, y))

          x += w + res_x
          height = max(height, h)
        
        y += height + res_y
        x = res_x

    pygame.display.update()

  # sets the current sheet info 
  def set_selected_sheet(self, sheet : str) -> None:
    self.sel_sheet = sheet
    self.curr_sheet = self.glob.sheets.sheets[self.sel_sheet]
    self.tex_cache.clear()

    tex_zoom = self.glob.tex_zoom
    
    for row in self.curr_sheet:

      new_row = []

      for surf in row:

        w = surf.get_width() * tex_zoom
        h = surf.get_height() * tex_zoom

        scaled_surf = pygame.Surface((w, h))
        scaled_surf.blit(scale(surf, (w, h)), (0, 0))
        scaled_surf.set_colorkey((0, 0, 0))

        new_row.append(scaled_surf)

      self.tex_cache.append(new_row)

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