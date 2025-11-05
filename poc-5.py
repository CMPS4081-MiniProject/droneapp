print("program: Loading ML models...")

import cv2
import easyocr
from VideoDriver import VideoDriver

camera = None
drone = None
reader = easyocr.Reader(['en'])
scale_percent = 40  # e.g., shrink to 50% of original
ack_frozen = False
has_taken_off = False


def main():
    # Using:
    global camera, ack_frozen, scale_percent, drone, has_taken_off

    # Next:
    camera = VideoDriver()
    camera.initialize()
    drone = camera.drone
    # camera = cv2.VideoCapture(0)
    if camera.platform == "DRONE":
        scale_percent = 50  # Upscale the video for better results

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('p'):
            camera.set_freeze(not camera.frozen)
        elif key == ord('q'):
            break  # Exit on pressing 'q'
        elif key == ord('h'):
            print(str(drone.get_height()) + "cm")
        elif key == ord('b'):
            print(str(drone.get_battery()) + "%")
        elif key == ord('t'):
            drone.takeoff()
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
            except Exception as e:
                continue
        elif key == ord('s'):
            if not has_taken_off:
                print("error: Take off first.")
                continue
            try:
                drone.move_back(30)
            except Exception as e:
                continue
        elif key == ord('a'):
            if not has_taken_off:
                print("error: Take off first.")
                continue
            try:
                drone.move_left(30)
            except Exception as e:
                continue
        elif key == ord('d'):
            if not has_taken_off:
                print("error: Take off first.")
                continue
            try:
                drone.move_right(30)
            except Exception as e:
                continue

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
            conf_pct = int(confidence * 100)  # Convert to percent as int
            print(f"Detected: {text}, Confidence: {conf_pct}%")
            if conf_pct > 80:
                match text:
                    case 'A':
                        print("Action for A")
                    case 'B':
                        print("Action for B")
                    case 'C':
                        print("Action for C")
                    case _:
                        print("No action for this letter")

        # print(f"Detected: {letter}")  # You might want to process/format this output

        cv2.imshow('Frame', frame)

    # Release resources
    camera.release()
    cv2.destroyAllWindows()


try:
    main()
except KeyboardInterrupt:
    # Checks if camera is an instance of VideoDriver
    if isinstance(camera, VideoDriver):
        camera.release()
    cv2.destroyAllWindows()
