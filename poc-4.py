print ("program: Loading ML models...")

import cv2
import easyocr
from VideoDriver import VideoDriver

camera = None
reader = easyocr.Reader(['en'])
scale_percent = 40  # e.g., shrink to 50% of original
ack_frozen = False


def main():
    # Using:
    global camera, ack_frozen

    # Next:
    camera = VideoDriver()
    camera.initialize()
    # camera = cv2.VideoCapture(0)

    print(camera.drone.get_battery())
    while True:

        key = cv2.waitKey(1) & 0xFF
        if key == ord('p'):
            camera.set_freeze(not camera.frozen)
        elif key == ord('q'):
            break  # Exit on pressing 'q'

        ret, frame = camera.read()
        if not ret:
            print("Failed to grab frame.")
            break
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
