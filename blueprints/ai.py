from flask import Blueprint, jsonify, request

from utils import get_hf_query_suggestion, login_required

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai-suggest', methods=['POST'])
@login_required
def ai_suggest():
    query = request.json.get('query', '')
    if not query:
        return jsonify({"error": "Query is required"}), 400
    suggestion = get_hf_query_suggestion(query)
    return jsonify({"suggestion": suggestion})
