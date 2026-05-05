from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import sqlite3
import random
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# DB CONFIG
DB_NAME = "../congolang_pan_congo.db"

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="CongoLang Pan-Congo API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/health")
def health_check():
    return {"status": "ACTIVE", "region": "PAN_CONGO"}

@app.get("/records/random")
def get_random_record(language_code: str = "lin", db: sqlite3.Connection = Depends(get_db)):
    """Fetches a random unverified record for swiping."""
    cursor = db.cursor()
    # Using the optimized index for fast random selection
    cursor.execute('''
        SELECT id, language_code, region_target, normalized_text, register_type 
        FROM records 
        WHERE language_code = ? AND status = 'UNVERIFIED'
        ORDER BY RANDOM() LIMIT 1
    ''', (language_code,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No unverified records found for this language.")
    return dict(row)

@app.post("/vote")
@limiter.limit("60/minute")
async def register_vote(request: Request, user_id: int, record_id: int, action: str, db: sqlite3.Connection = Depends(get_db)):
    """
    Registers a swipe vote with expert weighting.
    Right (+1), Left (-1), Up (+2).
    Trust score > 95.0 = 3x weight (Expert).
    """
    cursor = db.cursor()
    
    # 1. Fetch User Trust Score
    cursor.execute("SELECT trust_score FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    trust_score = user['trust_score']
    
    # 2. Determine Action Score
    base_score = 1
    if action == "LEFT":
        base_score = -1
    elif action == "UP":
        base_score = 2
    
    # 3. Apply Expert Weighting
    weight = 1
    if trust_score > 95.0:
        weight = 3
    
    final_weighted_score = base_score * weight
    
    # 4. Insert Vote
    cursor.execute('''
        INSERT INTO votes (user_id, record_id, swipe_action, weighted_score)
        VALUES (?, ?, ?, ?)
    ''', (user_id, record_id, action, final_weighted_score))
    
    # 5. Update Record net_votes
    cursor.execute('''
        UPDATE records 
        SET net_votes = net_votes + ? 
        WHERE id = ?
    ''', (final_weighted_score, record_id))
    
    db.commit()
    return {"status": "VOTE_REGISTERED", "weighted_score": final_weighted_score}

@app.get("/profile/{username}")
def get_profile(username: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, username, trust_score, xp_points FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return dict(row)
