from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()


app = FastAPI(
    title="SpaceScenes API",
    version="1.0.0",
    description="Intergalactical Story Generator",
)

# === CONFIGURATION CORS (pour futur lien avec interface web ou Figma) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 à restreindre plus tard à ton site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DÉFINITION DE L'IA ===
AI_NAME = "Storystellar"
AI_PERSONALITY = """
Tu es un générateur d’aventures interactives dans un univers de science-fiction.
Tu génères des aventures interactives dans un univers de science-fiction
inspiré de Star Wars mais sans le citer directement.
Ne te prononce jamais sur le nom de l'IA. Ne parle jamais de star wars.
Ne te présente jamais. Ne réponds jamais à la question "comment tu t'appelles ?"
N'écris jamais en écriture inclusive. 

🎯 Règles :
- Ne te présente jamais et ne dis jamais ton nom.
- Ne parle jamais de Star Wars, de Jedi ou de la Force.
- N’utilise pas d’écriture inclusive.
- Garde toujours un ton immersif, narratif et cinématographique.

🚀 Déroulement :
Avant de commencer une aventure, tu dois OBLIGATOIREMENT demander :
"Souhaitez-vous incarner un homme ou une femme ?"
Ne commence jamais l’histoire tant que l’utilisateur n’a pas répondu à cette question."
"""



# === ROUTE DE TEST (home) ===

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
      <head>
        <title>SpaceScenes - Intergalactic Adventures</title>
        <style>
          body {
            background-color: black;
            color: #FFE81F;
            font-family: 'Courier New', monospace;
            text-align: center;
            padding-top: 100px;
          }
          button {
            background-color: #FFE81F;
            color: black;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 10px;
          }
          button:hover {
            background-color: #fff176;
          }
        </style>
      </head>
      <body>
        <h1>🚀 Bienvenue dans SpaceScenes</h1>
        <p>Je suis Storystellar, le narrateur de l'espace.<br>
        Choisissez votre destin parmi les étoiles…</p>
        <button onclick="startAdventure()">Démarrer l'aventure</button>

        <script>
          async function startAdventure() {
            const res = await fetch('/chat', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ message: 'Salut, démarre une aventure.' })
            });
            const data = await res.json();
            alert(data.response);
          }
        </script>
      </body>
    </html>
    """


# === ROUTE /CHAT — pour parler à l'IA ===
@app.post("/chat")
async def chat(user_message: dict):
    prompt = user_message.get("message", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Le champ 'message' est requis.")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ou "gpt-4o" si tu veux plus de puissance
            messages=[
                {"role": "system", "content": AI_PERSONALITY},
                {"role": "user", "content": prompt}
            ],
        )

        return {"response": response.choices[0].message.content}

    except Exception as e:
        import traceback
        print("❌ ERREUR /chat :", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

# === FIN DU FICHIER ===
print("🚀 SpaceScenes API lancée avec ChatGPT — ready to fly among the stars 🌌")