import pygame

# compare method for kdtrees
def compare(p1: tuple, p2: tuple, vert: bool) -> float:
  if vert:
    return p1[0] - p2[0]
  return p1[1] - p2[1]

# returns squared distance between two points
def sq_dist(p1: tuple, p2: tuple) -> float:
  return ((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2)

# returns a modified version of input rect vased on p, cmp, and vert
def resize_rect(r: pygame.Rect, p: tuple, cmp: float,
                vert: bool) -> pygame.Rect:
  x, y = p
  if vert and cmp < 0:
    r = pygame.Rect(r.x, r.y, x - r.x, r.h)
  elif vert and cmp >= 0:
    r = pygame.Rect(x, r.y, r.right - x, r.h)
  elif not vert and cmp < 0:
    r = pygame.Rect(r.x, r.y, r.w, y - r.y)
  else:
    r = pygame.Rect(r.x, y, r.w, r.bottom - y)
  r.normalize()
  return r

# method for finding distance from rect to a point
def rect_sq_dist(r: pygame.Rect, p: tuple) -> float:
  x, y = p
  rect_x = x
  rect_y = y
  if x < r.left:
    rect_x = r.left
  elif x > r.right:
    rect_x = r.right
  if y < r.top:
    rect_y = r.top
  elif y > r.bottom:
    rect_y = r.bottom

  return ((x - rect_x) ** 2) + ((y - rect_y) ** 2)

class KDTree:
  class _Node:
    def __init__(self, pos: tuple, data: type):
      self.pos = pos
      self.data = data
      self.left = None
      self.right = None

  def __init__(self, item_size: int):
    self.root = None
    self.n = 0
    self._item_size = item_size
    self._test_rect = pygame.Rect(0, 0, item_size, item_size)

  def clear(self) -> None:
    self.__init__()

  # inserts node into kdtree
  def put(self, pos: tuple, data: type) -> None:
    self.root = self._put(self.root, pos, data, True)

  # recursive helper method for self.put
  def _put(self, x: _Node, pos: tuple, data: type, vert: bool) -> _Node:
    if not x:
      self.n += 1
      return self._Node(pos, data)

    c = compare(pos, x.pos, vert)
    if c < 0:
      x.left = self._put(x.left, pos, data, not vert)
    else:
      x.right = self._put(x.right, pos, data, not vert)
    return x

  # gets a node from the tree given a pos, returns none for invalid pos
  def get(self, pos: tuple) -> None:
    return self._get(self.root, pos, True)

  # recursive helper method for self.get
  def _get(self, x: _Node, pos: tuple, vert: bool) -> _Node:
    if not x:
      return None
    if x.pos == pos:
      return x

    c = compare(pos, x.pos, vert)
    if c < 0:
      return self._get(x.left, pos, not vert)
    else:
      return self._get(x.right, pos, not vert)

  # returns nearest node to a given position
  def find_nearest(self, pos: tuple, curr_rect: pygame.Rect) -> type:
    if self.n == 0:
      return None
    x = self._find_nearest(self.root, pos, self.root, curr_rect, True)
    return x.pos

  # recursive helper method for self.find_nearest
  def _find_nearest(self, x: _Node, pos: tuple, champ: _Node,
                    curr_rect: pygame.Rect, vert: bool) -> _Node:
    # x is empty node
    if not x:
      return champ

    # prune this branch if its rect is further than the closest found point
    if sq_dist(pos, champ.pos) < rect_sq_dist(curr_rect, pos):
      return champ

    # update champ if x is closer
    if sq_dist(pos, x.pos) < sq_dist(pos, champ.pos):
      champ = x

    # decide which direction to go to check first
    if (vert and pos[0] < x.pos[0]) or (not vert and pos[1] < x.pos[1]):
      # left first
      curr_rect = resize_rect(curr_rect, x.pos, -1, vert)
      best_left = self._find_nearest(x.left, pos, champ, curr_rect, not vert)
      if sq_dist(pos, best_left.pos) < sq_dist(pos, champ.pos):
        champ = best_left
      curr_rect = resize_rect(curr_rect, x.pos, 1, vert)
      best_right = self._find_nearest(x.right, pos, champ, curr_rect, not vert)
      if sq_dist(pos, best_right.pos) < sq_dist(pos, champ.pos):
        champ = best_right
    else:
      # right first
      curr_rect = resize_rect(curr_rect, x.pos, 1, vert)
      best_right = self._find_nearest(x.right, pos, champ, curr_rect, not vert)
      if sq_dist(pos, best_right.pos) < sq_dist(pos, champ.pos):
        champ = best_right
      curr_rect = resize_rect(curr_rect, x.pos, -1, vert)
      best_left = self._find_nearest(x.left, pos, champ, curr_rect, not vert)
      if sq_dist(pos, best_left.pos) < sq_dist(pos, champ.pos):
        champ = best_left

    return champ

  def range(self, query: pygame.Rect) -> list:
    found = []
    self._range(self.root, query, query, found, True)
    return found

  def _range(self, x: _Node, query: pygame.Rect, curr_rect: pygame.Rect,
             found: list, vert: bool) -> None:
    if not x:
      return
    if not query.colliderect(curr_rect):
      return
    self._test_rect.center = x.pos
    if query.colliderect(self._test_rect):
      found.append(x.data)
    self._range(x.left, query, resize_rect(curr_rect, x.pos, -1, vert),
                found, not vert)
    self._range(x.right, query, resize_rect(curr_rect, x.pos, 1, vert),
                found, not vert)

  # returns the kdtree as a dictionary
  def convert_to_dict(self) -> dict:
    if not self.root:
      return {}

    kd_dict = {
      'pos': self.root.pos,
      'data': self.root.data,
      'left': self._convert_to_dict(self.root.left),
      'right': self._convert_to_dict(self.root.right)
    }

    return kd_dict

  def _convert_to_dict(self, x: _Node) -> dict:
    if not x:
      return None

    return {
      'pos': x.pos,
      'data': x.data,
      'left': self._convert_to_dict(x.left),
      'right': self._convert_to_dict(x.right)
    }