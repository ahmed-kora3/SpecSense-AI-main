import os

labels_path = "."

for filename in os.listdir(labels_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(labels_path, filename)

        with open(file_path, "r") as f:
            lines = f.readlines()

        new_lines = []

        for line in lines:
            line = line.strip()

            # ⛔ تجاهل السطور الفاضية
            if not line:
                continue

            parts = line.split()

            # ⛔ تأكد إن فيه بيانات
            if len(parts) < 5:
                continue

            # ✔ تعديل الكلاس
            parts[0] = "0"

            new_lines.append(" ".join(parts))

        with open(file_path, "w") as f:
            f.write("\n".join(new_lines))

print("✅ Labels fixed safely!")