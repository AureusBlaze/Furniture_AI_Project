import clip
import torch
from PIL import Image
import numpy as np
import os
from sklearn.cluster import MiniBatchKMeans

class ImageAnalyzer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "ViT-L-14.pt")
        self.model, self.preprocess = clip.load(model_path, device=self.device)
        self._init_descriptors()

    def _init_descriptors(self):
        self.room_type_descriptors = [
            "a living room with sofa and coffee table",
            "a bedroom with bed and nightstands",
            "a dining room with table and chairs",
            "a kitchen with cabinets and countertops",
            "a home office with desk and chair",
            "a bathroom with bathtub and sink",
            "a hallway or entryway",
            "a children's room or nursery",
            "a study room with bookshelves",
            "an outdoor patio or terrace"
        ]

        self.style_descriptors = [
            "modern minimalist interior with clean lines and simple furniture",
            "classic traditional interior with ornate details and rich wood",
            "rustic farmhouse interior with natural wood and vintage decor",
            "industrial loft interior with exposed brick and metal elements",
            "bohemian eclectic interior with colorful patterns and textures",
            "scandinavian interior with light wood and white walls",
            "mid-century modern interior with retro furniture and warm tones",
            "contemporary luxury interior with elegant materials and sleek design",
            "coastal beach house interior with blue accents and natural materials",
            "art deco interior with geometric patterns and gold accents",
            "japanese zen interior with minimal furniture and natural elements",
            "mediterranean interior with warm colors and terracotta elements",
            "country cottage interior with floral patterns and cozy furniture",
            "urban modern interior with concrete and glass elements",
            "transitional interior blending traditional and contemporary styles"
        ]

        self.color_palette_descriptors = [
            "warm room with red orange yellow and earth tones",
            "cool room with blue green purple and teal tones",
            "neutral room with white beige cream and gray tones",
            "dark moody room with black charcoal and deep colors",
            "bright airy room with white light gray and pastel colors",
            "earth tone room with brown terracotta olive and tan",
            "monochromatic room with varying shades of one color",
            "bold colorful room with vibrant contrasting colors",
            "muted soft room with dusty rose sage and lavender",
            "natural room with wood tones green and organic colors"
        ]

        self.lighting_descriptors = [
            "bright naturally lit room with large windows and sunlight",
            "dimly lit cozy room with warm ambient lighting",
            "dramatically lit room with spotlights and shadows",
            "soft diffused lighting room with gentle glow",
            "warm golden hour lighting in the room",
            "cool blue-toned lighting in the room",
            "evenly lit room with uniform artificial lighting",
            "moody atmospheric room with low light and candles",
            "bright white fluorescent lighting in the room",
            "romantic dim lighting with table lamps"
        ]

        self.space_descriptors = [
            "small compact cozy room with limited space",
            "medium sized comfortable room",
            "large spacious open room with high ceilings",
            "open plan room flowing into other areas",
            "narrow long corridor-like room",
            "square proportional balanced room",
            "L-shaped room with distinct areas",
            "loft room with exposed ceiling and open space",
            "cramped cluttered room with many items",
            "minimalist empty room with lots of negative space"
        ]

        self.material_descriptors = [
            "wooden room with natural wood grain textures",
            "metal room with steel iron and chrome surfaces",
            "glass room with transparent reflective surfaces",
            "fabric room with soft textiles and upholstered furniture",
            "stone room with marble granite and natural stone",
            "leather room with leather furniture and surfaces",
            "ceramic room with tiles and pottery elements",
            "concrete room with raw industrial concrete surfaces",
            "velvet room with plush soft velvet textures",
            "rattan and wicker room with woven natural materials"
        ]

        self.mood_descriptors = [
            "calm peaceful relaxing serene room",
            "energetic vibrant dynamic lively room",
            "cozy warm comfortable inviting room",
            "elegant sophisticated refined luxurious room",
            "playful fun whimsical cheerful room",
            "serious formal professional corporate room",
            "romantic intimate sensual warm room",
            "fresh clean crisp modern room",
            "dramatic bold intense striking room",
            "natural organic earthy grounded room"
        ]

        self.furniture_present_descriptors = [
            "room with sofa or couch",
            "room with armchair or accent chair",
            "room with coffee table",
            "room with dining table",
            "room with bed",
            "room with bookshelf or shelving",
            "room with desk or workspace",
            "room with TV or entertainment unit",
            "room with rug or carpet on floor",
            "room with plants or greenery",
            "room with curtains or drapes",
            "room with lamps or lighting fixtures",
            "room with artwork or wall decor",
            "room with mirror",
            "room with cabinet or storage"
        ]

    def encode_descriptors(self, descriptors):
        tokens = clip.tokenize(descriptors, truncate=True).to(self.device)
        with torch.no_grad():
            features = self.model.encode_text(tokens)
        return features / features.norm(dim=-1, keepdim=True)

    def analyze_with_clip(self, image_features, descriptors, top_k=3):
        text_features = self.encode_descriptors(descriptors)
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        values, indices = similarity[0].topk(top_k)

        matches = []
        for i in range(top_k):
            matches.append({
                "label": descriptors[indices[i]],
                "confidence": round(values[i].item(), 4)
            })
        return matches

    def extract_dominant_colors(self, image_path, n_colors=8):
        img = Image.open(image_path).convert("RGB")
        img_small = img.resize((200, 200))
        pixels = np.array(img_small).reshape(-1, 3)

        brightness = np.mean(pixels, axis=1)
        mask = (brightness > 20) & (brightness < 240)
        filtered_pixels = pixels[mask]

        if len(filtered_pixels) < 100:
            filtered_pixels = pixels

        kmeans = MiniBatchKMeans(n_clusters=n_colors, random_state=42, n_init=3)
        kmeans.fit(filtered_pixels)

        colors = kmeans.cluster_centers_.astype(int)
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        percentages = (counts / counts.sum() * 100).round(1)

        sorted_indices = np.argsort(-percentages)
        colors = colors[sorted_indices]
        percentages = percentages[sorted_indices]

        dominant_colors = []
        for i in range(n_colors):
            r, g, b = int(colors[i][0]), int(colors[i][1]), int(colors[i][2])
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            color_name = self.get_precise_color_name(r, g, b)
            color_category = self.get_color_category(r, g, b)

            dominant_colors.append({
                "rgb": [r, g, b],
                "hex": hex_color,
                "name": color_name,
                "category": color_category,
                "percentage": float(percentages[i])
            })

        warm_score = 0
        cool_score = 0
        for color in dominant_colors:
            if color["category"] in ["warm", "red", "orange", "yellow", "brown"]:
                warm_score += color["percentage"]
            elif color["category"] in ["cool", "blue", "green", "cyan", "purple"]:
                cool_score += color["percentage"]

        if warm_score > cool_score + 15:
            color_temperature = "warm"
        elif cool_score > warm_score + 15:
            color_temperature = "cool"
        else:
            color_temperature = "neutral"

        return {
            "colors": dominant_colors,
            "temperature": color_temperature,
            "warm_score": round(warm_score, 1),
            "cool_score": round(cool_score, 1),
            "saturation": self.calculate_saturation(dominant_colors),
            "brightness_level": self.calculate_brightness_level(dominant_colors)
        }

    def get_precise_color_name(self, r, g, b):
        h, s, v = self.rgb_to_hsv(r, g, b)

        if s < 10:
            if v < 30:
                return "black"
            if v < 60:
                return "charcoal"
            if v < 100:
                return "dark grey"
            if v < 150:
                return "grey"
            if v < 190:
                return "light grey"
            if v < 230:
                return "off-white"
            return "white"

        if h < 12 or h >= 348:
            if v < 100:
                return "dark red"
            if s < 100:
                return "muted red"
            return "red"
        if 12 <= h < 25:
            if v < 100:
                return "burnt orange"
            return "orange"
        if 25 <= h < 45:
            if s < 100:
                return "golden"
            return "yellow"
        if 45 <= h < 70:
            return "lime green"
        if 70 <= h < 100:
            return "green"
        if 100 <= h < 140:
            if s < 80:
                return "sage"
            return "emerald"
        if 140 <= h < 170:
            return "teal"
        if 170 <= h < 200:
            return "cyan"
        if 200 <= h < 230:
            if v < 100:
                return "navy"
            return "blue"
        if 230 <= h < 260:
            return "indigo"
        if 260 <= h < 290:
            if s < 100:
                return "mauve"
            return "purple"
        if 290 <= h < 320:
            return "magenta"
        if 320 <= h < 348:
            if s < 100:
                return "dusty rose"
            return "pink"

        return "unknown"

    def get_color_category(self, r, g, b):
        h, s, v = self.rgb_to_hsv(r, g, b)

        if s < 15:
            return "neutral"
        if h < 50 or h >= 340:
            return "warm"
        if 50 <= h < 160:
            return "cool"
        if 160 <= h < 260:
            return "cool"
        if 260 <= h < 340:
            return "cool"
        return "neutral"

    def rgb_to_hsv(self, r, g, b):
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        diff = mx - mn

        if diff == 0:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        s = 0 if mx == 0 else (diff / mx) * 100
        v = mx * 100

        return h, s, v

    def calculate_saturation(self, colors):
        total_sat = 0
        total_weight = 0
        for color in colors:
            r, g, b = color["rgb"]
            _, s, _ = self.rgb_to_hsv(r, g, b)
            total_sat += s * color["percentage"]
            total_weight += color["percentage"]

        avg_sat = total_sat / total_weight if total_weight > 0 else 0

        if avg_sat < 15:
            return "desaturated"
        if avg_sat < 40:
            return "muted"
        if avg_sat < 70:
            return "moderate"
        return "vibrant"

    def calculate_brightness_level(self, colors):
        total_bright = 0
        total_weight = 0
        for color in colors:
            r, g, b = color["rgb"]
            _, _, v = self.rgb_to_hsv(r, g, b)
            total_bright += v * color["percentage"]
            total_weight += color["percentage"]

        avg_bright = total_bright / total_weight if total_weight > 0 else 50

        if avg_bright < 25:
            return "very dark"
        if avg_bright < 45:
            return "dark"
        if avg_bright < 65:
            return "medium"
        if avg_bright < 85:
            return "bright"
        return "very bright"

    def analyze_lighting(self, image_path):
        img = Image.open(image_path).convert("L")
        pixels = np.array(img).flatten()

        brightness = float(np.mean(pixels))
        contrast = float(np.std(pixels))

        if brightness < 50:
            brightness_level = "very dark"
        elif brightness < 90:
            brightness_level = "dark"
        elif brightness < 140:
            brightness_level = "medium"
        elif brightness < 190:
            brightness_level = "bright"
        else:
            brightness_level = "very bright"

        if contrast < 25:
            contrast_level = "low contrast"
        elif contrast < 50:
            contrast_level = "medium contrast"
        elif contrast < 75:
            contrast_level = "high contrast"
        else:
            contrast_level = "very high contrast"

        return {
            "brightness_value": round(brightness, 1),
            "brightness_level": brightness_level,
            "contrast_value": round(contrast, 1),
            "contrast_level": contrast_level,
            "exposure": "underexposed" if brightness < 70 else ("overexposed" if brightness > 200 else "well-exposed")
        }

    def analyze_composition(self, image_path):
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        aspect_ratio = round(w / h, 2)

        pixels = np.array(img)

        mid_h, mid_w = h // 2, w // 2
        gray = np.mean(pixels, axis=2)

        h_edges = float(np.abs(np.diff(gray, axis=1)).sum())
        v_edges = float(np.abs(np.diff(gray, axis=0)).sum())

        if h_edges > v_edges * 1.2:
            orientation = "horizontal emphasis"
        elif v_edges > h_edges * 1.2:
            orientation = "vertical emphasis"
        else:
            orientation = "balanced"

        edges_total = h_edges + v_edges
        edge_density = float(edges_total / (w * h))

        if edge_density < 8:
            complexity = "simple"
        elif edge_density < 18:
            complexity = "moderate"
        elif edge_density < 30:
            complexity = "complex"
        else:
            complexity = "very complex"

        left_half = gray[:, :mid_w]
        right_half = np.fliplr(gray[:, mid_w:mid_w*2])
        if left_half.shape == right_half.shape:
            symmetry_score = float(1 - np.mean(np.abs(left_half - right_half)) / 255)
        else:
            symmetry_score = 0.5

        return {
            "aspect_ratio": float(aspect_ratio),
            "orientation": orientation,
            "complexity": complexity,
            "symmetry_score": round(symmetry_score, 2),
            "is_symmetrical": bool(symmetry_score > 0.85)
        }

    def analyze(self, image_path):
        pil_image = Image.open(image_path).convert("RGB")
        image_tensor = self.preprocess(pil_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        results = {}

        results["room_type"] = self.analyze_with_clip(image_features, self.room_type_descriptors, 3)
        results["style"] = self.analyze_with_clip(image_features, self.style_descriptors, 5)
        results["color_palette"] = self.analyze_with_clip(image_features, self.color_palette_descriptors, 3)
        results["lighting"] = self.analyze_with_clip(image_features, self.lighting_descriptors, 3)
        results["space"] = self.analyze_with_clip(image_features, self.space_descriptors, 3)
        results["materials"] = self.analyze_with_clip(image_features, self.material_descriptors, 5)
        results["mood"] = self.analyze_with_clip(image_features, self.mood_descriptors, 3)
        results["furniture_present"] = self.analyze_with_clip(image_features, self.furniture_present_descriptors, 10)

        results["dominant_colors"] = self.extract_dominant_colors(image_path)
        results["lighting_analysis"] = self.analyze_lighting(image_path)
        results["composition"] = self.analyze_composition(image_path)

        results["summary"] = {
            "room_type": results["room_type"][0]["label"] if results["room_type"] else "unknown",
            "primary_style": results["style"][0]["label"] if results["style"] else "unknown",
            "color_temperature": results["dominant_colors"]["temperature"],
            "saturation": results["dominant_colors"]["saturation"],
            "brightness": results["lighting_analysis"]["brightness_level"],
            "mood": results["mood"][0]["label"] if results["mood"] else "unknown"
        }

        return results
