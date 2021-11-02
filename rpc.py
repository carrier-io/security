from .models.security_results import SecurityResultsDAST


def security_results_or_404(run_id: int) -> SecurityResultsDAST:
    return SecurityResultsDAST.query.get_or_404(run_id)
