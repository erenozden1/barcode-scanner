# ITF Barcode Reader

# Summary:

	Requirements

* Operate within a 20 cm – 150 cm distance range.

* Read ITF (Interleaved 2 of 5\) barcodes.

* Angled (skewed) reading capability.

Hardware Ideas

* The camera can have autofocus, so it can read barcodes at different distances.

* Narrow field-of-view, varifocal (adjustable focal length) lens \-\> provides a long focal length, increasing the number of pixels per bar for distant reads.

* Cross-polarization (to block reflections) \-\> If lighting is insufficient, polarizing film can be placed in front of the added LEDs. The same polarizing film or a Circular Polarizing (CPL) filter can be used for the camera.

[https://www.amazon.com/ELP-8mp-Microphone-Autofocus-Surveillance/dp/B0CG4BYL7Z](https://www.amazon.com/ELP-8mp-Microphone-Autofocus-Surveillance/dp/B0CG4BYL7Z) \- 1500 TRY

**Software process:** OpenCV cannot decode the ITF-type barcodes that Turkish Airlines (THY) uses for baggage. As a result, in the first phase of the project my attempts failed to read the barcodes and I could not understand why. It took me a long time to realize the problem was in the library itself. Once I noticed this, I resolved the issue by using the add-on provided by ZXing. Due to the limitations of my camera equipment, I could not fully test how well optimized my software is; I concluded it was successful once I started getting results on par with the iPhone's built-in barcode reader. The iPhone camera's resolution and its need for user input to focus show that such cameras cannot be used for this purpose. The rest of this report examines everything needed for the most optimized system.

# How to Run

Requires Python 3 and a webcam (developed on Windows).

```
pip install -r requirements.txt
cd src
python frameSelector.py
```

* `frameSelector.py` opens camera index `1` with the DirectShow backend (`cv2.VideoCapture(1, cv2.CAP_DSHOW)`). If you have only one camera, or you're not on Windows, change this line, e.g. to `cv2.VideoCapture(0)`.
* The scanner stops when it reads the barcode set in `EXPECTED_BARCODE_TEXT` in `barcodeDetector.py`. Change it to the number on your own test tag.
* Press `q` to quit.

# 1\. Project Requirements

* Read ITF (Interleaved 2 of 5\) barcodes with industrial reliability — IATA numbers on airline baggage tags are in ITF format.

* Operate within a 20 cm – 150 cm distance range.

* Angled (skewed) reading capability.

* Software: OpenCV (image processing) \+ ZBar or ZXing-C++ (barcode decoding).

* Total budget: approximately $100.

# 2\. Key Design Decisions

## 2.1 Autofocus Is Required, Motorized Zoom Is Unnecessary

When the barcode's distance changes, two things happen: the image loses sharpness (this genuinely prevents reading) and the barcode shrinks/grows in the frame (this usually isn't a problem). Therefore the varying-distance problem is solved with autofocus; automatic focal length adjustment (motorized zoom) is not needed.

## 2.2 Lens Selection: Narrow Field of View

A narrow lens (long focal length) concentrates the sensor's fixed pixel count onto a smaller scene area, increasing the number of pixels per bar at 150 cm. A wide lens spreads the pixels over a wide area, making thin ITF bars unresolvable.

Calculation: a 4000-pixel-wide sensor with a 65° lens sees \~0.48 mm per pixel at 150 cm — borderline for the thinnest ITF bars (0.25–0.5 mm). The same sensor with a \~40° lens reaches \~0.27 mm/pixel — a comfortable zone. So the narrow-lens variant should be preferred whenever possible.

A fixed-focal-length lens is not mandatory: a varifocal lens (e.g. 5–50 mm) is adjusted by hand during installation and then locked, giving freedom to experiment. Focal length (zoom ring) and sharpness (focus ring) are separate adjustments.

## 2.3 Monochrome vs Color Sensor

A monochrome sensor is optically superior for barcodes: with no Bayer filter, edges are sharper and light sensitivity is 2–3x better. However, autofocus monochrome modules are hard to find in the budget class. Since the 20–150 cm range requires autofocus, the practical choice is: a color autofocus camera \+ grayscale conversion in software.

# 3\. Lighting and Angled Reading

## 3.1 The Glare Problem

Baggage tags are synthetic-coated thermal paper (semi-glossy surface). The main cause of failure in angled reading is not geometry, but light reflected off the glossy surface washing the bars out to white.

## 3.2 Cross-Polarization (Recommended)

* Polarizing film is placed in front of the LEDs in one orientation, and in front of the lens rotated by 90°.

* Specular reflections preserve polarization and are blocked by the lens filter; the diffuse light carrying the barcode contrast passes through.

* Cost: \~$10–15 (adhesive film sheet). Because it absorbs \~60% of the light, LED power should be increased 2–3x.

## 3.3 Operating in Bright Environments

