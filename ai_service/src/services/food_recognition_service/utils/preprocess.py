import numpy as np
import albumentations as A
import cv2

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

META_MEAN = np.array([230187.149645, 0.762236, 117.990822, 0.774815], dtype=np.float32)
META_STD = np.array([251482.752087, 0.326101, 31.697426, 0.266599], dtype=np.float32)

density_indices = {
    0: 0.65, 1: 0.60, 2: 1.04, 3: 0.50, 4: 1.10, 5: 0.40, 6: 1.05, 7: 0.95, 8: 1.00, 9: 0.85, 
    10: 1.00, 11: 0.90, 12: 1.00, 13: 0.65, 14: 0.55, 15: 1.05, 16: 0.45, 17: 0.35, 18: 0.80, 19: 0.85, 
    20: 0.40, 21: 0.60, 22: 0.91, 23: 0.45, 24: 0.40, 25: 0.20, 26: 0.35, 27: 0.50, 28: 0.75, 29: 0.95, 
    30: 0.50, 31: 1.00, 32: 1.00, 33: 1.25, 34: 0.35, 35: 1.04, 36: 1.02, 37: 0.80, 38: 0.30, 39: 0.55, 
    40: 0.95, 41: 0.65, 42: 0.75, 43: 0.95, 44: 1.03, 45: 1.04, 46: 0.85, 47: 1.02, 48: 0.55, 49: 0.40, 
    50: 0.70, 51: 0.65, 52: 0.90, 53: 0.80, 54: 0.95, 55: 0.60, 56: 1.00, 57: 0.60, 58: 1.40, 59: 0.30, 
    60: 0.55, 61: 0.75, 62: 1.05, 63: 1.03, 64: 1.02, 65: 1.15, 66: 0.65, 67: 0.25, 68: 0.25, 69: 0.95, 
    70: 0.75, 71: 1.20, 72: 1.00, 73: 1.01, 74: 1.04, 75: 1.05, 76: 0.90, 77: 0.95, 78: 0.70, 79: 1.02, 
    80: 0.95, 81: 0.92, 82: 1.05, 83: 0.95, 84: 1.05, 85: 0.55, 86: 0.85, 87: 1.03, 88: 0.75, 89: 1.02, 
    90: 0.85, 91: 0.45, 92: 0.75, 93: 1.15, 94: 0.65, 95: 0.55, 96: 0.65, 97: 0.55, 98: 0.85, 99: 0.85, 
    100: 1.06, 101: 0.08, 102: 0.75, 103: 0.65, 104: 0.75, 105: 0.95, 106: 1.30, 107: 0.85, 108: 0.95, 109: 0.45, 
    110: 0.65, 111: 1.02, 112: 0.55, 113: 0.50, 114: 1.00, 115: 0.65, 116: 1.00, 117: 0.95, 118: 1.02, 119: 1.02, 
    120: 1.00, 121: 1.02, 122: 0.25, 123: 1.04, 124: 0.80, 125: 0.50, 126: 1.02, 127: 0.65, 128: 0.35, 129: 1.02, 
    130: 0.85, 131: 0.35, 132: 0.85, 133: 0.75, 134: 0.55, 135: 1.00, 136: 1.05, 137: 1.20
}

classes = ['achichuk', 'almond', 'apple_juice', 'apple_strudel', 'balqaymaq', 'bauyrsak', 'beef', 'beef_cutlet', 'beefstroganov', 'beet_salad', 'belise_tea', 'beshbarmak', 'black_tea', 'bliny', 'borek', 'borsh', 'bread', 'broccoli', 'buckwheat', 'bukteme', 'bun', 'burger', 'butter', 'caesar_salad', 'capuccino', 'cereal', 'chak_chak', 'cheburek', 'cheese_sticks', 'cheesecake', 'chelpek', 'chicken', 'chicken_in_plum', 'chocolate', 'ciabatta', 'coke', 'compote', 'cottage_cheese', 'croissant', 'cupcake', 'dapanji', 'doner', 'dried_apricot', 'dumpling_with_soup', 'egg', 'fanta', 'fettucini', 'fish_soup', 'french_fries', 'fresh_salad', 'fried_aubergine', 'fried_dumplings', 'fried_lagman', 'funchosa', 'golubcy', 'greek_salad', 'green_tea', 'grilled_vegetables', 'honey', 'hvorost', 'icecream', 'irimshik', 'kazy', 'kefir', 'kespe', 'ketchup', 'khachapuri', 'kirieshki_cheese', 'kirieshki_shashlyk', 'koktal', 'korean_carrot', 'kurt', 'kuyrdak', 'kymyz', 'lemonade', 'lentiil_soup', 'lime', 'lulya_kebab', 'malibu_salad', 'manpar', 'mashed_potato', 'mayonnaise', 'meat_assorty', 'meatball', 'multifruit', 'napoleon', 'naryn', 'nauryz_koje', 'nuggets', 'okroshka', 'olivie_salad', 'onion', 'orama_nan', 'pahlava', 'pie', 'pirojki', 'pistachio', 'pizza', 'plov', 'pod_shuboi', 'pomergranate_juice', 'pop_corn', 'potato', 'quesadilla', 'raisins', 'ramen', 'raspberry_jam', 'rice', 'rice_porridge', 'rollton', 'salad_mushrooms', 'salmon', 'samsa', 'sandwich', 'sausage', 'sausage_in_dough', 'shashlyk_beef', 'shashlyk_chicken', 'shorpa', 'shubat', 'sirne', 'sorpa', 'spinach', 'sprite', 'syrniki', 'taba_nan', 'tea_with_milk', 'tiramisu', 'toast', 'tom_yam', 'tongue_salad', 'tuc', 'udon', 'vinegret', 'walnut', 'water', 'zhal_zhaya', 'zhent']

def preprocess_for_detector(image_bgr):
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    transform = A.Compose([
        A.Resize(height=512, width=512)
    ])
    augmented = transform(image=image_rgb)
    img = augmented['image']
    
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    
    return np.expand_dims(img, axis=0)

def preprocess_for_supernet(crop_rgb, ft, meta_features):
    transform = A.Compose([
        A.Resize(224, 224),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])
    augmented = transform(image=crop_rgb)
    img = augmented['image']
    
    img = np.transpose(img, (2, 0, 1)).astype(np.float32)
    img_tensor = np.expand_dims(img, axis=0)
    
    ft_tensor = np.array([ft], dtype=np.int64)
    
    meta_array = np.array(meta_features, dtype=np.float32)
        
    meta_norm = (meta_array - META_MEAN) / META_STD
    meta_tensor = np.expand_dims(meta_norm, axis=0)
    
    return img_tensor, ft_tensor, meta_tensor

def to_norm_xyxy(x1, y1, x2, y2, h, w, ht, wt):
    x_min_new = int(x1 * (w / wt))
    y_min_new = int(y1 * (h / ht))

    x_max_new = int(x2 * (w / wt))
    y_max_new = int(y2 * (h / ht))
    return x_min_new, y_min_new, x_max_new, y_max_new


def safe_crop(image, bbox):
    x1, y1, x2, y2 = map(int, bbox.tolist())
    h, w = image.shape[:2]
    
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)
    
    return image[y1:y2, x1:x2]

def get_features(img: np.array):
    width, height = img.shape[:2]
    image_area = width * height
    aspect_ratio = width / height
    api = np.mean(img)

    return image_area, aspect_ratio, api

def get_density(ft):
    return density_indices[ft]

def get_classes(ft):
    return classes[ft]