from mopidy_packages import models


def test_person_data_is_valid():
    list(models.Person.all())


def test_project_data_is_valid():
    list(models.Project.all())
