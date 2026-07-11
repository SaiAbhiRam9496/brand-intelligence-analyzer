# ============================================================
# main.py
# FastAPI application entry point - python-engine
# Exposes API endpoints for analysis and PDF generation
# ============================================================

import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
# NOTE: orchestrator and pdf_generator are imported lazily inside endpoints
# to avoid loading heavy ML models at server startup time

app = FastAPI(
    title="Brand Intelligence Analyzer - Python Engine",
    description="Microservice for data collection, NLP analysis, and PDF generation.",
    version="1.0"
)


class AnalysisRequest(BaseModel):
    brand: str


class PDFRequest(BaseModel):
    brand: str
    analysis_data: dict


@app.get("/health")
def health_check():
    """
    Service health check endpoint.
    """
    return {"status": "ok"}


@app.post("/analyze")
def analyze_brand(request: AnalysisRequest):
    """
    Runs the full scraping and NLP pipeline for a brand.
    """
    from orchestrator import run_full_analysis
    brand_name = request.brand.strip()
    if not brand_name:
        raise HTTPException(status_code=400, detail="Brand name cannot be empty.")

    try:
        results = run_full_analysis(brand_name)
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        return results
    except Exception as e:
        print(f"[API] Error running analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-pdf")
def generate_report_pdf(request: PDFRequest, background_tasks: BackgroundTasks):
    """
    Generates a 7-page PDF report using pre-computed analysis data.
    Streamed back as a FileResponse, and deleted after sending.
    """
    from report.pdf_generator import generate_pdf_report
    brand_name = request.brand.strip()
    if not brand_name:
        raise HTTPException(status_code=400, detail="Brand name cannot be empty.")

    # Create a unique temporary filename
    temp_pdf_path = f"temp_report_{brand_name}_{int(os.getpid())}.pdf"

    try:
        data = request.analysis_data
        generate_pdf_report(
            brand=brand_name,
            output_path=temp_pdf_path,
            sentiment_summary=data.get("sentiment_summary", {}),
            strategy_report=data.get("strategy_report", {}),
            tone_result=data.get("tone_result", {}),
            wiki_data=data.get("wiki_data", {}),
            issues=data.get("issues", [])
        )

        if not os.path.exists(temp_pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed.")

        # Cleanup the file after sending
        background_tasks.add_task(os.remove, temp_pdf_path)

        return FileResponse(
            temp_pdf_path,
            media_type="application/pdf",
            filename=f"{brand_name}_Brand_Report.pdf"
        )
    except Exception as e:
        print(f"[API] Error generating PDF: {e}")
        # Clean up in case of failure before response
        if os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Run server locally on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)