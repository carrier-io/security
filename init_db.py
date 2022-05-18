from tools import db


def init_db():
    from .models.tests import SecurityTestsDAST
    from .models.results import SecurityResultsDAST
    from .models.thresholds import SecurityThresholds

    from .models.details import SecurityDetails
    from .models.reports import SecurityReport
    db.Base.metadata.create_all(bind=db.engine)

