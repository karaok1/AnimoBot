from windowcapture import WindowCapture


class Coordinates:
    instance = None
    OFFSET_X = 0
    OFFSET_Y = 0

    WIDTH = 75
    HEIGHT = 20

    win_cap: WindowCapture = None

    def __init__(self, win_cap):
        self.win_cap = win_cap

        width = int(win_cap.w)
        self.OFFSET_X = width

    def get_area(self, img):
        return img[
               self.OFFSET_Y: self.OFFSET_Y + self.HEIGHT,
               self.OFFSET_X: self.OFFSET_X + self.WIDTH,
               ]

    def get_area_points(self):
        return (self.OFFSET_X, self.OFFSET_Y), (
            self.OFFSET_X + self.WIDTH, self.OFFSET_Y + self.HEIGHT)
