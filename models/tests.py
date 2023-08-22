#     Copyright 2021 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from json import dumps
from queue import Empty
from typing import List, Union

from sqlalchemy import Column, Integer, String, ARRAY, JSON, and_

from tools import rpc_tools, db, db_tools, constants, VaultClient

from pylon.core.tools import log  # pylint: disable=E0611,E0401


class SecurityTestsDAST(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    __tablename__ = "security_tests_dast"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    project_name = Column(String(64), nullable=False)
    test_uid = Column(String(64), unique=True, nullable=False)

    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True, unique=False)

    urls_to_scan = Column(ARRAY(String(128)), nullable=False)
    urls_exclusions = Column(ARRAY(String(128)), nullable=True)
    scan_location = Column(String(128), nullable=False)
    test_parameters = Column(ARRAY(JSON), nullable=True)

    integrations = Column(JSON, nullable=True)

    schedules = Column(ARRAY(Integer), nullable=True, default=[])

    results_test_id = Column(Integer)
    build_id = Column(String(128), unique=True)

    def add_schedule(self, schedule_data: dict, commit_immediately: bool = True):
        schedule_data['test_id'] = self.id
        schedule_data['project_id'] = self.project_id
        try:
            schedule_id = self.rpc.timeout(2).scheduling_security_create_schedule(data=schedule_data)
            log.info(f'schedule_id {schedule_id}')
            updated_schedules = set(self.schedules)
            updated_schedules.add(schedule_id)
            self.schedules = list(updated_schedules)
            if commit_immediately:
                self.commit()
            log.info(f'self.schedules {self.schedules}')
        except Empty:
            log.warning('No scheduling rpc found')

    def handle_change_schedules(self, schedules_data: List[dict]):
        new_schedules_ids = set(i['id'] for i in schedules_data if i['id'])
        ids_to_delete = set(self.schedules).difference(new_schedules_ids)
        self.schedules = []
        for s in schedules_data:
            log.warning('!!!adding schedule')
            log.warning(s)
            self.add_schedule(s, commit_immediately=False)
        try:
            self.rpc.timeout(2).scheduling_delete_schedules(ids_to_delete)
        except Empty:
            ...
        self.commit()

    @property
    def scanners(self) -> list:
        try:
            return list(self.integrations.get('scanners', {}).keys())
        except AttributeError:
            return []

    @staticmethod
    def get_api_filter(project_id: int, test_id: Union[int, str]):
        log.info(f'getting filter int? {isinstance(test_id, int)}  {test_id}')
        if isinstance(test_id, int):
            return and_(
                SecurityTestsDAST.project_id == project_id,
                SecurityTestsDAST.id == test_id
            )
        return and_(
            SecurityTestsDAST.project_id == project_id,
            SecurityTestsDAST.test_uid == test_id
        )

    def configure_execution_json(
            self,
            output='cc',
            thresholds={}
    ):
        vault_client = VaultClient.from_project(self.project_id)
        if output == "dusty":
            from flask import current_app
            global_dast_settings = dict()
            global_dast_settings["max_concurrent_scanners"] = 1

            # if "toolreports" in self.reporting:
            #     global_dast_settings["save_intermediates_to"] = "/tmp/intermediates"

            # Thresholds
            tholds = {}
            if thresholds and any(int(thresholds[key]) > -1 for key in thresholds.keys()):

                for key, value in thresholds.items():
                    if int(value) > -1:
                        tholds[key.capitalize()] = int(value)

            #
            # Scanners
            #

            scanners_config = dict()
            for scanner_name in self.integrations.get('scanners', []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f'dusty_config_{scanner_name}',
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["scanners"][scanner_name],
                        )
                    scanners_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find scanner config rpc for {scanner_name}')

            # # scanners_data
            # for scanner_name in self.scanners_cards:
            #     scanners_config[scanner_name] = {}
            #     scanners_data = (
            #             current_app.config["CONTEXT"].rpc_manager.node.call(scanner_name)
            #             or
            #             {"target": "urls_to_scan"}
            #     )
            #     for setting in scanners_data:
            #         scanners_config[scanner_name][setting] = self.__dict__.get(
            #             scanners_data[setting],
            #             scanners_data[setting]
            #         )

            #
            # Processing
            #

            processing_config = dict()
            for processor_name in self.integrations.get("processing", []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f"dusty_config_{processor_name}",
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["processing"][processor_name],
                        )
                    processing_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find processor config rpc for {processor_name}')

            processing_config["quality_gate"] = {
                "thresholds": tholds
            }

            # "min_severity_filter": {
            #     "severity": "Info"
            # },
            # "quality_gate": {
            #     "thresholds": tholds
            # },
            # # "false_positive": {
            # #     "galloper": secrets_tools.unsecret(
            # #         "{{secret.galloper_url}}",
            # #         project_id=self.project_id
            # #     ),
            # #     "project_id": f"{self.project_id}",
            # #     "token": secrets_tools.unsecret(
            # #         "{{secret.auth_token}}",
            # #         project_id=self.project_id
            # #     )
            # # },
            # # "ignore_finding": {
            # #     "galloper": secrets_tools.unsecret(
            # #         "{{secret.galloper_url}}",
            # #         project_id=self.project_id
            # #     ),
            # #     "project_id": f"{self.project_id}",
            # #     "token": secrets_tools.unsecret(
            # #         "{{secret.auth_token}}",
            # #         project_id=self.project_id
            # #     )
            # # }

            #
            # Reporters
            #

            reporters_config = dict()
            for reporter_name in self.integrations.get('reporters', []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f'dusty_config_{reporter_name}',
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["reporters"][reporter_name],
                        )
                    reporters_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find reporter config rpc for {reporter_name}')

            reporters_config["centry_loki"] = {
                "url": vault_client.unsecret("{{secret.loki_host}}"),
                "labels": {
                    "project": str(self.project_id),
                    "build_id": str(self.build_id),
                    "report_id": str(self.results_test_id),
                    "hostname": "dusty"
                },
            }
            reporters_config["centry_status"] = {
                "url": vault_client.unsecret("{{secret.galloper_url}}"),
                "token": vault_client.unsecret("{{secret.auth_token}}"),
                "project_id": str(self.project_id),
                "test_id": str(self.results_test_id),
            }


            reporters_config["centry"] = {
                "url": vault_client.unsecret("{{secret.galloper_url}}"),
                "token": vault_client.unsecret("{{secret.auth_token}}"),
                "project_id": str(self.project_id),
                "test_id": str(self.results_test_id),
            }
            # TODO: check valid reports names
            # for report_type in self.reporting:
            #     if report_type == "toolreports":
            #         reporters_config["galloper_tool_reports"] = {
            #             "bucket": "dast",
            #             "object": f"{self.test_uid}_tool_reports.zip",
            #             "source": "/tmp/intermediates",
            #         }
            #
            #     elif report_type == "quaity":
            #         reporters_config["galloper_junit_report"] = {
            #             "bucket": "dast",
            #             "object": f"{self.test_uid}_junit_report.xml",
            #         }
            #         reporters_config["galloper_quality_gate_report"] = {
            #             "bucket": "dast",
            #             "object": f"{self.test_uid}_quality_gate_report.json",
            #         }
            #         reporters_config["junit"] = {
            #             "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.xml",
            #         }
            #
            #     elif report_type == "jira":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "jira" in project_secrets:
            #             jira_settings = loads(project_secrets["jira"])
            #             reporters_config["jira"] = {
            #                 "url": jira_settings["jira_url"],
            #                 "username": jira_settings["jira_login"],
            #                 "password": jira_settings["jira_password"],
            #                 "project": jira_settings["jira_project"],
            #                 "fields": {
            #                     "Issue Type": jira_settings["issue_type"],
            #                 }
            #             }
            #
            #     elif report_type == "email":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "smtp" in project_secrets:
            #             email_settings = loads(project_secrets["smtp"])
            #             reporters_config["email"] = {
            #                 "server": email_settings["smtp_host"],
            #                 "port": email_settings["smtp_port"],
            #                 "login": email_settings["smtp_user"],
            #                 "password": email_settings["smtp_password"],
            #                 "mail_to": self.dast_settings.get("email_recipients", ""),
            #             }
            #             reporters_config["html"] = {
            #                 "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.html",
            #             }
            #
            #     elif report_type == "ado":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "ado" in project_secrets:
            #             reporters_config["azure_devops"] = loads(
            #                 project_secrets["ado"]
            #             )
            #
            #     elif report_type == "rp":
            #         project_secrets = get_project_hidden_secrets(self.project_id)
            #         if "rp" in project_secrets:
            #             rp = loads(project_secrets.get("rp"))
            #             reporters_config["reportportal"] = {
            #                 "rp_host": rp["rp_host"],
            #                 "rp_token": rp["rp_token"],
            #                 "rp_project_name": rp["rp_project"],
            #                 "rp_launch_name": "dast"
            #             }

            dusty_config = {
                "config_version": 2,
                "suites": {
                    "dast": {
                        "settings": {
                            "project_name": self.project_name,
                            "project_description": self.name,
                            "environment_name": "target",
                            "testing_type": "DAST",
                            "scan_type": "full",
                            "build_id": self.test_uid,
                            "dast": global_dast_settings
                        },
                        # "actions": {
                        #     "git_clone": {
                        #         "source": "https://github.com/carrier-io/galloper.git",
                        #         "target": "/tmp/code",
                        #         "branch": "master",
                        #     }
                        # },
                        "scanners": {
                            "dast": scanners_config,
                            # "dast": {"nmap": {
                            #     "target": "http://scanme.nmap.org/",
                            #     "include_ports": "22,80,443"
                            # }},
                            # "sast": {
                            #     "python": {
                            #         "code": "/tmp/code",
                            #     },
                            # },
                        },
                        "processing": processing_config,
                        "reporters": reporters_config
                    }
                }
            }
            #
            log.info("Resulting config: %s", dusty_config)
            #
            return dusty_config

        job_type = "dast"
        # job_type = "sast"

        # container = f"getcarrier/{job_type}:{CURRENT_RELEASE}"
        # container = f"getcarrier/sast:latest"
        container = f"getcarrier/dast:latest"
        parameters = {
            "cmd": f"run -b centry:{job_type}_{self.test_uid} -s {job_type}",
            "GALLOPER_URL": vault_client.unsecret("{{secret.galloper_url}}"),
            "GALLOPER_PROJECT_ID": f"{self.project_id}",
            "GALLOPER_AUTH_TOKEN": vault_client.unsecret("{{secret.auth_token}}"),
        }
        cc_env_vars = {
            "RABBIT_HOST": vault_client.unsecret("{{secret.rabbit_host}}"),
            "RABBIT_USER": vault_client.unsecret("{{secret.rabbit_user}}"),
            "RABBIT_PASSWORD": vault_client.unsecret("{{secret.rabbit_password}}"),
            "REPORT_ID": str(self.results_test_id),
            "build_id": str(self.build_id),
            "project_id": str(self.project_id),
        }
        concurrency = 1

        if output == "docker":
            return f"docker run --rm -i -t " \
                   f"-e project_id={self.project_id} " \
                   f"-e galloper_url={vault_client.unsecret('{{secret.galloper_url}}')} " \
                   f"-e token=\"{vault_client.unsecret('{{secret.auth_token}}')}\" " \
                   f"getcarrier/control_tower:{constants.CURRENT_RELEASE} " \
                   f"-tid {self.test_uid}"
        if output == "cc":
            channel = self.scan_location
            if channel == "Carrier default config":
                channel = "default"
            #
            execution_json = {
                "job_name": self.name,
                "job_type": job_type,
                "concurrency": concurrency,
                "container": container,
                "execution_params": dumps(parameters),
                "cc_env_vars": cc_env_vars,
                # "channel": self.region
                "channel": channel,
            }
            # todo: scanner_cards no longer present
            # if "quality" in self.scanners_cards:
            #     execution_json["quality_gate"] = "True"
            #
            log.info("Resulting CC config: %s", execution_json)
            #
            return execution_json

        return ""

    # def to_json(self, exclude_fields: tuple = ()) -> dict:
    #     test_param = super().to_json(exclude_fields)
    #     # test_param["tools"] = ",".join(test_param["scanners_cards"].keys())
    #     if test_param['created']:
    #         test_param['created'] = format_date(test_param['created'])
    #     if test_param['updated']:
    #         test_param['updated'] = format_date(test_param['updated'])
    #     # print('test_param', test_param)
    #
    #     return test_param
