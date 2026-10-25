
import pytest

from benchmarks.workflow_case.workflow import resolve_workflow


def test_linear_workflow():
    graph = {
        "a_ship": ["b_build"],
        "b_build": ["c_fetch"],
        "c_fetch": [],
    }

    assert resolve_workflow(graph) == [
        "c_fetch",
        "b_build",
        "a_ship",
    ]


def test_independent_tasks():
    graph = {
        "beta": [],
        "alpha": [],
    }

    assert resolve_workflow(graph) == [
        "alpha",
        "beta",
    ]


def test_cycle_rejected():
    graph = {
        "a": ["b"],
        "b": ["a"],
    }

    with pytest.raises(ValueError, match="cycle"):
        resolve_workflow(graph)


def test_unknown_dependency_rejected():
    graph = {
        "a": ["missing"],
    }

    with pytest.raises(ValueError, match="Unknown task"):
        resolve_workflow(graph)
