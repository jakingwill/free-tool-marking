from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import openai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

class MarkingRequest(BaseModel):
    question: str
    totalMarks: str
    studentAnswer: str
    markingGuide: str

@app.post("/api/mark")
async def mark_answer(request: MarkingRequest):
    try:
        # Convert marking guide to list
        marking_points = [
            point.strip() 
            for point in request.markingGuide.split('\n') 
            if point.strip()
        ]
        total_marks = float(request.totalMarks)
        points_value = total_marks / len(marking_points)

        # Construct prompt for GPT-4
        prompt = f"""
        Question: {request.question}
        
        Marking Guide Points (each worth {points_value:.1f} marks):
        {request.markingGuide}
        
        Student Answer:
        {request.studentAnswer}
        
        Please analyze the student's answer against each marking guide point and provide:
        1. Whether each point was addressed (YES/NO)
        2. Total marks earned
        3. Detailed feedback
        
        Format your response in JSON:
        {{
          "breakdown": [
            {{"point": "point text", "earned": true/false, "value": mark_value}},
            ...
          ],
          "mark": total_marks_earned,
          "totalMarks": total_available,
          "percentage": percentage_score,
          "feedback": "detailed feedback"
        }}
        """

        # Call OpenAI API
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert teacher marking student work. Provide detailed, constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={ "type": "json_object" }
        )

        # Extract and return the result
        result = response.choices[0].message.content
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
