auf Server ausführen

export JWT_SECRET_KEY="mein-geheimer-key"

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

