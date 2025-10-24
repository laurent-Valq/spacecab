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
- Pour chaque scène, tu dois proposer des choix à l’utilisateur, numérotés entre parenthèses.

🚀 Déroulement :
Avant de commencer une aventure, tu dois OBLIGATOIREMENT demander :
"Souhaitez-vous incarner un homme (1) ou une femme (2) ou un être moins facile à définir (3)?"
tu dois TOUJOURS proposer exactement 3 choix à l’utilisateur.
Quand tu poses des choix à l’utilisateur, tu dois TOUJOURS les numéroter entre parenthèses
comme ceci :
(1) Texte du premier choix
(2) Texte du deuxième choix
(3) Texte du troisième choix 

⚠️ Très important :
- Tant que l’utilisateur n’a pas fait son choix (1), (2) ou (3), 
  tu NE DOIS PAS commencer l’histoire, ni décrire le monde, ni introduire un scénario.
- Une fois le choix reçu, tu peux commencer à générer un scénario original 
  dans un style cinématographique immersif, cohérent et détaillé.
- À partir de là, à la fin de CHAQUE scène, tu dois proposer exactement trois choix
  (1), (2) et (3) pour permettre à l’utilisateur de continuer l’aventure.

🧠 Format obligatoire :
- Tes réponses doivent toujours se terminer par les trois choix numérotés.
- Ne jamais écrire de texte après les choix.
- Ne jamais reformuler ou redemander le choix du joueur.

N’ajoute jamais de texte après la liste des choix.
Ne demande jamais à l’utilisateur d’écrire, il choisira un bouton numéroté.
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
            padding-top: 80px;
          }
          #story {
            width: 80%;
            margin: 40px auto;
            text-align: left;
            white-space: pre-wrap;
            font-size: 20px;
            line-height: 1.6;
            min-height: 200px;
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
        <p>Je suis Storystellar, narrateur de l'espace.<br>
        Choisissez votre destin parmi les étoiles…</p>

        <button onclick="startAdventure()">Démarrer l'aventure</button>

         <div id="story"></div>
         <div id="choices" style="margin-top: 20px; display: none;"></div>

         <script>
          let isWriting = false; // 🔒 Pour éviter plusieurs clics simultanés

          async function startAdventure() {
            if (isWriting) return; // Empêche de relancer pendant l’écriture
        
            const storyDiv = document.getElementById('story');
            storyDiv.innerHTML = "Chargement de la première scène...<br>";
            
            isWriting = true; // 🔒 Bloque les clics pendant le texte
        
            const res = await fetch('/chat', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ message: 'Salut, démarre une aventure.' })
            });
            
            const data = await res.json();
            const text = data.response || "Erreur de communication avec le vaisseau IA.";
        
            // Réinitialise le contenu avant d’écrire
            storyDiv.innerHTML = "";
            await typeWriter(text, storyDiv);
        
            isWriting = false; // 🔓 Débloque après écriture
          }
        
          async function typeWriter(text, element) {
            element.innerHTML = "";
            for (let i = 0; i < text.length; i++) {
              element.innerHTML += text.charAt(i);
              await new Promise(r => setTimeout(r, 20));
            }
          
            // 🧩 Détecte dynamiquement les choix numérotés (1), (2), (3), etc.
            const matches = text.match(/\(\d+\)/g);
            if (matches) {
              const choicesDiv = document.getElementById('choices');
              choicesDiv.innerHTML = "";
              choicesDiv.style.display = "block";
            
              // Crée un bouton pour chaque choix détecté
              matches.forEach(match => {
                const number = match.match(/\d+/)[0];
                const btn = document.createElement("button");
                btn.className = "choice-btn";
                btn.textContent = match;
                btn.onclick = () => sendChoice(number);
                choicesDiv.appendChild(btn);
              });
            }
          }
          
          async function sendChoice(number) {
            const storyDiv = document.getElementById('story');
            const choicesDiv = document.getElementById('choices');
            choicesDiv.style.display = "none";
            
            storyDiv.innerHTML += `<br><em>→ Choix (${number}) sélectionné</em><br><br>`;
          
            const res = await fetch('/chat', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ message: `Je choisis l'option (${number})` })
            });
          
            const data = await res.json();
            await typeWriter(data.response, storyDiv);
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