import json
import shutil

ENTITY_REGISTRY_PATH = '.storage/core.entity_registry'
BACKUP_PATH = ENTITY_REGISTRY_PATH + '.bak'
TARGET_PLATFORM = ['feeding_plc', 'pools_plc']  # укажи свою платформу, если другая

# 1. Резервное копирование
shutil.copy(ENTITY_REGISTRY_PATH, BACKUP_PATH)
print(f"Создана резервная копия: {BACKUP_PATH}")

# 2. Загрузка оригинального файла
with open(ENTITY_REGISTRY_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 3. Фильтрация сущностей
entities = data['data']['entities']
filtered = [e for e in entities if e.get('platform') not in TARGET_PLATFORM]
removed = len(entities) - len(filtered)

# 4. Сохранение обновлённого файла
data['data']['entities'] = filtered
with open(ENTITY_REGISTRY_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Удалено {removed} сущностей с platform='{TARGET_PLATFORM}'")
