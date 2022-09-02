# cartographer
pygame map editor for 2d games

to use:
launch cartographer.py and the application will open

controls:

1: draw mode
2: erase mode
3: select mode

Arrow Keys: scroll movement

CTRL + UP/DOWN: zoom in/out
SHIFT + UP/DOWN: layer up/down

CTRL + F: flood fill (only works in tile mode with a selected texture)
CTRL + D: flood delete (only works in tile mode)
CTRL + A: toggles auto tiling (will instead auto tile any selected tiles)
CTRL + Z: undo (buggy)

H: return to 0, 0

L: cycle forward through view modes
SHIFT + L: cycle backwards through view modes

TAB: cycle forward through loaded sheets
SHIFT + TAB: cycle backward through loaded sheets

ESCAPE: quits the app (will instead deselected current selected texture if a texture is currently selected)

