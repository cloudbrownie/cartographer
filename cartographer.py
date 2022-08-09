# main script simply brings everything together
from mods.glob import Glob

glob = Glob(1000, 700)

# window loop
while 1:

  glob.window.render()
  glob.input.handle()
  glob.clock.tick()