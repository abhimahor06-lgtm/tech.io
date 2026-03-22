"""user_routes.py
User profile endpoints (public + authenticated)
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db_connect import db

user_bp = Blueprint('user', __name__)


@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Return basic user profile info."""
    try:
        claims = get_jwt()
        requester_id = int(get_jwt_identity())
        role = claims.get('role')

        # Admin can view any user, users can view themselves
        if role != 'admin' and requester_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        user = db.fetch_one('SELECT id, username, email, role, status FROM users WHERE id=%s', (user_id,))
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Return consistent API format
        response_data = {'user': user}
        return jsonify({'success': True, 'data': response_data, **response_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error fetching user data', 'error': str(e)}), 500
