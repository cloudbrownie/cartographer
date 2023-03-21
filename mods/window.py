import pygame

from pygame.draw import *
from pygame.transform import scale


class Window:
  # init
  def __init__(self, glob : object, width : int, height : int, font_size : int):
    self.glob = glob

    pygame.init()

    pygame.mouse.set_visible(False)

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

    self.cached_selection_outline = None
    self.cached_selection_pos = None
    self.hov_tex = None
    self.sel_tex = None
    self.curr_tex_data = None

    self.render_cache = {}

    self.view_modes = ['all', 'focus', 'single']
    self.view_mode_i = 0

    self.show_grid = False

  # generates a selection mask for outlining the selected tiles then caches it
  def generate_mask(self) -> pygame.Surface:
    tiles = self.glob.input.selected_tiles
    tile_size = self.glob.TILE_SIZE
    left = min(tiles, key=lambda x: x[0][0])[0][0]
    top = min(tiles, key=lambda x: x[0][1])[0][1]
    right = max(tiles, key=lambda x: x[0][0])[0][0]
    bottom = max(tiles, key=lambda x: x[0][1])[0][1]

    w = right - left
    h = bottom - top

    cached_surf = pygame.Surface((w + tile_size * 3, h + tile_size * 3))
    cached_surf.set_colorkey((0, 0, 0))

    for (x, y), asset_data in tiles:
        surf = self.glob.sheets.get_asset(*asset_data).copy()
        mask = pygame.mask.from_surface(surf)
        offx, offy = self.glob.sheets.get_config_info(*asset_data)

        mask_surf = mask.to_surface()
        mask_surf.set_colorkey((0, 0, 0))

        for bx, by in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
          cached_surf.blit(mask_surf, (x - left + tile_size + offx + bx,
                                       y - top + tile_size + offy + by))

    self.cached_selection_outline = cached_surf
    self.cached_selection_pos = left - tile_size, top - tile_size


  # called each frame to render stuff to the window
  def render(self) -> None:

    # grab globals
    scroll = self.glob.scroll
    zoom = self.glob.cam_zoom
    main_c = self.glob.COLORS['main']
    m_comp_c = self.glob.COLORS['m_comp']
    accent_c = self.glob.COLORS['accent']
    a_comp_c = self.glob.COLORS['a_comp']
    muted_comp = tuple(max(a_comp_c[i] / ((i + 1) * 2), 0) for i in range(3))
    px, py = self.glob.input.pen_pos
    tool = self.glob.input.tool

    cam_size = self.glob.cam_scale_size

    self.window.fill(main_c)

    # camera stuff -------------------------------------------------------------
    self.camera.fill(main_c)

    # show the grid
    if self.show_grid:

      chunk_size = self.glob.CHUNK_SIZE
      tile_size = self.glob.TILE_SIZE
      h_chunk_lines = self.camera_rect.w // chunk_size
      v_chunk_lines = self.camera_rect.h // chunk_size
      camera_x, camera_y = self.camera_rect.topleft

      # tile grid
      h_tile_lines = self.camera_rect.w // tile_size
      v_tile_lines = self.camera_rect.h // tile_size

      x_start = camera_x // tile_size * tile_size
      for i in range(-1, h_tile_lines):
        start = x_start - scroll[0], camera_y - scroll[1]
        end = x_start - scroll[0], camera_y + self.camera_rect.h - scroll[1]
        line(self.camera, muted_comp, start, end, max(int(zoom), 1))
        x_start += tile_size

      y_start = camera_y // tile_size * tile_size
      for i in range(-1, v_tile_lines + 1):
        start = camera_x - scroll[0], y_start - scroll[1]
        end = camera_x + self.camera_rect.w - scroll[0], y_start - scroll[1]
        line(self.camera, muted_comp, start, end, max(int(zoom), 1))
        y_start += tile_size

      # chunk grid
      x_start = camera_x // chunk_size * chunk_size
      for i in range(-1, h_chunk_lines):
        start = x_start - scroll[0], camera_y - scroll[1]
        end = x_start - scroll[0], camera_y + self.camera_rect.h - scroll[1]
        line(self.camera, m_comp_c, start, end, max(int(zoom), 1))
        x_start += chunk_size

      y_start = camera_y // chunk_size * chunk_size
      for i in range(-1, v_chunk_lines + 1):
        start = camera_x - scroll[0], y_start - scroll[1]
        end = camera_x + self.camera_rect.w - scroll[0], y_start - scroll[1]
        line(self.camera, m_comp_c, start, end, max(int(zoom), 1))
        y_start += chunk_size

    # origin indicator
    ind_len = 7
    line(self.camera, accent_c, (-ind_len - scroll[0], - scroll[1]), \
      (ind_len - scroll[0], -scroll[1]), 1)
    line(self.camera, accent_c, (-scroll[0], -ind_len - scroll[1]), \
      (-scroll[0], ind_len - scroll[1]), 1)

    # draw outline for selected tiles
    if self.glob.input.selected_tiles:

      if not self.cached_selection_outline:
        self.generate_mask()

      x, y = self.cached_selection_pos
      self.camera.blit(self.cached_selection_outline, (x - scroll[0],
                                                       y - scroll[1]))

    # new rendering system for tiles
    layers = self.glob.tilemap.get_visible(self.camera_rect.topleft,
                                          self.camera_rect.size)
    for i, layer_data in enumerate(layers):
      if self.view_mode_i == 2 and i != self.glob.input._layer:
       continue

      layer_cache = {}

      for (x, y), asset_data in layer_data:
        offx, offy = self.glob.sheets.get_config_info(*asset_data)

        x -= scroll[0] - offx
        y -= scroll[1] - offy
        asset_hash = hash(asset_data)
        if asset_hash not in layer_cache:
          asset = self.glob.sheets.get_asset(*asset_data).copy()
          if self.view_mode_i == 1 and i != self.glob.input._layer:
            asset.set_alpha(40)
          layer_cache[asset_hash] = asset

        self.camera.blit(layer_cache[asset_hash], (x, y))

    # draw tile highlight at current pen position
    if self.sel_tex and self.glob.input.tool == 'draw':
      hover_surf = self.sel_tex.copy()
      hover_surf.set_alpha(120)
      t_size = self.glob.TILE_SIZE
      row, col = self.curr_tex_data
      if self.glob.input.entity_type == 'tiles':
        tx = px * t_size - scroll[0]
        ty = py * t_size - scroll[1]
        offsets = self.glob.sheets.get_config_info(self.sel_sheet, row, col)
        tx += offsets[0]
        ty += offsets[1]
        self.camera.blit(hover_surf, (tx, ty))
      elif self.glob.input.entity_type == 'decor':
        w, h = hover_surf.get_size()
        bx = px - w / 2 - scroll[0]
        by = py - h / 2 - scroll[1]
        self.camera.blit(hover_surf, (bx, by))

    # draw the selection rect
    if self.glob.input.last_pos and self.glob.input.tool == 'select':
      drawn_rect = self.glob.input.generate_rect(self.glob.input.canvas_pos,
                                                  self.glob.input.entity_type
                                                  == 'tiles')
      drawn_rect.x -= scroll[0]
      drawn_rect.y -= scroll[1]
      pygame.draw.rect(self.camera, accent_c, drawn_rect, 3)
    elif self.glob.input.selection:
      drawn_rect = pygame.Rect(self.glob.input.selection)
      drawn_rect.x -= scroll[0]
      drawn_rect.y -= scroll[1]
      pygame.draw.rect(self.camera, accent_c, drawn_rect, 3)

    self.window.blit(scale(self.camera, cam_size), (self.glob.tbar_width, 0))

    # window stuff -------------------------------------------------------------
    self.window.fill(accent_c, [0, 0, self.glob.tbar_width, self.height])

    # render info
    info = f'''
    fps : {self.glob.clock.fps_info}
    current sheet : {self.sel_sheet if self.sel_sheet else ''}
    pen position : {px}, {py}
    tool : {tool}
    entity type : {self.glob.input.entity_type}
    layer : {self.glob.input.layer}
    auto-tile : {'on' if self.glob.input.auto_tiling else 'off'}
    view mode : {self.view_modes[self.view_mode_i]}
    scroll : {self.glob.scroll}
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

    pygame.draw.rect(self.window, (255, 255, 255), self.glob.input.cursor)

    # draws the cursor
    cursor_ctr = self.glob.input.cursor.center
    border_rect = pygame.Rect(0, 0, 25, 25)
    border_rect.center = cursor_ctr
    #pygame.draw.rect(self.window, (255, 255, 255), border_rect, 2)

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

  # cycle through view modes
  def cycle_view_mode(self, value : int) -> None:
    self.view_mode_i = (self.view_mode_i + value) % len(self.view_modes)