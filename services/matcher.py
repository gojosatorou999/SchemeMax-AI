import json
from services.llm import llm_client
import db

def parse_income_bracket(bracket: str) -> int:
    """Helper to convert income_bracket string to a max numerical value."""
    if not bracket:
        return None
    mapping = {
        "below_1L": 100000,
        "1L_2.5L": 250000,
        "2.5L_5L": 500000,
        "5L_8L": 800000,
        "above_8L": 10000000 # arbitrary high number
    }
    return mapping.get(bracket, None)

def match_schemes(user_id: int, situation_text: str) -> dict:
    """
    1. Load user profile
    2. Extract context via LLM
    3. Pull all schemes
    4. Hard filters (state, age, income)
    5. Rank with LLM
    6. Save situation row
    7. Return situation ID
    """
    # 1. Load user
    user = db.query("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        return None
        
    user_state = user["state"]
    user_age = user["age"]
    user_income_max = parse_income_bracket(user["income_bracket"])
    
    # 2. Extract context
    extracted_context = llm_client.extract_context(situation_text)
    
    # Merge DB profile with LLM hints if DB profile is missing info
    effective_state = user_state or extracted_context.get("state_hint")
    effective_age = user_age if user_age is not None else extracted_context.get("age_hint")
    
    full_context = {
        "user_profile": dict(user),
        "extracted_situation": extracted_context,
        "raw_text": situation_text
    }

    # 3. Pull all schemes
    all_schemes = db.query("SELECT * FROM schemes")
    
    # 4. Hard filters
    filtered_schemes = []
    for s in all_schemes:
        try:
            eligibility = json.loads(s["eligibility_json"])
        except:
            eligibility = {}
            
        # State check
        scheme_states = eligibility.get("states", [])
        if scheme_states and effective_state:
            # If the scheme specifies states, user's state must be in it
            # Normalise strings for comparison
            u_state = effective_state.lower().strip()
            if not any(st.lower().strip() == u_state for st in scheme_states):
                continue
                
        # Age check
        min_age = eligibility.get("min_age")
        max_age = eligibility.get("max_age")
        if effective_age is not None:
            try:
                eff_age_int = int(effective_age)
                if min_age is not None and eff_age_int < min_age:
                    continue
                if max_age is not None and eff_age_int > max_age:
                    continue
            except (ValueError, TypeError):
                pass
                
        # Income check (only filter out if user strictly exceeds scheme cap)
        scheme_income_cap = eligibility.get("income_max")
        if user_income_max is not None and scheme_income_cap is not None:
            # If user's max income > scheme cap, they *might* not be eligible, but to be safe we don't strictly filter
            # unless we know for sure. Let's do a soft filter: if their bracket is definitely above the cap.
            # E.g. scheme cap is 100k. User bracket is 2.5L-5L (max 500k). 
            # In our mapping, below_1L means max 1L. 1L_2.5L means min 1L. 
            if bracket := user["income_bracket"]:
                min_income_for_bracket = {
                    "below_1L": 0,
                    "1L_2.5L": 100000,
                    "2.5L_5L": 250000,
                    "5L_8L": 500000,
                    "above_8L": 800000
                }.get(bracket, 0)
                
                if min_income_for_bracket > scheme_income_cap:
                    continue
                    
        filtered_schemes.append(dict(s))
        
    # Take top 15 if there are too many to save LLM tokens
    filtered_schemes = filtered_schemes[:15]

    # 5. Rank with LLM
    ranked_results = llm_client.rank_schemes(full_context, filtered_schemes)
    
    # Filter out low relevance (<40 score) and build matched_scheme_ids
    matched_ids = [r["scheme_id"] for r in ranked_results if r.get("score", 0) >= 40]
    
    # If LLM failed or filtered all, provide fallback matching
    if not matched_ids and filtered_schemes:
        matched_ids = [s["id"] for s in filtered_schemes[:3]]
        
    # Build final result payload
    final_matches = []
    for r in ranked_results:
        if r["scheme_id"] in matched_ids:
            final_matches.append(r)
            
    # 6. Save situation row
    situation_id = db.execute(
        """
        INSERT INTO situations 
            (user_id, description, extracted_context, matched_scheme_ids)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            situation_text,
            json.dumps(extracted_context),
            json.dumps(final_matches)
        )
    )
    
    return situation_id
