import cv2
import easyocr

camera = cv2.VideoCapture(0)
reader = easyocr.Reader(['en'])
scale_percent = 40  # e.g., shrink to 50% of original size


while True:
    ret, frame = camera.read()
    if not ret:
        print("Failed to grab frame.")
        break

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
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break  # Exit on pressing 'q'

# Release resources
camera.release()
cv2.destroyAllWindows()
