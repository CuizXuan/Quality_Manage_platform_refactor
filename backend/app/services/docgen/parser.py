"""
需求文档解析器 — 将 .docx 解析为统一数据结构 DocumentTree
从 doc-generator 迁入
"""

from docx import Document
from typing import Optional, List, Dict

from .datamodel import DocumentTree, Platform, Section, Group, Leaf, LeafData, FlowRow

STYLE_MAP = {
    '3': 'Heading1',
    '4': 'Heading2',
    '5': 'Heading3',
    '6': 'Heading4',
    '7': 'Heading5',
    '64': 'ListParagraph',
}


class DocParser:
    """需求文档解析器"""

    NS_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self._doc: Optional[Document] = None

    def parse(self) -> DocumentTree:
        """解析文档，返回 DocumentTree"""
        self._doc = Document(self.docx_path)
        body_xml = self._doc.element.body
        tables = list(self._doc.tables)
        tree = self._build_tree(body_xml)
        self._match_tables(body_xml, tables, tree)
        return tree

    def _get_pstyle(self, p_element) -> Optional[str]:
        pPr = p_element.find(f'{{{self.NS_W}}}pPr')
        if pPr is not None:
            ps = pPr.find(f'{{{self.NS_W}}}pStyle')
            if ps is not None:
                return ps.get(f'{{{self.NS_W}}}val')
        return None

    def _get_text(self, p_element) -> str:
        texts = p_element.findall(f'.//{{{self.NS_W}}}t')
        return ''.join([t.text or '' for t in texts]).strip()

    def _detect_platform_name(self, text: str) -> str:
        t = text.lower()
        if 'pc端' in t:
            return 'PC端'
        elif '管理端' in t:
            return '管理端APP'
        elif '农户端' in t:
            return '农户端APP'
        return text

    def _build_tree(self, body_xml) -> DocumentTree:
        tree = DocumentTree()
        current_platform: Platform | None = None
        current_section: Section | None = None
        current_group: Group | None = None

        for child in body_xml:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag != 'p':
                continue

            style_val = self._get_pstyle(child)
            text = self._get_text(child)
            if not text:
                continue

            if style_val == '3':
                continue
            elif style_val == '4':
                current_platform = Platform(name=self._detect_platform_name(text))
                tree.platforms.append(current_platform)
                current_section = None
                current_group = None
            elif style_val == '5':
                current_section = Section(name=text)
                if current_platform is not None:
                    current_platform.sections.append(current_section)
                current_group = None
            elif style_val in ('6', '7'):
                h_level = 4 if style_val == '6' else 5
                current_group = Group(name=text, heading_level=h_level)
                if current_section is not None:
                    current_section.groups.append(current_group)
            elif style_val == '64':
                leaf = Leaf(
                    name=text,
                    heading_level=5,
                    source_path=self._current_path(current_platform, current_section, current_group, text)
                )
                if current_group is not None:
                    current_group.children.append(leaf)
                elif current_section is not None:
                    current_section.direct_leaves.append(leaf)

        return tree

    def _current_path(self, plat, sec, grp, name):
        pn = plat.name if plat else ''
        sn = sec.name if sec else ''
        gn = grp.name if grp else None
        return (pn, sn, gn, name)

    def _match_tables(self, body_xml, tables, tree: DocumentTree):
        leaf_index = {}
        for plat in tree.platforms:
            for sec in plat.sections:
                for leaf in sec.direct_leaves:
                    leaf_index[leaf.source_path] = leaf
                for grp in sec.groups:
                    if grp.is_leaf:
                        group_leaf = Leaf(
                            name=grp.name,
                            heading_level=grp.heading_level,
                            source_path=(plat.name, sec.name, grp.name, None)
                        )
                        grp._leaf_ref = group_leaf
                        leaf_index[group_leaf.source_path] = group_leaf
                    else:
                        for child in grp.children:
                            leaf_index[child.source_path] = child

        current_plat = None
        current_sec = None
        current_grp = None
        last_lp_name = None
        ti = 0

        for child in body_xml:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'p':
                style_val = self._get_pstyle(child)
                text = self._get_text(child)
                if not text:
                    continue

                if style_val == '4':
                    current_plat = self._detect_platform_name(text)
                    current_sec = None; current_grp = None; last_lp_name = None
                elif style_val == '5':
                    current_sec = text; current_grp = None; last_lp_name = None
                elif style_val in ('6', '7'):
                    current_grp = text; last_lp_name = None
                elif style_val == '64':
                    last_lp_name = text

            elif tag == 'tbl':
                if current_plat is None:
                    ti += 1
                    continue

                table = tables[ti] if ti < len(tables) else None
                ti += 1
                if table is None or len(table.rows) < 2:
                    continue

                case_name = table.rows[0].cells[1].text.strip() if len(table.rows[0].cells) > 1 else ''
                if not case_name:
                    continue
                case_desc = table.rows[1].cells[1].text.strip() if len(table.rows) > 1 and len(table.rows[1].cells) > 1 else ''

                basic_flow = []
                for row in table.rows:
                    cells = row.cells
                    if len(cells) >= 3:
                        c0 = cells[0].text.strip()
                        c1 = cells[1].text.strip()
                        c2 = cells[2].text.strip()
                        if c0 == '基本流程' and c1 and c2 and c1 not in ('参与者行为', '系统响应'):
                            basic_flow.append(FlowRow(action=c1, response=c2))

                leaf_data = LeafData(desc=case_desc, flow=basic_flow)
                target_leaf = None

                if current_grp is not None and last_lp_name is not None:
                    path = (current_plat, current_sec, current_grp, last_lp_name)
                    target_leaf = leaf_index.get(path)
                elif current_grp is not None:
                    path1 = (current_plat, current_sec, current_grp, current_grp)
                    path2 = (current_plat, current_sec, current_grp, None)
                    target_leaf = leaf_index.get(path1) or leaf_index.get(path2)
                    if target_leaf is None:
                        for path, leaf in leaf_index.items():
                            if leaf.name == current_grp and path[0] == current_plat and path[1] == current_sec:
                                target_leaf = leaf
                                break
                elif last_lp_name is not None:
                    path = (current_plat, current_sec, None, last_lp_name)
                    target_leaf = leaf_index.get(path)
                else:
                    path = (current_plat, current_sec, None, current_sec)
                    target_leaf = leaf_index.get(path)

                if target_leaf is None:
                    for path, leaf in leaf_index.items():
                        if leaf.name == case_name and path[0] == current_plat and path[1] == current_sec:
                            target_leaf = leaf
                            break

                if target_leaf is not None:
                    if target_leaf.data is None:
                        target_leaf.data = leaf_data
                    else:
                        if not target_leaf.data.desc:
                            target_leaf.data.desc = leaf_data.desc
                        target_leaf.data.flow.extend(leaf_data.flow)