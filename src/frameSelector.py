import cv2
import numpy as np
from barcodeDetector import barcodeDetector

# this camera doesn't respond to CAP_PROP_FOCUS/AUTOFOCUS (measured flat sharpness
# across the full focus range and a -1 readback) - it's effectively fixed-focus, so
# there's no software refocus to trigger; the sharp zone is a fixed physical distance.
# BLUR_THRESHOLD is a rough placeholder - watch the on-screen sharpness value with a
# real barcode at your working distance and adjust it to match.
BLUR_THRESHOLD = 20           # Laplacian variance below this = too blurry to decode
REFOCUS_AFTER_BLURRY_FRAMES = 15   # consecutive blurry frames before forcing a refocus

# whole-frame blur is a weak signal for "the barcode itself is out of focus" - the
# candidate region can be blurry while the rest of the scene keeps the average
# sharpness above BLUR_THRESHOLD, so refocus never triggers. A barcode-shaped
# candidate that keeps failing to decode is a much more specific and faster signal.
REFOCUS_AFTER_UNDECODED_CANDIDATE_FRAMES = 5

capture = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # index may need to change - see note below
# requesting well above what iVCam is likely to grant - the driver negotiates down
# to whatever it actually supports, and the printout below shows the real result
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)

# read back what the driver actually negotiated - capture.set() can silently be
# ignored, so this is the only way to know the real resolution being captured
print(f"Camera resolution: {int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

blurry_streak = 0
undecoded_candidate_streak = 0

while True:
    success, frame = capture.read()
    if not success:
        print("Camera is not working properly.")
        break
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    sharpness = cv2.Laplacian(gray_frame, cv2.CV_64F).var()
    cv2.putText(frame, f"sharpness: {sharpness:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    frame_h, frame_w = frame.shape[:2]
    cv2.putText(frame, f"resolution: {frame_w}x{frame_h}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    if sharpness < BLUR_THRESHOLD:
        blurry_streak += 1
        if blurry_streak >= REFOCUS_AFTER_BLURRY_FRAMES:
            # no-op over iVCam: its virtual DirectShow device doesn't forward real
            # focus control to Windows (confirmed by the flat sharpness / -1 readback
            # noted above), so toggling AUTOFOCUS here does nothing. Left commented
            # out rather than deleted in case a future camera/driver does support it.
            # capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            # capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            blurry_streak = 0
    else:
        blurry_streak = 0
        stopper, detected_points, candidate_boxes, count = barcodeDetector(gray_frame)

        # debug: regions the zoomed-candidate localizer tried (yellow)
        for (x, y, w, h) in candidate_boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 1)

        # border around any barcode that was actually decoded (green)
        for points in detected_points:
            cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

        if stopper:
            break

        if candidate_boxes and not stopper:
            # something barcode-shaped is in view but won't decode - much more
            # likely to be a focus problem than plain frame-wide blur, so react faster
            undecoded_candidate_streak += 1
            if undecoded_candidate_streak >= REFOCUS_AFTER_UNDECODED_CANDIDATE_FRAMES:
                # same no-op over iVCam as above - see comment near BLUR_THRESHOLD check
                # capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                # capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                undecoded_candidate_streak = 0
        else:
            undecoded_candidate_streak = 0
    ##should be changed depending on what needs to happen once a barcode is read

    # Display the live video feed
    cv2.imshow('Live Video Feed', frame)

    # Stop the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
capture.release()
cv2.destroyAllWindows()
