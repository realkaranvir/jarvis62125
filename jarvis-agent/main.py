import asyncio
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from agentworkflow import general_workflow
from agents import RunResult

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/query")
async def query(query: str = Form(...), session_id: str = Form(...)):
    result: RunResult = await general_workflow.run_workflow(query, session_id)
    result_obj = {
        "response":{
            "query": query,
            "history": [], # TODO: implement sessions,
            "LLM_response": result.final_output_as(str),
        }
    }
    return JSONResponse(content=result_obj)