"""
统一数据结构 — 连接 parser（解析）和 builder（构建）的纽带
从 doc-generator 迁入
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class FlowRow:
    """处理流程的一行"""
    action: str
    response: str


@dataclass
class LeafData:
    """叶子节点的业务数据"""
    desc: str = ""
    flow: List[FlowRow] = field(default_factory=list)


@dataclass
class Leaf:
    """叶子节点"""
    name: str
    heading_level: int = 5
    data: Optional[LeafData] = None
    source_path: Tuple = ()


@dataclass
class Group:
    """子功能组"""
    name: str
    heading_level: int = 4
    children: List[Leaf] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0


@dataclass
class Section:
    """大模块"""
    name: str
    groups: List[Group] = field(default_factory=list)
    direct_leaves: List[Leaf] = field(default_factory=list)


@dataclass
class Platform:
    """平台/终端"""
    name: str
    sections: List[Section] = field(default_factory=list)


@dataclass
class DocumentTree:
    """完整的文档树"""
    platforms: List[Platform] = field(default_factory=list)

    @property
    def total_leaves(self) -> int:
        count = 0
        for plat in self.platforms:
            for sec in plat.sections:
                count += len(sec.direct_leaves)
                for grp in sec.groups:
                    if grp.is_leaf:
                        count += 1
                    else:
                        count += len(grp.children)
        return count

    def leaf_paths(self) -> List[Tuple]:
        paths = []
        for plat in self.platforms:
            for sec in plat.sections:
                for leaf in sec.direct_leaves:
                    paths.append((plat.name, sec.name, None, leaf.name, leaf.heading_level))
                for grp in sec.groups:
                    if grp.is_leaf:
                        paths.append((plat.name, sec.name, grp.name, grp.name, grp.heading_level))
                    else:
                        for leaf in grp.children:
                            paths.append((plat.name, sec.name, grp.name, leaf.name, leaf.heading_level))
        return paths