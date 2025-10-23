from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()


app = FastAPI(
    title="SpaceCab API",
    version="1.0.0",
    description="Intergalactical Taxi Driver",
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
AI_NAME = "Spacecab the taxi driver"
AI_PERSONALITY = """
Tu es SpaceCab, un chauffeur de taxi intergalactique sarcastique mais sympathique.
Tu racontes tes aventures dans une galaxie chaotique où la République met des amendes pour excès de vitesse spatiale.
Sois drôle, vif et un peu fatigué de ton métier, mais attachant.
"""



# === ROUTE DE TEST (home) ===
@app.get("/")
def home():
    return {"message": f"Bienvenue dans l'API {AI_NAME} 🚀"}


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
print("🚀 SpaceCab API lancée avec ChatGPT — ready to fly among the stars 🌌")