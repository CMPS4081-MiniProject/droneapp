from djitellopy import Tello
import threading


class HeightGuard:
    def __init__(self, limit=100, config=Tello()):
        self.drone = config
        self.limit = limit
        self.current_height = 0
        self.maintain_height_thread__stop_event = threading.Event()
        self.maintain_height_thread = threading.Thread(target=self._maintain_height)
        self.maintain_height_thread.daemon = True
        self.maintain_height_thread.start()

    def _maintain_height(self):
        # Consistently check the height of the drone
        dead = self.maintain_height_thread__stop_event.is_set()
        while not dead:
            self.drone.connect()
            height = self.drone.get_height()
            self.current_height = height

            if height < self.limit:
                self.drone.move_up(20)

    def stop(self):
        # Stop the thread
        self.maintain_height_thread__stop_event.set()
