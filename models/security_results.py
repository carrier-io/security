import string
from datetime import datetime as dt, timedelta

from sqlalchemy import String, Column, Integer, JSON, DateTime, ARRAY

from ...shared.db_manager import Base
from ...shared.models.abstract_base import AbstractBaseMixin
from ...shared.utils.rpc import RpcMixin
from ...shared.connectors.minio import MinioClient


class SecurityResultsDAST(AbstractBaseMixin, Base, RpcMixin):
    __tablename__ = "security_results_dast"

    # TODO: excluded = ignored
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_id = Column(Integer, unique=False)
    test_uid = Column(String(128), unique=False)
    test_name = Column(String(128), unique=False)
    start_date = Column(DateTime, default=dt.utcnow)
    duration = Column(String(128), unique=False)
    #
    scan_time = Column(String(128), unique=False)
    scan_duration = Column(String(128), unique=False)
    project_name = Column(String(128), unique=False)
    app_name = Column(String(128), unique=False)
    dast_target = Column(String(128), unique=False)
    sast_code = Column(String(128), unique=False)
    scan_type = Column(String(4), unique=False)
    findings = Column(Integer, unique=False)
    false_positives = Column(Integer, unique=False)
    excluded = Column(Integer, unique=False)
    info_findings = Column(Integer, unique=False)
    environment = Column(String(32), unique=False)
    #
    # findings counts
    # findings = Column(Integer, unique=False, default=0)
    valid = Column(Integer, unique=False, default=0)
    false_positive = Column(Integer, unique=False, default=0)
    ignored = Column(Integer, unique=False, default=0)
    critical = Column(Integer, unique=False, default=0)
    high = Column(Integer, unique=False, default=0)
    medium = Column(Integer, unique=False, default=0)
    low = Column(Integer, unique=False, default=0)
    info = Column(Integer, unique=False, default=0)
    # other
    # excluded = Column(Integer, unique=False)
    tags = Column(ARRAY(String), default=[])
    test_status = Column(
        JSON,
        default={
            "status": "Pending...",
            "percentage": 0,
            "description": "Process details description"
        }
    )
    test_config = Column(JSON, nullable=False, unique=False)

    # TODO: write this method
    def set_test_status(self, ts):
        self.test_status = ts
        self.commit()

    @staticmethod
    def sanitize(val):
        valid_chars = "_%s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in val if c in valid_chars)

    @property
    def bucket_name(self):
        return f'run--{self.id}'

    def get_minio_client(self) -> MinioClient:
        return MinioClient(self.rpc.call.project_get_or_404(self.project_id))

    def insert(self):
        super().insert()
        # minio part
        minio_client = self.get_minio_client()
        minio_client.create_bucket(bucket=self.bucket_name)
        # if created:
        #     minio_client.configure_bucket_lifecycle(self.bucket_name, 7)



    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json(exclude_fields)

        test_param["name"] = test_param.pop("test_name")
        if test_param["duration"]:
            test_param["ended_date"] = str(test_param["start_date"] + timedelta(seconds=float(test_param["duration"])))
        test_param["start_date"] = str(test_param["start_date"])
        return test_param
