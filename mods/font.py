from pygame import Surface
from pygame.font import Font as pgfont

class Font(pgfont):
    ''' this class extends from the pygame font class for more uses '''

    def __init__(self, filename, size, color=(255, 255, 255)):
        super().__init__(filename, size)
        self.font_size = size
        self._color = color

    def render_txt(self, txt : str, dest : Surface, loc : tuple[float, float], 
                          ctrd : bool=False, align_ctr : bool=False) -> Surface:
        ''' renders a surf with rendered text to the screen ''' 

        # check if there are new line commands
        if '\n' in txt:
            txts = txt.split('\n')
            sizes = [self.size(txt) for txt in txts]
            width = max([size[0] for size in sizes])
            height = sum([size[1] for size in sizes]) + len(txts)
            txt_surf = Surface((width, height))
            txt_surf.set_colorkey((0, 0, 0))

            x = 0
            y = 0
            for i, txt in enumerate(txts):
                if align_ctr:
                    x = (width - sizes[i][0]) // 2
                txt_surf.blit(self.render(txt, False, self._color), (x, y))
                y += sizes[i][1] + 1

        # otherwise, render normally
        else:
            txt_surf = self.render(txt, False, self._color)

        # blit surf to the location
        if ctrd:
            size = txt_surf.get_size()
            loc = loc[0] - size[0] // 2, loc[1] - size[1] // 2
        dest.blit(txt_surf, loc)

        return txt_surf

    def recolor(self, new_color : tuple[float, float, float]) -> None:
        ''' changes the color rendered from this font class '''
        self._color = new_color