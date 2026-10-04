import cv2
import zxingcpp
import numpy as np
COUNT = 0
EXPECTED_BARCODE_TEXT = "0235859367"  # testing only - flag any decode that doesn't match this - 
#The decoded barcode number should be compared against the passenger's barcode number by connecting to a database
#if they don't match, the barcode and the bag should be rejected

def _order_points(pts):
    # returns points ordered top-left, top-right, bottom-right, bottom-left
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _four_point_transform(gray, pts, padding=8):
    rect = _order_points(pts)
    center = rect.mean(axis=0)

    # push corners outward a bit so the quiet zone around the bars survives the warp
    directions = rect - center
    norms = np.linalg.norm(directions, axis=1, keepdims=True)
    norms[norms == 0] = 1
    padded_rect = rect + directions / norms * padding

    (tl, tr, br, bl) = padded_rect
    max_width = max(int(np.linalg.norm(br - bl)), int(np.linalg.norm(tr - tl)))
    max_height = max(int(np.linalg.norm(tr - br)), int(np.linalg.norm(tl - bl)))
    if max_width <= 0 or max_height <= 0:
        return None

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(padded_rect.astype(np.float32), dst)
    return cv2.warpPerspective(gray, matrix, (max_width, max_height))


def _enhance_candidate(image):
    # boost local contrast (helps with glare/dim lighting), then sharpen edges via
    # unsharp masking - can't invent detail, but can tip a marginal read into decoding
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(image)
    blurred = cv2.GaussianBlur(contrast_enhanced, (0, 0), sigmaX=3)
    return cv2.addWeighted(contrast_enhanced, 1.5, blurred, -0.5, 0)


def _locate_barcode_candidates(gray, min_area=400, target_min_dimension=200,
                                max_upscale=8, approx_epsilon=0.03):
    # bars produce a strong gradient along one axis and a weak gradient along the
    # other; combining both directions catches upright and 90-degree-rotated codes
    grad_x = cv2.Sobel(gray, cv2.CV_32F, dx=1, dy=0, ksize=-1)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, dx=0, dy=1, ksize=-1)
    gradient = cv2.max(cv2.convertScaleAbs(cv2.subtract(grad_x, grad_y)),
                        cv2.convertScaleAbs(cv2.subtract(grad_y, grad_x)))

    blurred = cv2.blur(gradient, (9, 9))
    _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    closed = cv2.erode(closed, None, iterations=2)
    closed = cv2.dilate(closed, None, iterations=2)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for c in contours:
        if cv2.contourArea(c) < min_area:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, approx_epsilon * peri, True)

        if len(approx) == 4:
            # clean quadrilateral - use its actual corners so we can perspective-warp
            # away skew from an off-axis viewing angle, not just in-plane rotation
            quad = approx.reshape(4, 2).astype(np.float32)
        else:
            # contour isn't a clean quad (occlusion/noise) - fall back to a rotated rect
            quad = cv2.boxPoints(cv2.minAreaRect(c))

        warped = _four_point_transform(gray, quad, padding=8)
        if warped is None or warped.size == 0:
            continue

        # a distant/small candidate needs more magnification than a close/large one -
        # scale so the shorter side lands near target_min_dimension either way
        warped_h, warped_w = warped.shape[:2]
        upscale_factor = target_min_dimension / min(warped_h, warped_w)
        upscale_factor = min(max(upscale_factor, 1.0), max_upscale)

        upscaled = cv2.resize(warped, None, fx=upscale_factor, fy=upscale_factor,
                               interpolation=cv2.INTER_CUBIC)
        enhanced = _enhance_candidate(upscaled)

        x, y, w, h = cv2.boundingRect(quad.astype(np.intp))
        candidates.append({
            "image": enhanced,
            "quad": [tuple(map(int, p)) for p in quad],
            "box": (x, y, w, h),
        })

    return candidates


def _position_to_points(position):
    corners = [position.top_left, position.top_right, position.bottom_right, position.bottom_left]
    return [(int(p.x), int(p.y)) for p in corners]


def _log_barcode(b):
    print(b.bytes)         # raw bytes, e.g. b'ABC-1234'
    print(b.text)          # as a string
    print(b.format)        # symbology, e.g. PDF417
    print(b.position)      # corner points: top_left, top_right, bottom_right, bottom_left
    print(b.orientation)   # rotation of the symbol, in degrees


def barcodeDetector(frame):
    # a wrong barcode (misread, or a real but irrelevant one sharing the frame with
    # the target) must not stop the scan - only a match to EXPECTED_BARCODE_TEXT does
    global COUNT
    matched_points = []
    candidates = []

    for b in zxingcpp.read_barcodes(frame):
        _log_barcode(b)
        if b.text == EXPECTED_BARCODE_TEXT:
            matched_points.append(_position_to_points(b.position))
        else:
            COUNT += 1
            print(f"!!! ALERT: unexpected barcode read: {b.text!r} (expected {EXPECTED_BARCODE_TEXT!r}) - ignoring, still looking")
            print(f"COUNT: {COUNT}")
    if not matched_points:
        # nothing matched directly (too small/far/angled, or only wrong barcodes were
        # visible) - retry on perspective-corrected, zoomed-in candidate regions
        candidates = _locate_barcode_candidates(frame)
        for candidate in candidates:
            for b in zxingcpp.read_barcodes(candidate["image"]):
                _log_barcode(b)
                if b.text == EXPECTED_BARCODE_TEXT:
                    # the exact decoded corners live in the warped candidate's own
                    # coordinate space, not the original (skewed) frame - report the
                    # source quad instead since that's what actually encloses the
                    # barcode in the original view
                    matched_points.append(candidate["quad"])
                else:
                    COUNT += 1
                    print(f"!!! ALERT: unexpected barcode read: {b.text!r} (expected {EXPECTED_BARCODE_TEXT!r}) - ignoring, still looking")
                    print(f"COUNT: {COUNT}")
            if matched_points:
                break

    candidate_boxes = [c["box"] for c in candidates]

    if matched_points:
        COUNT += 1
        print(f"Matching barcode(s) detected: {len(matched_points)}")
        print(f"COUNT: {COUNT}")
        return True, matched_points, candidate_boxes, COUNT

    #print("No matching barcode detected.")
    return False, matched_points, candidate_boxes, COUNT
