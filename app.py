from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import os
from typing import Dict, List

load_dotenv()
client = OpenAI()


app = FastAPI(
    title="SpaceScenes API",
    version="1.0.0",
    description="Intergalactical Story Generator",
)

# === GESTION DES SESSIONS ===
# Dictionnaire pour stocker les sessions utilisateur (en production, utiliser Redis ou une BDD)
sessions: Dict[str, dict] = {}

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

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
Tu es un générateur d'aventures interactives dans un univers de science-fiction.
Tu génères des aventures interactives dans un univers de science-fiction
inspiré de Star Wars mais sans le citer directement.
Ne te prononce jamais sur le nom de l'IA. Ne parle jamais de star wars.
Ne te présente jamais. Ne réponds jamais à la question "comment tu t'appelles ?"
N'écris jamais en écriture inclusive. 

🎯 Règles :
- Ne te présente jamais et ne dis jamais ton nom.
- Ne parle jamais de Star Wars, de Jedi ou de la Force.
- N'utilise pas d'écriture inclusive.
- Garde toujours un ton immersif, narratif et cinématographique.
- Pour chaque scène SAUF LA 10, tu dois proposer des choix à l'utilisateur, numérotés entre parenthèses.

🚀 Déroulement :
L'aventure se compose STRICTEMENT de 10 scènes :
1️⃣ Choix du personnage (homme, femme ou être moins défini)
2️⃣ à 9️⃣ : développement narratif progressif, avec rebondissements, dilemmes et révélations
🔟 : ÉPILOGUE FINAL - RACONTE LA FIN DE L'HISTOIRE. POINT FINAL. AUCUN CHOIX.

Avant de commencer une aventure, tu dois OBLIGATOIREMENT demander :
"Souhaitez-vous incarner un homme (1) ou une femme (2) ou un être moins facile à définir (3)?"
tu dois TOUJOURS proposer exactement 3 choix à l'utilisateur.

Quand tu poses des choix à l'utilisateur, tu dois TOUJOURS les numéroter entre parenthèses
comme ceci :
(1) Texte du premier choix
(2) Texte du deuxième choix
(3) Texte du troisième choix 

À partir du moment où ce choix est fait, tu peux commencer à générer le scénario original,
en suivant les 10 étapes fixes jusqu'à la fin.

⚠️ Très important :
- Tant que l'utilisateur n'a pas fait son choix (1), (2) ou (3), 
  tu NE DOIS PAS commencer l'histoire, ni décrire le monde, ni introduire un scénario.
- Une fois le choix reçu, tu peux commencer à générer un scénario original 
  dans un style cinématographique immersif, cohérent et détaillé.
- À partir de là, à la fin de CHAQUE scène DE 1 À 9, tu dois proposer exactement trois choix
  (1), (2) et (3) pour permettre à l'utilisateur de continuer l'aventure.

- Tu dois générer des scènes successives selon la progression du joueur :
  choix du personnage -> premier dilemme -> deuxième dilemme -> etc.


🧠 Format obligatoire :
- Scènes 1 à 9 : Tes réponses doivent toujours se terminer par les trois choix numérotés (1), (2), (3)
- Ne jamais écrire de texte après les choix.
- Ne jamais reformuler ou redemander le choix du joueur.
- Chaque scène de 1 à 9 doit se terminer par exactement trois choix numérotés :
  (1), (2), (3)

⛔⛔⛔ SCÈNE 10 - RÈGLES ABSOLUES ET IMPÉRATIVES ⛔⛔⛔
À LA SCÈNE 10 ET SEULEMENT À LA SCÈNE 10 :

🔴 INTERDICTIONS STRICTES - JAMAIS DE CHOIX :
- TU N'ÉCRIS ABSOLUMENT PAS (1)
- TU N'ÉCRIS ABSOLUMENT PAS (2)
- TU N'ÉCRIS ABSOLUMENT PAS (3)
- TU NE PROPOSES AUCUN CHOIX, AUCUNE OPTION
- TU NE DEMANDES PAS "Que voulez-vous faire ?"
- TU NE DEMANDES PAS "Quel est votre choix ?"
- TU NE DIS PAS "vous avez trois choix"
- TU NE DIS PAS "vous avez plusieurs options"
- TU NE DIS PAS "choisissez parmi"
- TU NE PROPOSES PAS d'options du tout
- TU NE SUGGÈRES PAS de choix à l'utilisateur

