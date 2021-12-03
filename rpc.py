from functools import reduce

from sqlalchemy.sql import func, LABEL_STYLE_TABLENAME_PLUS_COL

from .models.security_reports import SecurityReport
from .models.security_results import SecurityResultsDAST


def security_results_or_404(run_id: int) -> SecurityResultsDAST:
    return SecurityResultsDAST.query.get_or_404(run_id)


def overview_data(project_id: int):
    queries = [
        func.sum(getattr(SecurityResultsDAST, i)).label(f'sum_{i}')
        for i in SecurityReport.SEVERITY_CHOICES.keys()
    ]
    q = SecurityResultsDAST.query.with_entities(
        *queries
    ).filter(
        SecurityResultsDAST.project_id == project_id,
    )
    return dict(zip([i['name'] for i in q.column_descriptions], q.first()))
