from src import create_app

import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Here we start our application server

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5002")
