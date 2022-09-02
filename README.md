# cartographer
pygame map editor for 2d games

to use:
launch cartographer.py and the application will open

controls:

1: draw mode \n
2: erase mode \n
3: select mode \n

Arrow Keys: scroll movement \n

CTRL + UP/DOWN: zoom in/out \n
SHIFT + UP/DOWN: layer up/down \n

CTRL + F: flood fill (only works in tile mode with a selected texture) \n
CTRL + D: flood delete (only works in tile mode) \n
CTRL + A: toggles auto tiling (will instead auto tile any selected tiles) \n
CTRL + Z: undo (buggy) \n

H: return to 0, 0 \n

L: cycle forward through view modes \n
SHIFT + L: cycle backwards through view modes \n

TAB: cycle forward through loaded sheets \n
SHIFT + TAB: cycle backward through loaded sheets \n

ESCAPE: quits the app (will instead deselected current selected texture if a texture is currently selected) \n

