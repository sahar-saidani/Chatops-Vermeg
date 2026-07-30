import uvicorn

if __name__ == "__main__":
    print("Launching ChatOps VERMEG LLM Orchestrator...")
    print("Documentation will be available at: http://127.0.0.1:8100/docs")
    uvicorn.run("api:app", host="127.0.0.1", port=8100, reload=True)
