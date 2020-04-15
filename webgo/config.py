import os

DB_FILE = 'sqlite.db'

project = None


class ProjectParse:
    def __init__(self, project_path):
        self._project_path = project_path

    @property
    def path(self):
        return self._project_path

    @property
    def name(self):
        return os.path.basename(self._project_path)

    @property
    def pkg_name(self):
        return self.name + '__main__'
