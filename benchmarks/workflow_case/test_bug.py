
from benchmarks.workflow_case.workflow import resolve_workflow


def test_diamond_workflow():
    graph = {
        "a_ship": ["b_test", "c_package"],
        "b_test": ["d_build"],
        "c_package": ["d_build"],
        "d_build": [],
    }

    assert resolve_workflow(graph) == [
        "d_build",
        "b_test",
        "c_package",
        "a_ship",
    ]


def test_shared_dependency_three_branches():
    graph = {
        "a_publish": ["b_docs", "c_site", "d_email"],
        "b_docs": ["e_compile"],
        "c_site": ["e_compile"],
        "d_email": ["e_compile"],
        "e_compile": [],
    }

    assert resolve_workflow(graph) == [
        "e_compile",
        "b_docs",
        "c_site",
        "d_email",
        "a_publish",
    ]
