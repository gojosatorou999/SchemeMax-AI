import json
import traceback
import datetime
from openai import OpenAI
from flask import current_app


class _DTEncoder(json.JSONEncoder):
    """JSON encoder that converts datetime objects to ISO strings."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)


def _dumps(obj):
    return json.dumps(obj, cls=_DTEncoder)

class LLMClient:
    def __init__(self):
        # The client will be instantiated when used to allow app context config access
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
        return self._client

    @property
    def model(self):
        return current_app.config["OPENAI_MODEL"]

    def extract_context(self, user_text: str) -> dict:
        """
        Extracts medical and financial context from the user's situation description.
        Returns a dict: {age_hint, state_hint, condition_categories, financial_hint, family_situation}
        """
        try:
            prompt = f"""
            Extract the following information from the user's situation description:
            - age_hint (integer or null if not mentioned)
            - state_hint (string name of the Indian state, or null)
            - condition_categories (list of strings like "cancer", "cardiac", "accident", "general", "pediatric", "maternal")
            - financial_hint (string summarizing their financial situation/income if mentioned, or null)
            - family_situation (string summarizing relevant family details, or null)

            User Description: "{user_text}"
            
            Return ONLY a JSON object.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            current_app.logger.error(f"Error in extract_context: {traceback.format_exc()}")
            return {
                "age_hint": None,
                "state_hint": None,
                "condition_categories": ["general"],
                "financial_hint": None,
                "family_situation": None
            }

    def rank_schemes(self, user_context: dict, candidate_schemes: list) -> list:
        """
        Ranks candidate schemes based on the user's context.
        Returns a list of dicts: {scheme_id, score (0-100), reasoning} sorted by score.
        """
        if not candidate_schemes:
            return []
            
        schemes_json = json.dumps([{
            "id": s["id"], 
            "name": s["name"], 
            "description": s["full_description"],
            "eligibility": s["eligibility_json"]
        } for s in candidate_schemes])

        try:
            prompt = f"""
            You are an expert matching Indian government schemes to a user's situation.
            
            User Profile and Situation: {_dumps(user_context)}
            
            Candidate Schemes: {schemes_json}
            
            For each candidate scheme, provide a relevance score from 0 to 100 based on how well it matches the user's medical and financial situation. Also provide a 1-2 sentence reassuring reasoning explaining why they might be eligible.
            
            Return ONLY a JSON object with a key "ranked_schemes" containing a list of objects, each with "scheme_id" (integer), "score" (integer), and "reasoning" (string).
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            result = json.loads(response.choices[0].message.content)
            ranked = result.get("ranked_schemes", [])
            # Sort by score descending
            ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
            return ranked
        except Exception as e:
            current_app.logger.error(f"Error in rank_schemes: {traceback.format_exc()}")
            # Fallback: return all schemes with a dummy score
            return [{"scheme_id": s["id"], "score": 50, "reasoning": "May be applicable based on general matching rules."} for s in candidate_schemes]

    def generate_checklist(self, scheme: dict, user_context: dict) -> list:
        """
        Generates a personalized document checklist based on scheme requirements and user context.
        Returns a list of strings.
        """
        try:
            prompt = f"""
            You are helping a user apply for the scheme: {scheme['name']}.
            Standard required documents for this scheme: {scheme['required_documents']}
            
            User Profile and Situation: {_dumps(user_context)}
            
            Generate a personalized, clear checklist of documents the user should gather to apply for this scheme. Tailor it to their situation if possible (e.g., if they had an accident, mention accident report). Use plain English.
            
            Return ONLY a JSON object with a key "checklist" containing a list of strings.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("checklist", json.loads(scheme.get("required_documents", "[]")))
        except Exception as e:
            current_app.logger.error(f"Error in generate_checklist: {traceback.format_exc()}")
            return json.loads(scheme.get("required_documents", "[]"))

llm_client = LLMClient()
