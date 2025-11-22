import re

def test_url_fix():
    test_cases = [
        "../../docs/AC437B34557F88EA4115D2F374B0A07B/questions/31C6B63D6C22848746013402B1A72A54(copy1)/xs3qstsrc31C6B63D6C22848746013402B1A72A54_1_1512575080.png",
        "docs/AC437B34557F88EA4115D2F374B0A07B/questions/795AF3E71A2291E8409B40134DB5B085(copy1)/xs3qstsrc164ebee2c79c41a989df535a795492eb_7_1759831280.png",
        "AC437B34557F88EA4115D2F374B0A07B/questions/D2295821B2339E5C48183A316A76652E(copy1)/xs3qstsrcD2295821B2339E5C48183A316A76652E_1_1710237026.png"
    ]
    
    for test_path in test_cases:
        relative_path = test_path
        
        # Правильное формирование пути к изображению из ShowPictureQ
        if relative_path.startswith('docs/'):
            full_url = "https://ege.fipi.ru/bank/" + relative_path
        elif relative_path.startswith('../../docs/'):
            corrected_path = relative_path[6:]  # Убираем '../../'
            full_url = "https://ege.fipi.ru/bank/" + corrected_path
        elif '/docs/' in relative_path:
            full_url = "https://ege.fipi.ru/bank/" + relative_path
        else:
            full_url = "https://ege.fipi.ru/bank/docs/" + relative_path
        
        # Убираем (copy1), (copy2) и т.д. из пути
        full_url = re.sub(r'\(copy\d+\)', '', full_url)
        
        print(f"Input: {test_path}")
        print(f"Output: {full_url}")
        print("---")

if __name__ == "__main__":
    test_url_fix()
