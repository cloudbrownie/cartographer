import time

class Clock:
    def __init__(self):
        self.lastTime = 0
        self.dt = 0
        self.fpsPace = 60
        self.averageFrames = []

    def tick(self) -> None:
        self.dt = (time.time() - self.lastTime) * 60
        self.lastTime = time.time()
        self.averageFrames.append(self.fps)
        if len(self.averageFrames) > self.fpsPace:
            self.averageFrames.pop(0)

    @property
    def avgFPS(self) -> float:
        if self.averageFrames == []:
            return 0    
        return int(sum(self.averageFrames) / len(self.averageFrames))

    @property
    def fps(self) -> float:
        if self.dt != 0:
            return int(1 / (self.dt / self.fpsPace))
        return 0
