# StudyPal — application image
# Uses PyMySQL (pure Python DB driver), so no libmysqlclient/gcc build
# toolchain is needed — cryptography and everything else ship prebuilt
# manylinux wheels for this base image.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Wait for the DB, then run migrations-equivalent (create_all) and start.
CMD ["sh", "-c", "python wait_for_db.py && python run.py"]
