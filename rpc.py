from .models.security_results import SecurityResultsDAST


def security_results_or_404(run_id):
    return SecurityResultsDAST.query.get_or_404(run_id)
