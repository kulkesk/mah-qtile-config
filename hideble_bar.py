from telnetlib import GA
from libqtile.bar import Gap

class HidebleGap(Gap):
    def __init__(self, size):
        super().__init__(size)
    
    # def _configure(self, qtile, screen, **kwargs):
    #     return super()._configure(qtile, screen, **kwargs)

    def is_show(self):
        return self.size != 0

    def show(self, is_show=True):
        if is_show != self.is_show():
            if is_show:
                self.size = self.size_calculated
            else:
                self.size_calculated = self.size
                self.size = 0

