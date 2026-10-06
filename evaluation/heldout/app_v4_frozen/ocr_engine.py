"""EasyOCR extraction with geometry-driven ruled-table recognition.

No document names, page numbers, vocabularies or expected cell values are used.
Cell coordinates refer to the deskewed image; the affine transform is audited.
"""
import math
import cv2
import numpy as np


def prepare(image):
    gray = cv2.cvtColor(np.asarray(image.convert('RGB')), cv2.COLOR_RGB2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 15)
    h, w = gray.shape
    lines = cv2.HoughLinesP(binary, 1, np.pi/1800, threshold=max(60, w//10),
                           minLineLength=w//5, maxLineGap=20)
    angles = []
    if lines is not None:
        for x0, y0, x1, y1 in lines[:, 0]:
            angle = math.degrees(math.atan2(float(y1-y0), float(x1-x0)))
            if abs(angle) < 5:
                angles.append(angle)
    angle = float(np.median(angles)) if len(angles) >= 5 else 0.0
    if abs(angle) < 0.08:
        angle = 0.0
    matrix = cv2.getRotationMatrix2D((w/2, h/2), angle, 1)
    if angle:
        gray = cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    enhanced = cv2.createCLAHE(clipLimit=2, tileGridSize=(8, 8)).apply(gray)
    return gray, enhanced, angle, matrix.tolist()


def detect_tables(gray):
    h, w = gray.shape
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 15)
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(25, w//30), 1)))
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(25, h//30))))
    grid = cv2.dilate(horizontal | vertical, np.ones((3, 3), np.uint8))
    contours, hierarchy = cv2.findContours(grid, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return []
    groups = {}
    for i, contour in enumerate(contours):
        parent = int(hierarchy[0, i, 3])
        x, y, cw, ch = cv2.boundingRect(contour)
        if parent < 0 or min(cw, ch) < 12 or cw*ch < 200:
            continue
        # Holes enclosed by a connected grid are candidate cells.
        if cv2.contourArea(contour)/(cw*ch) < 0.65:
            continue
        groups.setdefault(parent, []).append([x, y, x+cw, y+ch])
    tables = []
    for parent, cells in groups.items():
        if len(cells) < 12:
            continue
        x, y, cw, ch = cv2.boundingRect(contours[parent])
        tables.append({'bbox': [x, y, x+cw, y+ch], 'cells': cells})
    return sorted(tables, key=lambda t: (t['bbox'][1], t['bbox'][0]))


def _boundaries(values, tolerance):
    groups = []
    for value in sorted(values):
        if groups and value - np.mean(groups[-1]) <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [float(np.mean(group)) for group in groups]


def _lines(detections, clean_edges=False):
    boxes = []
    for box, text, confidence in detections:
        pts = np.asarray(box)
        boxes.append((float(pts[:, 0].min()), float(pts[:, 1].min()),
                      float(pts[:, 0].max()), float(pts[:, 1].max()), str(text)))
    boxes.sort(key=lambda b: ((b[1]+b[3])/2, b[0]))
    rows = []
    for x0, y0, x1, y1, text in boxes:
        center = (y0+y1)/2
        candidates = [row for row in rows
                      if abs(center-row['y']) <= max(4, min(y1-y0, row['height'])*0.4)]
        if not candidates:
            rows.append({'top': y0, 'bottom': y1, 'y': center, 'height': y1-y0,
                         'items': [(x0, text)]})
            continue
        row = min(candidates, key=lambda r: abs(center-r['y']))
        row['items'].append((x0, text)); row['top'] = min(row['top'], y0)
        row['bottom'] = max(row['bottom'], y1); row['height'] = max(row['height'], y1-y0)
        row['y'] = (row['top']+row['bottom'])/2
    lines = []
    for row in rows:
        items = [text.strip(" _-'\"<>=~.[]{}") if clean_edges else text
                 for _, text in sorted(row['items'])]
        lines.append({'y': row['y'], 'text': ' '.join(text for text in items if text.strip())})
    return lines


def extract_page(image, reader):
    gray, enhanced, angle, matrix = prepare(image)
    tables = detect_tables(gray)
    # Mask only confirmed table interiors for prose detection. Recognition of
    # table cells uses the original deskewed grayscale pixels, without grid lines.
    prose_image = enhanced.copy()
    for table in tables:
        x0, y0, x1, y1 = table['bbox']
        prose_image[y0:y1, x0:x1] = 255
    prose = reader.readtext(prose_image, detail=1, paragraph=False, canvas_size=3508,
                            mag_ratio=1, min_size=10, batch_size=1)
    blocks = _lines(prose)
    for table in tables:
        boxes = table.pop('cells')
        median_height = float(np.median([b[3]-b[1] for b in boxes]))
        tolerance = max(4, median_height*0.22)
        xs = _boundaries([b[i] for b in boxes for i in (0, 2)], tolerance)
        ys = _boundaries([b[i] for b in boxes for i in (1, 3)], tolerance)
        cells = []
        for bbox in sorted(boxes, key=lambda b: (b[1], b[0])):
            x0, y0, x1, y1 = bbox
            # Contour bounding rectangles include their boundary pixel.
            inset = 2
            crop = gray[y0+inset:y1-inset, x0+inset:x1-inset]
            ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]
            components, _, stats, _ = cv2.connectedComponentsWithStats(ink)
            nonempty = any(s[cv2.CC_STAT_AREA] >= 5 and s[cv2.CC_STAT_HEIGHT] >= 3
                           for s in stats[1:]) if components > 1 else False
            if not nonempty or int(crop.max())-int(crop.min()) < 18:
                detections = []
            elif y1-y0 > median_height*1.65:
                detections = reader.readtext(crop, detail=1, paragraph=False,
                    min_size=5, mag_ratio=2, canvas_size=2560,
                    rotation_info=[90, 270] if crop.shape[0] > crop.shape[1]*2 else None)
            else:
                detections = reader.recognize(crop, detail=1, paragraph=False)
            text = ' '.join(row['text'] for row in _lines(detections, clean_edges=True))
            confidences = [float(d[2]) for d in detections]
            cell = {'bbox': bbox, 'text': text, 'confidence': min(confidences) if confidences else None,
                    'blank': not nonempty, 'row': int(np.argmin(np.abs(np.asarray(ys)-y0))),
                    'row_end': int(np.argmin(np.abs(np.asarray(ys)-y1))),
                    'column': int(np.argmin(np.abs(np.asarray(xs)-x0))),
                    'column_end': int(np.argmin(np.abs(np.asarray(xs)-x1)))}
            cells.append(cell)
        table.update(cells=cells, x_boundaries=xs, y_boundaries=ys)
        rows = [[''] * (len(xs)-1) for _ in range(len(ys)-1)]
        for cell in cells:
            for row in range(cell['row'], cell['row_end']):
                if cell['column'] < len(xs)-1:
                    rows[row][cell['column']] = cell['text']
        table['rows'] = rows
        table_text = '\n'.join(' | '.join(row) for row in rows)
        blocks.append({'y': table['bbox'][1], 'text': table_text})
    return {'page_text': '\n'.join(block['text'] for block in sorted(blocks, key=lambda b: b['y'])),
            'deskew_degrees': angle, 'affine_matrix': matrix, 'tables': tables,
            'detections': [{'bbox': np.asarray(box).astype(float).tolist(), 'text': text,
                            'confidence': float(conf)} for box, text, conf in prose]}
