import time
from djitellopy import Tello, TelloException
import cv2
import easyocr
import threading
import queue
from VideoDriver import VideoDriver
from HeightGuard import HeightGuard

print("program: Loading ML models...")

camera = None
drone = None
reader = easyocr.Reader(['en'])
scale_percent = 40
ack_frozen = False
has_taken_off = False
height_guard = None
key_queue = queue.Queue()
action_queue = queue.Queue()  # Queue for letter-triggered actions


def main():
    global camera, ack_frozen, scale_percent, drone, has_taken_off, height_guard

    camera = VideoDriver()
    camera.initialize()
    drone = camera.drone

    # Start key handler thread
    key_thread = threading.Thread(target=thread__wait_key, daemon=True)
    key_thread.start()

    # Start action handler thread
    action_thread = threading.Thread(target=thread__handle_actions, daemon=True)
    action_thread.start()

    if camera.platform == "DRONE":
        scale_percent = 50

    while True:
        key = cv2.waitKey(1) & 0xFF

        # Send key to handler thread if it's not "no key"
        if key != 255:
            key_queue.put(key)

        if key == ord('q'):
            break

        ret, frame = camera.read()
        if not ret:
            print("Failed to grab frame.")
            continue
        if ret == 2:
            if not ack_frozen:
                print("Camera is frozen.")
                ack_frozen = True
            continue

        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)

        resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(gray)

        for bbox, text, confidence in results:
            conf_pct = int(confidence * 100)
            print(f"Detected: {text}, Confidence: {conf_pct}%")
            if conf_pct > 80:
                # Send action to handler thread instead of executing here
                action_queue.put((text, frame.copy()))

        cv2.imshow('Frame', frame)

    camera.release()
    cv2.destroyAllWindows()


def thread__handle_actions():
    """Handles letter-triggered actions in a separate thread"""
    global camera, drone, has_taken_off, height_guard

    while True:
        try:
            text, frame = action_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        try:
            match text:
                case 'A':
                    print("Action for A")
                    drone.rotate_clockwise(360)
                    time.sleep(5)
                    drone.rotate_clockwise(180)
                    drone.move_forward(30)
                case 'B':
                    print("Action for B")
                    drone.rotate_clockwise(180)
                    print("Should take a photo now")
                    # Save the current frame as an image
                    timestamp = int(time.time())
                    filename = f"tello_photo_{timestamp}.jpg"
                    # Freeze the frame to avoid motion blur
                    camera.set_freeze(True)
                    cv2.imwrite(filename, frame)
                    print(f"Photo saved: {filename}")
                    camera.set_freeze(False)
                case 'C':
                    print("Action for C")
                    drone.land()
                    # Kill the height guard
                    if height_guard is not None:
                        height_guard.stop()
                        height_guard = None
                    has_taken_off = False
                case _:
                    print("No action for this letter")
        except TelloException as e:
            print(f"Drone error during action: {e}")


def thread__wait_key():
    global camera, drone, has_taken_off, height_guard

    while True:
        try:
            # Block until a key is available (no busy waiting!)
            key = key_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if camera is None or drone is None:
            continue
        if not isinstance(camera, VideoDriver) or not isinstance(drone, Tello):
            continue

        try:
            if key == ord('p'):
                camera.set_freeze(not camera.frozen)
            elif key == ord('h'):
                print(str(drone.get_height()) + "cm")
            elif key == ord('b'):
                print(str(drone.get_battery()) + "%")
            elif key == ord('t'):
                drone.takeoff()
                height_guard = HeightGuard(100, camera.drone)
                has_taken_off = True
            elif key == ord('r'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                drone.rotate_clockwise(90)
            elif key == ord('f'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                drone.rotate_clockwise(-90)
            elif key == ord('l'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                drone.land()
                # Kill the height guard
                if height_guard is not None:
                    height_guard.stop()
                    height_guard = None
                has_taken_off = False
            elif key == ord('e'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                drone.emergency()
            elif key == ord('w'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                try:
                    drone.move_forward(30)
                except Exception:
                    pass
            elif key == ord('s'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                try:
                    drone.move_back(30)
                except Exception:
                    pass
            elif key == ord('a'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                try:
                    drone.move_left(30)
                except Exception:
                    pass
            elif key == ord('d'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                try:
                    drone.move_right(30)
                except Exception:
                    pass
            elif key == ord('u'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                drone.move_up(20)
            elif key == ord('i'):
                if not has_taken_off:
                    print("error: Take off first.")
                    continue
                drone.move_down(20)
        except TelloException as e:
            print(f"Drone error: {e}")


try:
    main()
except KeyboardInterrupt:
    if isinstance(camera, VideoDriver):
        camera.release()
    cv2.destroyAllWindows()