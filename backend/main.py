"""Compatibility entry point for hosts configured with ``uvicorn main:app``."""



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
