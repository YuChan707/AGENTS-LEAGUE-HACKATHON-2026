# 1. Usamos una sola imagen base oficial de Python (más ligera y directa)
FROM python:3-slim

# 2. Definimos el directorio de trabajo DENTRO del contenedor
WORKDIR /app

# 3. Copiamos el archivo de dependencias e instalamos
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos todo el contenido del directorio actual al contenedor
COPY . .

# 5. El archivo .env se copiará desde la misma carpeta (ver explicación abajo)
COPY .env ./

# 6. Comando para ejecutar la app
CMD [ "python", "./main.py" ]