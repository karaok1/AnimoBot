from math import sqrt
from threading import Thread, Lock
from time import sleep, time

import pyautogui

from detection import Detection


# from entities.minimap import MiniMap


class BotState:
    INITIALIZING = 0
    SEARCHING = 1
    ATTACKING = 2
    COLLECTING = 3


class AnimoBot:
    # constants
    INITIALIZING_SECONDS = 6
    IGNORE_RADIUS = 130
    TOOLTIP_MATCH_THRESHOLD = 0.72

    # threading properties
    stopped = True
    lock = None

    # properties
    state = None
    targets = []
    screenshot = None
    timestamp = None
    movement_screenshot = None
    window_offset = (0, 0)
    click_history = []

    detection: Detection = None

    def __init__(self, window_offset, window_size, detection, map):
        # create a thread lock object
        self.lock = Lock()

        # for translating window positions into screen positions, it's easier to just
        # get the offsets and window size from WindowCapture rather than passing in
        # the whole object
        self.window_offset = window_offset
        self.window_w = window_size[0]
        self.window_h = window_size[1]

        self.detection = detection  # set the Detection object instance
        self.map = map

        # start bot in the initializing mode to allow us time to get setup.
        # mark the time at which this started so, we know when to complete it
        self.state = BotState.INITIALIZING
        self.timestamp = time()

    def click_next_target(self):
        # 1. order targets by distance from center
        # loop:
        #   2. hover over the nearest target
        #   3. if it's not, check the next target
        # endloop
        # 4. if no target was found return false
        # 5. click on the found target and return true
        targets = self.targets_ordered_by_distance(self.targets)

        target_i = 0
        found_collectable = False
        while not found_collectable and target_i < len(targets):
            # if we stopped our script, exit this loop
            if self.stopped:
                break

            # load up the next target in the list and convert those coordinates
            # that are relative to the game screenshot to a position on our
            # screen
            target_pos = targets[target_i]
            screen_x, screen_y = self.get_screen_position(target_pos)
            print("Moving mouse to x:{} y:{}".format(screen_x, screen_y))

            # move the mouse
            pyautogui.moveTo(x=screen_x, y=screen_y)
            # short pause to let the mouse movement complete and allow
            # time for the tooltip to appear
            sleep(1.250)
            print("Click on confirmed target at x:{} y:{}".format(screen_x, screen_y))
            found_collectable = True
            self.state = BotState.COLLECTING
            pyautogui.click()
            # save this position to the click history
            self.click_history.append(target_pos)
            target_i += 1

        return found_collectable

    def is_moving(self):
        return self.detection.coordinates.has_changed()

    def targets_ordered_by_distance(self, targets):
        # our character is always in the center of the screen
        my_pos = (self.window_w / 2, self.window_h / 2)

        # searched "python order points by distance from point"
        # simply uses the pythagorean theorem
        # https://stackoverflow.com/a/30636138/4655368
        def pythagorean_distance(pos):
            return sqrt((pos[0] - my_pos[0]) ** 2 + (pos[1] - my_pos[1]) ** 2)

        targets.sort(key=pythagorean_distance)

        # print(my_pos)
        # print(targets)
        # for t in targets:
        #    print(pythagorean_distance(t))

        # ignore targets at are too close to our character (within 130 pixels) to avoid
        # re-clicking a deposit we just mined
        targets = [t for t in targets if pythagorean_distance(t) > self.IGNORE_RADIUS]

        return targets

    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the WindowCapture __init__ constructor.
    def get_screen_position(self, pos):
        return pos[0] + self.window_offset[0], pos[1] + self.window_offset[1]

    # threading methods

    def update_targets(self, targets):
        self.lock.acquire()
        self.targets = targets
        self.lock.release()

    def update_screenshot(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()

    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def stop(self):
        self.stopped = True

    # main logic controller
    def run(self):
        while not self.stopped:
            if self.state == BotState.INITIALIZING:
                # do no bot actions until the startup waiting period is complete
                if time() > self.timestamp + self.INITIALIZING_SECONDS:
                    # start searching when the waiting period is over
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()

            elif self.state == BotState.SEARCHING:
                # check the given click point targets, confirm a collectable,
                # then click it.
                success = self.click_next_target()
                # if not successful, try one more time
                if not success:
                    sleep(1)
                    success = self.click_next_target()

                # if successful, switch state to moving
                # if not, click to random position and keep searching
                if success:
                    self.lock.acquire()
                    self.state = BotState.COLLECTING
                    self.lock.release()
                else:
                    # click at a random position on the minimap if bot is not moving
                    sleep(3)
                    if not self.is_moving():
                        success = self.click_next_target()
                        if not success:
                            self.detection.map.click_random_position()
                        else:
                            self.lock.acquire()
                            self.state = BotState.COLLECTING
                            self.lock.release()

            elif self.state == BotState.COLLECTING:
                sleep(1)
                if self.is_moving():
                    pass
                else:
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()
            elif self.state == BotState.ATTACKING:
                pass
