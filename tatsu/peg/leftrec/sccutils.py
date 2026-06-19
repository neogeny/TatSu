# Adapted from pegen (sccutils.py) under the MIT license.
# pegen is Copyright (c) 2019, Guido van Rossum and contributors.

# noqa # type: ignore # ruff: noqa
# ty: ignore-file
# pyrefly: ignore
# pyright: ignore
# pyright: reportGeneralTypeIssues=false

from typing import AbstractSet, Dict, Iterable, Iterator, List, Set


def strongly_connected_components(
    vertices: AbstractSet[str], edges: Dict[str, AbstractSet[str]]
) -> Iterator[AbstractSet[str]]:
    identified: Set[str] = set()
    stack: List[str] = []
    index: Dict[str, int] = {}
    boundaries: List[int] = []

    def dfs(v: str) -> Iterator[Set[str]]:
        index[v] = len(stack)
        stack.append(v)
        boundaries.append(index[v])

        for w in edges[v]:
            if w not in index:
                yield from dfs(w)
            elif w not in identified:
                while index[w] < boundaries[-1]:
                    boundaries.pop()

        if boundaries[-1] == index[v]:
            boundaries.pop()
            scc = set(stack[index[v] :])
            del stack[index[v] :]
            identified.update(scc)
            yield scc

    for v in vertices:
        if v not in index:
            yield from dfs(v)


def find_cycles_in_scc(
    graph: Dict[str, AbstractSet[str]], scc: AbstractSet[str], start: str
) -> Iterable[List[str]]:
    assert start in scc, (start, scc)
    assert scc <= graph.keys(), scc - graph.keys()

    graph = {
        src: {dst for dst in dsts if dst in scc}
        for src, dsts in graph.items()
        if src in scc
    }
    assert start in graph

    def dfs(node: str, path: List[str]) -> Iterator[List[str]]:
        if node in path:
            yield path + [node]
            return
        path = path + [node]
        for child in graph[node]:
            yield from dfs(child, path)

    yield from dfs(start, [])
