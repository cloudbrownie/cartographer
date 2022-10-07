# main script simply brings everything together
from mods.glob import Glob

if __name__ == '__main__':
  glob = Glob(1200, 800)
  # window loop
  while 1:

    glob.window.render()
    glob.input.handle()
    glob.clock.tick()
    glob.update()