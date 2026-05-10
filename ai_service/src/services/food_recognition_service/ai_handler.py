import cv2
import numpy as np
import onnxruntime as ort

from .utils.preprocess import preprocess_for_detector, preprocess_for_supernet, to_norm_xyxy, safe_crop, get_features, get_density, get_classes

class AIHandler:
    def __init__(self):
        self.frcnn_session = ort.InferenceSession("src/services/food_recognition_service/models/faster_rcnn.onnx")
        self.supernet_session = ort.InferenceSession("src/services/food_recognition_service/models/supernet.onnx")

    def analyze(self, image_bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        h, w = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        det_input = preprocess_for_detector(img_bgr)
        det_outputs = self.frcnn_session.run(None, {self.frcnn_session.get_inputs()[0].name: det_input})
        
        results = {"detail": []}
        for i in range(len(det_outputs[0])):
            box, label, conf = det_outputs[0][i], det_outputs[1][i], det_outputs[2][i]
            
            if conf < 0.8: 
                continue

            x1, y1, x2, y2 = to_norm_xyxy(box[0], box[1], box[2], box[3], h, w, 512.0, 512.0)
            crop = safe_crop(img_rgb, np.array([x1, y1, x2, y2]))
            
            f_area, f_ratio, f_api = get_features(crop)
            food_idx = int(label) - 1
            meta = [f_area, f_ratio, f_api, get_density(food_idx)]

            sn_img, sn_ft, sn_meta = preprocess_for_supernet(crop, food_idx, meta)
            weight_out = self.supernet_session.run(None, {"image": sn_img, "food_type": sn_ft, "meta": sn_meta})
            
            results["detail"].append({
                "name_food": get_classes(food_idx),
                "weight": round(float(weight_out[0][0][0]), 2),
                "probability": round(float(conf), 2)
            })
        if not results["detail"]:
            results["detail"] = "Еда на картинке не найдена"
            results["status"] = "failed"
        else:
            results["status"] = "success"
        return results
    
    