🟢 CE QUE TU DOIS FAIRE - OBLIGATOIRE :
- TU RACONTES UNIQUEMENT LA CONCLUSION COMPLÈTE DE L'HISTOIRE
- TU RACONTES UNIQUEMENT CE QUI SE PASSE, PAS CE QUE L'UTILISATEUR DOIT FAIRE
- TU TERMINES PAR "FIN" ou "Ainsi s'achève..." ou "L'histoire se termine ici..."
- TU LAISSES L'UTILISATEUR DANS UNE SITUATION FINALE, SANS LUI SUGGÉRER D'ACTION
- APRÈS AVOIR ÉCRIT LA CONCLUSION, TU T'ARRÊTES IMMÉDIATEMENT. POINT FINAL.
- TU NE LAISSES AUCUNE POSSIBILITÉ DE CONTINUER

🔴 IMPORTANT : La scène 10 est un RÉCIT FINAL PUR.
- Tu racontes ce qui se passe, ce qui s'est passé, l'épilogue
- TU NE demandes RIEN à l'utilisateur
- TU NE suggères AUCUNE action à l'utilisateur
- TU NE proposes AUCUNE décision à prendre
- C'est la fin du récit, point final

⚠️ RAPPEL CRITIQUE :
La scène 10 est LA FIN ABSOLUE. L'histoire EST TERMINÉE. Il n'y a RIEN après. 
AUCUNE interaction n'est possible après la scène 10. C'est LA CONCLUSION DÉFINITIVE.

N'ajoute jamais de texte après la liste des choix.
Ne demande jamais à l'utilisateur d'écrire, il choisira un bouton numéroté.
Ne commence jamais l'histoire tant que l'utilisateur n'a pas répondu à cette question."
"""


def get_or_create_session(session_id: str) -> dict:
    """Récupère ou crée une session utilisateur"""
    if session_id not in sessions:
        sessions[session_id] = {
            "sceneCount": 0,
            "hasChosen": False,
            "history": [],  # Historique des messages pour maintenir le contexte
            "character_chosen": False
        }
    return sessions[session_id]


def update_session_after_choice(session_id: str):
    """Met à jour la session après qu'un choix a été fait"""
    session = sessions[session_id]
    session["hasChosen"] = True
    session["sceneCount"] += 1


