from app.errors import bp


@bp.app_errorhandler(413)
def too_large(error):
    return "File is too large", 413