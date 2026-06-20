import json
import random
from faker import Faker
from pathlib import Path

fake = Faker("en_IN")

NUM_RECORDS = 5000

# Generate unique random voter ID numbers
id_numbers = random.sample(range(100000, 999999), NUM_RECORDS)
file = Path(__file__).parent / "../voters.json"
records = []

for num in id_numbers:
    gender = random.choice(["Male", "Female"])

    if gender == "Male":
        name = fake.name_male()
    else:
        name = fake.name_female()

    record = {
        "voter_id": f"VOTER{num}",
        "name": name,
        "age": random.randint(18, 90),
        "gender": gender,
    }

    records.append(record)

# Save to JSON file
with open(file, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4, ensure_ascii=False)

print(f"Generated {NUM_RECORDS} voter records successfully!")
