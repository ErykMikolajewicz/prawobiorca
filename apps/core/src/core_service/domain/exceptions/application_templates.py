class ApplicationTemplateNotFound(Exception):
    pass


class ApplicationTemplateContentNotFound(Exception):
    pass


class ApplicationTemplateInInvalidState(Exception):
    pass


class InvalidApplicationTemplate(Exception):
    pass


class InvalidApplicationFieldsConfig(Exception):
    pass


class InvalidApplicationFieldValues(Exception):
    def __init__(self, field_names: list[str]):
        self.field_names = field_names
