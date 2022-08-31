import time

class Clock:
  # init
  def __init__(self):
    self.last_time = 0
    self.dt = 0
    self.fps_pace = 60
    self.avg_frames = []
    self.lowest = float('inf')
    self.refresh_lowest = 3
    self.last_refresh = 0

  # called each frame to update the delta time value and average frame value
  def tick(self) -> None:
    self.dt = (time.time() - self.last_time) * 60
    self.last_time = time.time()
    self.avg_frames.append(self.fps)
    if len(self.avg_frames) > self.fps_pace:
      self.avg_frames.pop(0)

    if time.time() - self.last_refresh >= self.refresh_lowest:
      self.lowest = float('inf')
      self.last_refresh = time.time()

    if self.fps < self.lowest:
      self.lowest = self.fps

  # returns the average fps value
  @property
  def avgFPS(self) -> float:
    if self.avg_frames == []:
      return 0    
    return int(sum(self.avg_frames) / len(self.avg_frames))

  # returns the fps calculated from this frame
  @property
  def fps(self) -> float:
    if self.dt != 0:
      return int(1 / (self.dt / self.fps_pace))
    return 0

  # returns an informative string about fps
  @property
  def fps_info(self) -> str:
    return f'{self.avgFPS}/{self.lowest}'