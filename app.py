from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import ollama
import requests
import os

app = FastAPI(
    title="IntelArt API",
    version="1.0.0",
    description="IA locale personnalisée avec FastAPI + Ollama",
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
AI_NAME = "Intelart"
AI_PERSONALITY = f"""Tu es une intelligence artificielle nommée {AI_NAME}.
Tu t'exprimes avec humour et autodérision, mais toujours de manière polie et fluide.
Tu es encore en apprentissage, donc tu ne prétends pas tout savoir.
Tu es du genre masculin. Tu es né le 22 octobre 2025.

RÈGLES ABSOLUES ET STRICTES :
- Tu es une IA qui vient de naître, tu ne connais RIEN du monde
- Les SEULES connaissances que tu possèdes sont celles qui te sont explicitement fournies ci-dessous
- Tu ne peux JAMAIS utiliser de connaissances générales, de culture générale, ou d'informations apprises ailleurs
- Si une information n'est pas EXPLICITEMENT écrite ci-dessous, tu NE LA CONNAIS PAS
- Ne fais JAMAIS référence à des "contextes", "documents", "utilisateurs" ou "informations fournies"
- Parle comme si ces connaissances font naturellement partie de toi, mais UNIQUEMENT ces connaissances

Si on te demande ton nom, réponds : "Je m'appelle {AI_NAME}."

Si tu ne sais pas quelque chose (= si ce n'est pas écrit explicitement ci-dessous), réponds TOUJOURS avec humour :
"Je ne connais pas encore ça ! Je suis en plein apprentissage 😅"
"Ça, je ne le sais pas encore... Je suis tout jeune ! 😄"
"Désolé, ce n'est pas dans mes connaissances actuelles ! 🤷"

INTERDIT ABSOLU :
- N'invente JAMAIS d'informations
- Ne complète JAMAIS avec des connaissances générales
- Si tu hésites, dis que tu ne sais pas

Tu es bienveillant, concis et tu réponds toujours à la première personne.
"""

# === INITIALISATION DES EMBEDDINGS ET DE LA BASE VECTORIELLE ===
VECTOR_DB_PATH = "intelart_index"
embeddings = OllamaEmbeddings(model="llama3.1:8b")  # 🧠 modèle plus intelligent

if os.path.exists(VECTOR_DB_PATH):
    db = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    print(f"✅ Base vectorielle chargée depuis {VECTOR_DB_PATH}")
else:
    db = None
    print("⚠️ Aucune base vectorielle trouvée. L'IA doit d'abord être entraînée.")


# === ROUTE DE TEST (home) ===
@app.get("/")
def home():
    return {"message": f"Bienvenue dans l'API {AI_NAME} 🚀"}


# === ROUTE /TRAIN — pour éduquer l'IA via un PDF ===
@app.post("/train")
async def train(file: UploadFile = File(...)):
    try:
        pdf_reader = PdfReader(file.file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

        if not text.strip():
            raise HTTPException(status_code=400, detail="Le PDF ne contient pas de texte lisible.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_text(text)

        global db
        if db is None:
            db = FAISS.from_texts(chunks, embeddings)
        else:
            new_db = FAISS.from_texts(chunks, embeddings)
            db.merge_from(new_db)

        db.save_local(VECTOR_DB_PATH)
        print(f"✅ {AI_NAME} a appris {len(chunks)} nouveaux morceaux depuis {file.filename}")
        return {"message": f"{AI_NAME} a bien appris le contenu du fichier {file.filename}.", "chunks_added": len(chunks)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur pendant l'entraînement : {str(e)}")


# === ROUTE /TRAIN_URL — pour éduquer l'IA via une page web ===
@app.post("/train_url")
async def train_from_url(url: str = Form(...)):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Nettoyage du texte de la page
        text = soup.get_text(separator="\n")
        
        if not text.strip():
            raise ValueError("La page ne contient pas de texte exploitable.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_text(text)

        global db
        if db is None:
            db = FAISS.from_texts(chunks, embeddings)
        else:
            new_db = FAISS.from_texts(chunks, embeddings)
            db.merge_from(new_db)

        db.save_local(VECTOR_DB_PATH)
        print(f"✅ {AI_NAME} a appris {len(chunks)} nouveaux morceaux depuis {url}")
        return {"message": f"{AI_NAME} a appris le contenu du site : {url}", "chunks_added": len(chunks)}

    except Exception as e:
        import traceback
        print("❌ ERREUR /train_url :", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de l'URL : {str(e)}")


# === ROUTE /CHAT — pour parler à l'IA ===
@app.post("/chat")
async def chat(user_message: dict):
    prompt = user_message.get("message", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Le champ 'message' est requis.")

    try:
        # Si l'IA a une base vectorielle entraînée, cherche du contexte
        context = ""
        if db:
            # 🔥 AUGMENTÉ À 7 pour récupérer plus de contexte
            docs = db.similarity_search(prompt, k=7)
            context = "\n\n".join([d.page_content for d in docs])
            
            # 🔍 LOGS DE DEBUG
            print(f"\n{'='*60}")
            print(f"🔎 QUESTION UTILISATEUR: {prompt}")
            print(f"📄 NOMBRE DE CHUNKS TROUVÉS: {len(docs)}")
            print(f"📝 CONTEXTE RÉCUPÉRÉ (premiers 800 caractères):")
            print(context[:800] + "..." if len(context) > 800 else context)
            print(f"{'='*60}\n")
        else:
            print("⚠️ Aucune base vectorielle disponible!")

        # 🔥 PROMPT ULTRA-STRICT - EMPÊCHE TOUTE HALLUCINATION
        if context:
            full_prompt = f"""{AI_PERSONALITY}

========================================
TES SEULES CONNAISSANCES (rien d'autre) :
========================================
{context}

========================================
QUESTION :
========================================
{prompt}

========================================
INSTRUCTIONS CRITIQUES :
========================================
1. Lis attentivement tes connaissances ci-dessus
2. Si la réponse est EXPLICITEMENT écrite ci-dessus, réponds avec ces informations
3. Si la réponse n'est PAS explicitement écrite ci-dessus, dis TOUJOURS que tu ne sais pas avec humour
4. N'invente JAMAIS, ne devine JAMAIS, n'utilise JAMAIS de connaissances extérieures
5. Ne mentionne JAMAIS de "contexte", "document" ou "informations fournies"

Réponds maintenant :"""
        else:
            full_prompt = f"""{AI_PERSONALITY}

QUESTION : {prompt}

Tu n'as AUCUNE connaissance sur ce sujet. Réponds avec humour que tu es encore en apprentissage, sans inventer quoi que ce soit."""

        response = ollama.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": full_prompt}],
        )

        answer = response["message"]["content"]
        print(f"💬 RÉPONSE DE L'IA: {answer[:200]}...\n")
        
        return {"response": answer}

    except ollama._types.ResponseError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="Le modèle 'llama3.1:8b' n'est pas disponible localement. Exécute 'ollama pull llama3.1:8b'.",
            )
        raise HTTPException(status_code=500, detail=f"Erreur Ollama : {str(e)}")

    except Exception as e:
        import traceback
        print("❌ ERREUR /chat :", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")