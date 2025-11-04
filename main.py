import cv2
import easyocr
camera = cv2.VideoCapture(0)

# Pseudocode for your system
def detect_letter():
    # 1. Capture frame
    ret, frame = camera.read()
    reader = easyocr.Reader(['en'])

    # 2. Simple preprocessing
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    letter = reader.readtext(gray, detail=0)

    # 4. Print to console
    print(f"Detected: {letter}")

    # 5. Display the frame
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return False

detect_letter()