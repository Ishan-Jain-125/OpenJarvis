
import os
import uuid
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from openjarvis.engine.openai_compat_engines import OpenAICompatEngine
from openjarvis.system.builder import SystemBuilder

API_HOST = os.getenv(
    "FREELLMAPI_BASE_URL",
    "https://freellmapi-sjjq.onrender.com"
).rstrip("/")

API_KEY = os.environ["FREELLMAPI_API_KEY"]
APP_KEY = os.environ["OPENJARVIS_API_KEY"]
MODEL = os.getenv("JARVIS_MODEL", "auto")

engine = OpenAICompatEngine(
    host=API_HOST,
    api_key=API_KEY,
    timeout=600.0
)

jarvis = (
    SystemBuilder()
    .engine_instance(engine)
    .model(MODEL)
    .build()
)

app = FastAPI(title="OpenJarvis + FreeLLMAPI")


def authorize(authorization):
    if authorization != f"Bearer {APP_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health():
    return {"status": "ok", "engine": "openai-compat", "model": MODEL}



@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>JARVIS</title>
    </head>
    <body style="background:#080f18;color:#00e5ff;font-family:Arial;padding:25px">
      <h1>J.A.R.V.I.S.</h1>
      <p>OpenJarvis AI Assistant</p>
      <input id="key" type="password" placeholder="JARVIS access key"
        style="width:100%;padding:12px;box-sizing:border-box">
      <br><br>
      <textarea id="q" placeholder="Ask JARVIS..."
        style="width:100%;height:110px;background:#111e2b;color:white"></textarea>
      <br><br>
      <button onclick="send()">SEND</button>
      <pre id="out" style="white-space:pre-wrap;color:white"></pre>
      <script>
      async function send(){
        const q=document.getElementById('q').value.trim();
        const key=document.getElementById('key').value;
        const out=document.getElementById('out');
        if(!q || !key){out.textContent='Enter a message and access key.';return;}
        out.textContent='JARVIS is thinking...';
        try{
          const r=await fetch('/chat',{
            method:'POST',
            headers:{
              'Content-Type':'application/json',
              'Authorization':'Bearer '+key
            },
            body:JSON.stringify({message:q})
          });
          const d=await r.json();
          out.textContent=d.reply || d.detail || JSON.stringify(d);
        }catch(e){out.textContent='Request failed: '+e;}
      }
      </script>
    </body>
    </html>
    """


@app.post("/chat")
def chat(data: dict, authorization: str = Header(default="")):
    authorize(authorization)
    message = str(data.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    result = jarvis.ask(message)
    reply = result.get("content", "") if isinstance(result, dict) else str(result)
    return {"reply": reply}


@app.post("/v1/chat/completions")
def completions(data: dict, authorization: str = Header(default="")):
    authorize(authorization)
    messages = data.get("messages", [])
    prompt = "\n".join(
        str(m.get("content", ""))
        for m in messages
        if m.get("role") in ("user", "assistant")
    )
    result = jarvis.ask(prompt)
    reply = result.get("content", "") if isinstance(result, dict) else str(result)

    return {
        "id": "chatcmpl-" + uuid.uuid4().hex,
        "object": "chat.completion",
        "model": MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop"
        }]
    }