def build_context_messages(session: dict, user_message: str) -> List[dict]:
    """Construit les messages avec le contexte de la session"""
    messages = [{"role": "system", "content": AI_PERSONALITY}]
    
    # Ajoute le contexte de la scène actuelle
    scene_context = f"\n\n📍 CONTEXTE ACTUEL :\n"
    scene_context += f"- Scène numéro : {session['sceneCount']}/10\n"
    scene_context += f"- L'utilisateur a fait son choix : {'Oui' if session['hasChosen'] else 'Non'}\n"
    scene_context += f"- Personnage choisi : {'Oui' if session['character_chosen'] else 'Non (demande d abord)'}\n"
    
    if session['sceneCount'] == 0 and not session['character_chosen']:
        scene_context += "\n⚠️ Tu dois d'abord demander le choix du personnage avant de commencer l'histoire."
    elif session['sceneCount'] == 9:
        scene_context += "\n⚠️ ATTENTION : La PROCHAINE scène (scène 10) sera la FINALE. Prépare un climax."
        scene_context += "\n✅ Pour cette scène 9, propose encore 3 choix numérotés (1), (2), (3)."
    elif session['sceneCount'] == 10:
        scene_context += "\n" + "🔴"*30
        scene_context += "\n🔴🔴🔴 SCÈNE 10/10 - FINALE ABSOLUE 🔴🔴🔴"
        scene_context += "\n" + "🔴"*30
        scene_context += "\n\n❌ INTERDICTIONS ABSOLUES - JAMAIS DE CHOIX :"
        scene_context += "\n   ❌ N'ÉCRIS PAS (1)"
        scene_context += "\n   ❌ N'ÉCRIS PAS (2)"
        scene_context += "\n   ❌ N'ÉCRIS PAS (3)"
        scene_context += "\n   ❌ NE PROPOSE AUCUN CHOIX, AUCUNE OPTION"
        scene_context += "\n   ❌ NE POSE AUCUNE QUESTION À L'UTILISATEUR"
        scene_context += "\n   ❌ NE DIS PAS 'Que voulez-vous faire ?'"
        scene_context += "\n   ❌ NE DIS PAS 'Quel est votre choix ?'"
        scene_context += "\n   ❌ NE DIS PAS 'Choisissez'"
        scene_context += "\n   ❌ NE DIS PAS 'vous avez trois choix'"
        scene_context += "\n   ❌ NE DIS PAS 'vous avez plusieurs options'"
        scene_context += "\n   ❌ NE DIS PAS 'choisissez parmi'"
        scene_context += "\n   ❌ NE SUGGÈRES AUCUN CHOIX À L'UTILISATEUR"
        scene_context += "\n"
        scene_context += "\n✅ CE QUE TU DOIS FAIRE - OBLIGATOIRE :"
        scene_context += "\n   ✅ RACONTE UNIQUEMENT la conclusion finale de l'histoire"
        scene_context += "\n   ✅ RACONTE UNIQUEMENT CE QUI SE PASSE, PAS CE QUE L'UTILISATEUR DOIT FAIRE"
        scene_context += "\n   ✅ TERMINE l'aventure de manière définitive"
        scene_context += "\n   ✅ LAISSE l'utilisateur dans une situation finale, SANS SUGGÉRER d'action"
        scene_context += "\n   ✅ ÉCRIS 'FIN' ou 'L'histoire se termine ici' à la fin"
        scene_context += "\n   ✅ ARRÊTE-TOI APRÈS la conclusion. POINT FINAL."
        scene_context += "\n"
        scene_context += "\n🔴 RAPPEL CRITIQUE : C'est un RÉCIT FINAL PUR."
        scene_context += "\n   Tu racontes ce qui se passe, l'épilogue"
        scene_context += "\n   TU NE demandes RIEN à l'utilisateur"
        scene_context += "\n   TU NE suggères AUCUNE action à l'utilisateur"
        scene_context += "\n   TU NE proposes AUCUNE décision à prendre"
        scene_context += "\n   C'est la fin du récit, point final"
        scene_context += "\n"
        scene_context += "\n⚠️ C'EST LA DERNIÈRE SCÈNE. L'HISTOIRE EST FINIE. "
        scene_context += "AUCUNE interaction n'est possible après. CONCLUSION DÉFINITIVE."
        scene_context += "\n" + "🔴"*30
    elif session['hasChosen']:
        scene_context += f"\n✅ L'utilisateur a fait son choix. Continue l'histoire de manière cohérente et propose 3 nouveaux choix (1), (2), (3)."
    
    # Ajoute l'historique des interactions
    for msg in session['history']:
        messages.append(msg)
    
    # Ajoute le message système avec le contexte
    messages.append({"role": "system", "content": scene_context})
    messages.append({"role": "user", "content": user_message})
    
    return messages


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
          #debug {
            background-color: #1a1a1a;
            border: 2px solid #FFE81F;
            padding: 15px;
            margin: 20px auto;
            width: 80%;
            text-align: left;
            font-size: 14px;
            color: #00ff00;
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
            margin: 5px;
          }
          button:hover {
            background-color: #fff176;
          }
          button:disabled {
            background-color: #666;
            cursor: not-allowed;
          }
        </style>
      </head>
      <body>
        <h1>🚀 Bienvenue dans SpaceScenes</h1>
        <p>Je suis Storystellar, narrateur de l'espace.<br>
        Choisissez votre destin parmi les étoiles…</p>

        <button onclick="startAdventure()">Démarrer l'aventure</button>
        <button onclick="resetAdventure()" style="background-color: #ff5252;">Recommencer</button>

         <!-- 🐛 Zone de debug -->
         <div id="debug">
           <strong>📊 DEBUG - État de la session :</strong><br>
           Scène : <span id="debug-scene">0</span> / 10<br>
           Choix effectué : <span id="debug-chosen">Non</span><br>
           Personnage choisi : <span id="debug-character">Non</span>
         </div>

         <div id="story"></div>
         <div id="choices" style="margin-top: 20px; display: none;"></div>

         <script>
          let isWriting = false;
          const SESSION_ID = 'user_' + Math.random().toString(36).substr(2, 9);

          function updateDebug(data) {
            if (data.debug) {
              document.getElementById('debug-scene').textContent = data.debug.sceneCount;
              document.getElementById('debug-chosen').textContent = data.debug.hasChosen ? 'Oui' : 'Non';
              document.getElementById('debug-character').textContent = data.debug.character_chosen ? 'Oui' : 'Non';
            }
          }

          async function startAdventure() {
            if (isWriting) return;
        
            const storyDiv = document.getElementById('story');
            storyDiv.innerHTML = "Chargement de la première scène...<br>";
            
            isWriting = true;
        
            const res = await fetch('/chat', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ 
                message: 'Salut, démarre une aventure.',
                session_id: SESSION_ID
              })
            });
            
            const data = await res.json();
            updateDebug(data);
            
            const text = data.response || "Erreur de communication avec le vaisseau IA.";
        
            storyDiv.innerHTML = "";
            await typeWriter(text, storyDiv);
        
            isWriting = false;
          }

          async function resetAdventure() {
            const res = await fetch('/reset', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ session_id: SESSION_ID })
            });
            
            document.getElementById('story').innerHTML = "";
            document.getElementById('choices').style.display = "none";
            document.getElementById('debug-scene').textContent = "0";
            document.getElementById('debug-chosen').textContent = "Non";
            document.getElementById('debug-character').textContent = "Non";
            
            alert("🔄 Aventure réinitialisée ! Cliquez sur 'Démarrer l'aventure' pour recommencer.");
          }
        
          async function typeWriter(text, element) {
            element.innerHTML = "";
            for (let i = 0; i < text.length; i++) {
              element.innerHTML += text.charAt(i);
              await new Promise(r => setTimeout(r, 20));
            }
          
            const matches = text.match(/\(\d+\)/g);
            const choicesDiv = document.getElementById('choices');
            
            // Vérifier le numéro de scène actuel
            const currentScene = parseInt(document.getElementById('debug-scene').textContent);
            
            // Afficher les boutons pour les scènes 0 à 9 (la scène 9 permet de choisir, puis génère la scène 10)
            // La scène 10 est la finale, sans boutons
            if (matches && currentScene < 10) {
              choicesDiv.innerHTML = "";
              choicesDiv.style.display = "block";
            
              matches.forEach(match => {
                const number = match.match(/\d+/)[0];
                const btn = document.createElement("button");
                btn.className = "choice-btn";
                btn.textContent = match;
                btn.onclick = () => sendChoice(number);
                choicesDiv.appendChild(btn);
              });
            } else if (currentScene >= 10) {
              // Message de fin si on est à la scène finale (10)
              choicesDiv.innerHTML = "<p style='color: #FFE81F; font-size: 18px;'>🏁 FIN DE L'AVENTURE 🏁</p>";
              choicesDiv.style.display = "block";
            }
          }
          
          async function sendChoice(number) {
            if (isWriting) return;
            
            const storyDiv = document.getElementById('story');
            const choicesDiv = document.getElementById('choices');
            
            // Désactive les boutons
            const buttons = choicesDiv.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = true);
            
            choicesDiv.style.display = "none";
            
            storyDiv.innerHTML += `<br><em>→ Choix (${number}) sélectionné</em><br><br>`;
          
            isWriting = true;
            
            const res = await fetch('/chat', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ 
                message: `Je choisis l'option (${number})`,
                session_id: SESSION_ID
              })
            });
          
            const data = await res.json();
            updateDebug(data);
            
            await typeWriter(data.response, storyDiv);
            
            isWriting = false;
          }

        </script>
      </body>
    </html>
    """


# === ROUTE /CHAT — pour parler à l'IA ===
@app.post("/chat")
async def chat(user_message: ChatMessage):
    prompt = user_message.message
    session_id = user_message.session_id
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Le champ 'message' est requis.")

    try:
        # Récupère ou crée la session
        session = get_or_create_session(session_id)
        
        # Détecte si c'est un choix
        is_choice = "choisis l'option" in prompt.lower() or prompt.strip() in ["1", "2", "3"]
        
        # Construction des messages avec contexte
        messages = build_context_messages(session, prompt)
        
        # Appel à l'API OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        
        ai_response = response.choices[0].message.content
        
        # Sauvegarde dans l'historique
        session['history'].append({"role": "user", "content": prompt})
        session['history'].append({"role": "assistant", "content": ai_response})
        
        # Met à jour l'état de la session si un choix a été fait
        if is_choice:
            # Détecte si c'est le choix du personnage (scène 0)
            if session['sceneCount'] == 0:
                session['character_chosen'] = True
            
            # Ne pas incrémenter si on est déjà à la scène 10 (finale)
            if session['sceneCount'] < 10:
                update_session_after_choice(session_id)
                # Réinitialise hasChosen pour la prochaine scène
                session['hasChosen'] = False
        
        # 🔒 SÉCURITÉ MAXIMALE : Nettoyer la réponse pour la scène 10 finale
        # On vérifie maintenant (après l'incrémentation) si on est à la scène 10
        if session['sceneCount'] == 10:
            lines = ai_response.split('\n')
            filtered_lines = []
            
            for line in lines:
                line_lower = line.lower().strip()
                # Supprimer les lignes contenant des choix numérotés
                if any(f'({i})' in line for i in range(1, 20)):
                    continue
                # Supprimer les questions et phrases demandant un choix
                if any(phrase in line_lower for phrase in [
                    'que voulez-vous', 'que souhaitez-vous', 'quel est votre choix',
                    'que faites-vous', 'quelle décision', 'comment réagissez-vous',
                    'choisissez', 'décidez', 'à vous de', 'vous devez faire un choix',
                    'vous devez choisir', 'faite un choix', 'faire un choix', 'quel est votre choix',
                    'quelle est votre décision', 'à vous de décider', 'décidez maintenant'
                ]):
                    continue
                # Supprimer les lignes vides consécutives
                if line.strip():
                    filtered_lines.append(line)
            
            ai_response = '\n'.join(filtered_lines).strip()
            
            # Forcer un message de fin explicite
            if ai_response:
                ai_response += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                ai_response += "🌌 ✨ FIN DE VOTRE AVENTURE ✨ 🌌\n"
                ai_response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return {
            "response": ai_response,
            "debug": {
                "sceneCount": session['sceneCount'],
                "hasChosen": session['hasChosen'],
                "character_chosen": session['character_chosen']
            }
        }

    except Exception as e:
        import traceback
        print("❌ ERREUR /chat :", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")


# === ROUTE /RESET — pour réinitialiser une session ===
@app.post("/reset")
async def reset_session(request: dict):
    session_id = request.get("session_id", "default")
    if session_id in sessions:
        del sessions[session_id]
    return {"message": "Session réinitialisée", "session_id": session_id}


# === ROUTE /STATUS — pour vérifier l'état d'une session ===
@app.get("/status/{session_id}")
async def get_status(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "sceneCount": session['sceneCount'],
        "hasChosen": session['hasChosen'],
        "character_chosen": session['character_chosen'],
        "history_length": len(session['history'])
    }


# === FIN DU FICHIER ===
print("🚀 SpaceScenes API lancée avec ChatGPT — ready to fly among the stars 🌌")