Cross-polarization is only effective with your own LEDs' light; ambient light is not polarized. Solution: reduce exposure time to \~0.5–1 ms and use close, powerful LEDs — the camera then mostly sees your polarized light. This also solves motion blur. If possible, adding a simple shade/hood over the scanning area is the cheapest and most robust solution.

## 3.4 LED Placement

LEDs should be placed at a 30–45° angle from the lens axis; this alone prevents most direct glare. Prefer diffused LED bars or panels.

# 4\. Challenges Specific to Baggage Tags

* **Curled/bent tags:** Because tags are wrapped around the handle, the barcode doesn't lie flat. The barcode is printed in multiple orientations on the tag; the software should try every barcode instance in the frame. Heavy curling may require region detection with OpenCV \+ perspective/cylindrical correction.

* **Resolution at 150 cm:** The IATA specification allows a narrow bar of \~0.25–0.5 mm; reliable decoding needs \~2 pixels per bar. This limits the horizontal field of view at 150 cm to \~50–60 cm — the scanning zone must be defined.
* **Realistic assessment:** In the 20–80 cm range, with cooperative presentation, a $100 system works well. Reliably reading a curled, glossy, moving tag at 150 cm is territory where industrial systems spend thousands of dollars; the 150 cm target should be validated early with real tags.

# 5\. Camera Comparison

| Model | Sensor / Resolution | Autofocus | Price / Note |
| :---- | :---- | :---- | :---- |
| ELP 12MP (IMX362) | 1/2.55", 4000×3000 | PDAF, \~300 ms (fast) | \~$70–80 — recommended for moving baggage |
| ELP 12MP (IMX577) | 1/2.3", 3840×3040 | Contrast AF (slower) | Interchangeable M12 lens (2.1–25 mm) |
| ELP 8MP (IMX179) | 3840×2160 | Autofocus | \~$60 — budget option |
| Arducam IMX519 16MP | 4656×3496 | Autofocus | \~$30–46 — requires Raspberry Pi |

Recommendation: for moving baggage, the ELP 12MP IMX362 (PDAF) — fast phase-detection autofocus. If lens flexibility is desired, the IMX577 version (with the 12/16 mm M12 lens option). The 65° lens variant should be preferred over the 76° one.

# 6\. Budget Summary

| Component | Estimated Price | Note |
| :---- | :---- | :---- |
| ELP 12MP PDAF Autofocus Camera (IMX362) | $70–80 | Main recommendation |
| LED lighting (diffused bar/panel) | $15–20 | Choose a powerful one to compensate for polarizing film loss |
| Linear polarizing film (2-pack) | $10–15 | For cross-polarization |
| **TOTAL** | **\~$95–115** | At the budget limit |

# 7\. Purchase Links

## 7.1 Retail

* ELP 12MP PDAF (IMX362), Amazon: amazon.com/dp/B0DQNP1MP9 (\~$70–80)

* ELP 12MP IMX577 (interchangeable M12 lens): svpro.cc/product/2008

* ELP 8MP autofocus (IMX179), Amazon: amazon.com/dp/B0C23C5NHS (\~$60)

* Arducam IMX519 16MP (Raspberry Pi): amazon.com/dp/B09STL7S88 (\~$35–46)

* Polarizing film (2-pack, adhesive): amazon.com/dp/B0BS6FMZNL (\~$10–15)

* LED: search Amazon for "12V LED bar light diffused" (\~$15–20)

## 7.2 Bulk Purchasing (B2B)

The manufacturer of ELP cameras is Shenzhen Ailipu Technology Co., Ltd. (since 2005; CE, FCC, RoHS, UL, ISO certified). They accept OEM/ODM and customization — for volume orders, the lens/sensor combination you want can be produced.

* Direct: elpcctv.com — sales@elpcctv.com

* Alibaba store: elpcctv.en.alibaba.com (Trade Assurance recommended)

* Made-in-China: ellipe.en.made-in-china.com

* Typical MOQ: 50–100 units for custom production; for standard models, discounts start at 20–50 units (\~30–50% cheaper than retail).

* Polarizing film wholesale: 3dlens.com; industrial grade: apioptics.com, MidOpt.

B2B advice: before committing to an MOQ, order 2–3 samples and validate them at 150 cm with real baggage tags. Autofocus and fixed-focus variants look very similar; clearly specify the exact model code and lens field of view on the order form.

# 8\. Software Architecture (Summary)

* OpenCV: image capture, grayscale, adaptive thresholding, skew/perspective correction, center region cropping (digital zoom).

* Decoding: ZBar or ZXing-C++ (don't write an ITF decoder from scratch).

* If a monochrome camera is used: frames arrive single-channel; set CAP\_PROP\_CONVERT\_RGB \= 0 if needed.

* Try every barcode candidate in the frame (the barcode is printed multiple times on a baggage tag).
